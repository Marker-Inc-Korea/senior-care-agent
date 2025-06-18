# LiveKit과 Twilio를 활용한 시니어 케어 에이전트 레시피

독거노인을 위한 능동적 안부확인 시스템입니다. LiveKit Agents와 OpenAI를 활용하여 전화를 통한 개인화되고 맥락 인식이 가능한 대화를 제공합니다.

## 주요 기능

- **전화 발신**: 독거노인을 위한 안부확인 전화 자동 발신
- **멀티 에이전트 시스템**: 대화 단계별 전문화된 에이전트를 통한 모듈형 설계
- **음성 상호작용**: 음성-텍스트, 텍스트-음성 변환 또는 OpenAI Realtime API를 통한 완전한 음성 기반 상호작용
- **신원 확인**: 안부확인 진행 전 간단하고 안전한 신원 확인
- **건강 모니터링**: 대화 기록을 활용한 맥락적 건강 상태 문의
- **응급 대응**: 응급상황 시 사람 상담원으로 자동 연결
- **요청사항 기록**: 돌봄 제공자의 후속 조치를 위한 사용자 요구사항 추적 및 기록
- **노이즈 제거**: 더 나은 소통을 위한 향상된 오디오 품질

## 아키텍처

시스템은 두 가지 주요 에이전트 타입으로 구성됩니다:

### IntakeAgent
- **목적**: 초기 신원 확인 및 인사
- **기능**: 
  - 발신자 신원을 이름으로 확인
  - 신원 확인 성공 시 건강 체크인으로 전환
  - 신원 확인 실패 시 통화 종료

### CheckInAgent
- **목적**: 안부확인 대화 수행
- **기능**:
  - 일상 건강 및 안녕 상태 문의
  - 연속성을 위한 이전 대화 기록 참조
  - 사용자 요청사항 및 우려사항 등록
  - 응급 통화를 사람 상담원에게 전환
  - 통화 적절한 종료

### 프로젝트 구조
```
senior-care-agent/
├── agent.py                 # 메인 에이전트 구현
├── realtime_agent.py        # Realtime API 버전
├── make_call.py            # 발신 통화 스크립트
├── utils.py                # 유틸리티 함수
├── prompts/                # 에이전트 지시사항 템플릿
│   ├── intake_prompt.yaml
│   └── check_in_prompt.yaml
├── data/                   # 데이터 저장소
│   ├── history/            # 대화 기록
│   └── requests/           # 사용자 요청 로그
└── pyproject.toml          # 프로젝트 설정
```

## 기술 스택

- **LiveKit Agents**: 실시간 음성 통신 프레임워크
- **OpenAI**: 자연어 처리를 위한 GPT-4o-mini
- **Deepgram**: 음성-텍스트 변환
- **Cartesia**: 텍스트-음성 합성
- **Silero VAD, OpenAI의 Server VAD / Semantic VAD**: 음성 활동 감지
- **SIP 통합**: 전화 시스템 연결

## 설치

1. **저장소 복제**:
   ```bash
   git clone https://github.com/Marker-Inc-Korea/senior-care-agent.git
   cd senior-care-agent
   ```

2. **의존성 설치**:
   ```bash
   pip install -e .
   # 또는 uv 사용
   uv sync
   ```

3. **환경 설정**:
   예제 환경 파일을 복사하고 API 키를 설정하세요:
   ```bash
   cp .env.example .env
   ```
   
   그 다음 `.env` 파일을 실제 API 키와 설정으로 편집하세요:
   ```env
   # LiveKit 설정
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   
   # OpenAI 설정
   OPENAI_API_KEY=sk-your-openai-api-key
   
   # 음성 서비스
   CARTESIA_API_KEY=sk_car_your_cartesia_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   
   # Twilio SIP 설정
   SIP_OUTBOUND_TRUNK_ID=your_twilio_sip_trunk_id
   
   # 사람 상담원 전화번호 (응급 전환용)
   HUMAN_AGENT_PHONE=+1234567890
   ```

