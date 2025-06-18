# 전화 발신용 스크립트
# LiveKit SIP 기능을 이용해 senior-care-agent가 특정 전화번호로 전화를 겁니다.
# 에이전트 실행 코드는 따로 agent.py에서 구동되고,
# 본 파일은 CLI에서 전화번호를 인자로 받아 해당 room을 만들고 SIP 발신을 수행합니다.

# make_call.py

import asyncio
import json
import logging
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

logger = logging.getLogger("cli-call")
logger.setLevel(logging.INFO)

# Configuration
room_name_prefix = "cli-call-"
agent_name = "senior-care-agent"
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")


# 전화 연결 함수
async def make_call(phone_number: str):
    """Make a call to the given phone number using LiveKit SIP"""

    # room 이름 및 전화번호 메타데이터 구성
    room_name = f"{room_name_prefix}{phone_number}"
    metadata = json.dumps({"phone_number": phone_number})

    # LiveKit API 클라이언트 생성
    lkapi = api.LiveKitAPI()

    # 에이전트 디스패치 요청 (해당 room에 senior-care-agent 할당)
    logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")

    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name, room=room_name, metadata=metadata
        )
    )
    logger.info(f"Created dispatch: {dispatch}")
    logger.info(f"Dialing {phone_number}...")

    # SIP participant 생성 (실제 전화 발신)
    sip_participant = await lkapi.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=room_name,
            sip_trunk_id=outbound_trunk_id,
            sip_call_to=phone_number,
            participant_identity="phone_user",  # 상대방 식별자
        )
    )
    logger.info(f"Created SIP participant: {sip_participant}")

    # API 연결 종료
    await lkapi.aclose()


# CLI 파라미터 파싱 및 호출 "python make_call.py +821012345678" or "uv run make_call.py +821012345678"
async def main():
    parser = argparse.ArgumentParser(description="Make a phone call using LiveKit SIP.")
    parser.add_argument(
        "phone_number",
        type=str,
        help="Phone number in E.164 format (e.g., +821012345678)",
    )
    args = parser.parse_args()

    if not outbound_trunk_id:
        logger.error("SIP_OUTBOUND_TRUNK_ID is not set in the .env file.")
        return

    # 전화번호 유효성 검사
    phone_number = args.phone_number.strip()
    if not phone_number.startswith("+"):
        logger.error("Phone number must start with '+' (E.164 format).")
        return

    # 전화 걸기 함수 호출
    await make_call(phone_number)


if __name__ == "__main__":
    asyncio.run(main())
