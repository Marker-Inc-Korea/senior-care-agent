# agent.py

# 독거노인 Ben씨의 안부 확인을 위한 음성 기반 자동화 에이전트입니다.
# LiveKit에 Voice pipeline(OpenAI, Deepgram, Cartesia)을 연결해
# 신원 확인, 건강 체크, 사람 상담원 연결까지 처리합니다.

import logging
from dataclasses import dataclass, field
from typing import Optional
import os
import json
import uuid
from dotenv import load_dotenv
import asyncio

# LiveKit 및 관련 플러그인
from livekit import api
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.llm import function_tool

from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.turn_detector.english import EnglishModel

# 유틸리티 함수들 (프롬프트 로딩, 기록 저장 등)
from utils import load_prompt, load_previous_history, save_history, append_request_log

logger = logging.getLogger("senior-care-agent")
logger.setLevel(logging.INFO)

# 환경변수 로드 (.env 파일)
load_dotenv()


# 사용자별 상태 관리 데이터 구조
@dataclass
class UserData:
    personas: dict[str, Agent] = field(default_factory=dict)  # 여러 에이전트 인스턴스
    prev_agent: Optional[Agent] = None  # 이전 에이전트 (context 공유 목적)
    ctx: Optional[JobContext] = None  # LiveKit job context

    def summarize(self) -> str:
        return "User data: Senior welfare check system"


# 타입 alias
RunContext_T = RunContext[UserData]


# 통화 종료 헬퍼 함수
async def hangup_call():
    ctx = get_job_context()
    if ctx is None:
        # Not running in a job context
        return
    await asyncio.sleep(4)

    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(
            room=ctx.room.name,
        )
    )


# 공통 에이전트 베이스 클래스
class BaseAgent(Agent):
    async def on_enter(self) -> None:
        # 에이전트 입장 시 초기화 처리
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")

        userdata: UserData = self.session.userdata

        # 현재 room participant의 속성 업데이트 (어떤 agent인지 명시)
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes(
                {"agent": agent_name}
            )

        # 이전 에이전트의 대화 기록 일부 가져와서 이어쓰기
        chat_ctx = self.chat_ctx.copy()

        if userdata.prev_agent:
            items_copy = self._truncate_chat_ctx(
                userdata.prev_agent.chat_ctx.items, keep_function_call=True
            )
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in items_copy if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)

        # 시스템 메시지로 에이전트 역할 명시
        chat_ctx.add_message(
            role="system", content=f"You are the {agent_name}. {userdata.summarize()}"
        )
        await self.update_chat_ctx(chat_ctx)

        # 응답 생성 시작
        self.session.generate_reply()

    # 대화 context를 길이에 맞게 줄이는 유틸리티 함수
    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 6,
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        """Truncate the chat context to keep the last n messages."""

        def _valid_item(item) -> bool:
            if (
                not keep_system_message
                and item.type == "message"
                and item.role == "system"
            ):
                return False
            if not keep_function_call and item.type in [
                "function_call",
                "function_call_output",
            ]:
                return False
            return True

        new_items = []
        for item in reversed(items):
            if _valid_item(item):
                new_items.append(item)
            if len(new_items) >= keep_last_n_messages:
                break
        new_items = new_items[::-1]

        # 앞부분이 함수 호출일 경우 제거
        while new_items and new_items[0].type in [
            "function_call",
            "function_call_output",
        ]:
            new_items.pop(0)

        return new_items

    # 다른 에이전트로 context 넘기며 전환
    async def _transfer_to_agent(self, name: str, context: RunContext_T) -> Agent:
        """Transfer to another agent while preserving context"""
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.personas[name]
        userdata.prev_agent = current_agent

        return next_agent


# 신원 확인 에이전트
class IntakeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            instructions=load_prompt("intake_prompt.yaml"),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(),
            turn_detection=EnglishModel(),
        )

    # 사용자 이름을 받아 신원 검증
    @function_tool
    async def verify_identity(self, context: RunContext_T, name: str) -> Agent:
        # NOTE: 현재는 데모 목적으로 단순한 하드코딩된 이름 비교 방식으로 신원 확인을 구현했습니다.
        # (예: 사용자가 'Ben'이라고 말하면 통과)
        # 실제 서비스 환경에서는 사용자 인증 토큰, 데이터베이스 기반 사용자 정보,
        # 등 보다 안전한 신원 확인 절차로 대체되어야 합니다.
        # 또한, 음성 기반 입력은 인식 오류(예: 이름 발음 차이, 억양, 잡음 등)가 발생할 수 있으므로,
        # STT 정확도를 고려한 보완 로직(예: fuzzy matching, 반복 확인 등)도 함께 설계되어야 합니다.
        if name in ["Ben", "Ben Kim", "ben"]:  # placeholder
            await self.session.say("Confirmed. We'd like to ask you about your health.")
            return await self._transfer_to_agent("check-in", context)
        await self.session.say(
            "End the call because you failed to verify your identity."
        )

        await hangup_call()