## 필수 조건 및 서비스 설정

이 프로젝트는 음성 통신 및 전화 통신 연동을 위한 외부 서비스 설정이 필요합니다.

### LiveKit 설정

LiveKit은 음성 에이전트를 위한 실시간 통신 인프라를 제공합니다.

1. **LiveKit Cloud 계정 생성**:
   - [LiveKit Cloud](https://cloud.livekit.io/)에서 가입
   - 새 프로젝트 생성

2. **API 자격 증명 얻기**:
   - 프로젝트 설정으로 이동
   - 다음 값들을 `.env` 파일에 복사:
     - `LIVEKIT_URL`: LiveKit 서버 URL (예: `wss://your-project.livekit.cloud`)
     - `LIVEKIT_API_KEY`: API 키
     - `LIVEKIT_API_SECRET`: API 시크릿

3. **SIP 통합 활성화**:
   - [여기](https://docs.livekit.io/sip/quickstarts/configuring-sip-trunk/)에서 확인하세요. 에이전트 실행을 위해 `SIP_OUTBOUND_TRUNK_ID`를 생성해야 합니다.

### Twilio Elastic SIP Trunking 설정

Twilio Elastic SIP Trunking은 시스템이 전화를 걸고 받을 수 있게 해줍니다.

1. **Twilio 계정 생성**:
   - [Twilio Console](https://console.twilio.com/)에서 가입
   - 발신 통화용 전화번호 구매

2. **Elastic SIP Trunking 설정**:
   - [여기](https://docs.livekit.io/sip/quickstarts/configuring-twilio-trunk/)에서 확인하세요.

### 설정 테스트

설정 후 다음과 같이 테스트하세요:

1. **이 명령으로 VAD 모델 다운로드**
    ```bash
    python agent.py download-files
    ```
    
2. **LiveKit 연결 확인**:
   ```bash
   python agent.py dev
   ```
   
3. **발신 통화 테스트**:
   ```bash
   python make_call.py +821012345678
   ```

## 사용법

### LiveKit에서 에이전트 실행

다음 명령으로 시작하세요:

```bash
python agent.py dev
# 또는 realtime 버전의 경우
python realtime_agent.py dev
# uv 사용도 가능합니다
uv run agent.py dev
```

### 발신 통화 만들기

안부확인 통화를 시작하려면 통화 스크립트를 사용하세요:

```bash
python make_call.py +1234567890
# 또는 uv 사용
uv run make_call.py +1234567890
```

### 에이전트 변형

프로젝트에는 두 가지 에이전트 구현이 포함되어 있습니다:

- **`agent.py`**: 별도의 STT/TTS/LLM 컴포넌트를 사용하는 표준 구현
- **`realtime_agent.py`**: 더 낮은 지연시간의 음성 상호작용을 위한 OpenAI의 Realtime API 사용

## 설정

### 프롬프트 사용자 정의

에이전트 동작은 `prompts/` 디렉토리의 YAML 프롬프트 파일을 통해 설정됩니다:

- `intake_prompt.yaml`: 신원 확인 에이전트 지시사항
- `check_in_prompt.yaml`: 안부확인 에이전트 지시사항

### 데이터 저장

- **대화 기록**: `data/history/history.json`에 저장
- **사용자 요청**: `data/requests/requests.csv`에 기록

## 주요 구성 요소

### 유틸리티 (`utils.py`)
- YAML 파일에서 프롬프트 로딩
- 대화 기록 관리
- 요청사항 로깅 기능

### 베이스 에이전트 클래스
- 모든 에이전트 타입의 공통 기능
- 컨텍스트 관리 및 에이전트 전환
- 채팅 기록 절삭 및 정리

### 함수 도구
- `verify_identity()`: 이름 기반 신원 확인
- `register_request()`: 사용자 우려사항 및 요청 기록
- `transfer_call_to_human()`: 사람 상담원으로 응급 전환
- `end_call()`: 기록 저장과 함께 우아한 통화 종료

## 라이선스

MIT © Marker-Inc-Korea