# 건강 상태 확인 및 상담 요청 처리
class CheckInAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            instructions=load_prompt("check_in_prompt.yaml"),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(),
            turn_detection=EnglishModel(),
        )

    # 사용자의 요청(불편사항 등)을 기록
    @function_tool
    async def register_request(self, context: RunContext_T, detail: str) -> str:
        """Use it to log a customer's complaint or request, which will be forwarded to a human agent for further action."""
        append_request_log(detail)
        return f"We've received your request for ‘{detail}’ and will forward it to the appropriate person."

    # 긴급 시 사람 상담원에게 전화 연결
    @function_tool()
    async def transfer_call_to_human(self, ctx: RunContext):
        """Transfer the call to a human agent, called after confirming with the user. Please call this when emergency happens."""

        # 실제 연결할 상담원의 전화번호는 환경 변수에서 불러오도록 처리
        phone_number = os.environ.get(
            "HUMAN_AGENT_PHONE", "+821000000000"
        )  # 기본값은 마스킹 처리된 번호
        job_ctx = get_job_context()
        if job_ctx is None:
            await ctx.session.say("I can't transfer the call right now.")
            return

        try:
            print(f"Transferring call to {phone_number}")

            await ctx.session.say("Transferring you to a human agent now. Please hold.")

            # SIP call 생성
            await job_ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=os.environ["SIP_OUTBOUND_TRUNK_ID"],
                    sip_call_to=phone_number,
                    room_name=job_ctx.room.name,
                    participant_identity=f"transfer_{uuid.uuid4().hex[:8]}",
                    participant_name="Human Agent",
                    krisp_enabled=True,
                )
            )
            ctx.session.output.set_audio_enabled(False)
            return (
                None,
                f"I've transferred you to a human agent at {phone_number}. Please hold while we connect you.",
            )

        except Exception as e:
            print(f"error transferring call: {e}")
            await ctx.session.say("Sorry, something went wrong transferring the call.")

    # 사용자가 자연어로 통화 종료를 말할 경우 이를 감지해 종료 흐름을 처리
    @function_tool
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        # let the agent finish speaking
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()
        try:
            # 마지막 대화 메시지 요약 및 저장
            last_messages = [
                {"role": item.role, "content": item.content}
                for item in self.chat_ctx.items
                if item.type == "message"
                and item.role in ("user", "assistant")
                and item.content
            ]
            history = {
                "last_messages": last_messages[-10:],
                "note": "Messages of last conversations",
            }
            save_history(ctx, history)
        except Exception as e:
            print(f"Error saving history: {e}")

        await ctx.session.say("End the call. Have a good day.")
        await hangup_call()

    async def on_enter(self):
        # 입장 시 과거 기록 일부 포함
        previous_history = load_previous_history()
        chat_ctx = self.chat_ctx.copy()
        chat_ctx.add_message(
            role="system",
            content=f"Partial history of recent conversations:\n{previous_history if isinstance(previous_history, str) else json.dumps(previous_history, ensure_ascii=False)}",
        )
        await self.update_chat_ctx(chat_ctx)
        await self.session.generate_reply()


# 메인 entrypoint - LiveKit 에이전트 실행 진입점
async def entrypoint(ctx: JobContext):
    await ctx.connect()
    userdata = UserData(ctx=ctx)

    # 두 에이전트 생성 후 등록
    agents = {
        "intake": IntakeAgent(),
        "check-in": CheckInAgent(),
    }

    userdata.personas.update(agents)

    # 에이전트 세션 생성 및 시작
    session = AgentSession[UserData](userdata=userdata)
    await session.start(
        agent=agents["intake"],  # 초기 진입 에이전트
        room=ctx.room,
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(entrypoint_fnc=entrypoint, agent_name="senior-care-agent")
    )
