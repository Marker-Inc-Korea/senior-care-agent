# Senior Care Agent Recipe using LiveKit & Twilio

A voice-enabled AI agent system designed for proactive wellness checks on elderly individuals living alone. Built with LiveKit Agents and OpenAI, this system provides personalized, context-aware conversations through phone calls.

## Features

- **Make Phone Calls**: Initiates outbound calls to elderly individuals for wellness checks
- **Multi-Agent System**: Modular design with specialized agents for different conversation phases
- **Voice Interaction**: Complete voice-based interaction using speech-to-text and text-to-speech or speech-to-speech using OpenAI Realtime API
- **Identity Verification**: Simple secure identity confirmation before proceeding with wellness checks
- **Health Monitoring**: Contextual health status inquiries with conversation history
- **Emergency Response**: Automatic transfer to human agents during emergencies
- **Request Logging**: Tracks and logs user concerns for follow-up by care providers
- **Noise Cancellation**: Enhanced audio quality for better communication

## Architecture

The system consists of two main agent types:

### IntakeAgent
- **Purpose**: Initial identity verification and greeting
- **Functions**: 
  - Verifies caller identity by name
  - Transfers to health check-in upon successful verification
  - Terminates call if identity cannot be confirmed

### CheckInAgent
- **Purpose**: Conducts wellness check-in conversations
- **Functions**:
  - Asks about daily health and wellbeing
  - References previous conversation history for continuity
  - Registers user requests and concerns
  - Transfers emergency calls to human agents
  - Properly terminates calls when complete


### Project Structure
```
senior-care-agent/
├── agent.py                 # Main agent implementation
├── realtime_agent.py        # Realtime API variant
├── make_call.py            # Outbound calling script
├── utils.py                # Utility functions
├── prompts/                # Agent instruction templates
│   ├── intake_prompt.yaml
│   └── check_in_prompt.yaml
├── data/                   # Data storage
│   ├── history/            # Conversation history
│   └── requests/           # User request logs
└── pyproject.toml          # Project configuration
```

## Technology Stack

- **LiveKit Agents**: Real-time voice communication framework
- **OpenAI**: GPT-4o-mini for natural language processing
- **Deepgram**: Speech-to-text conversion
- **Cartesia**: Text-to-speech synthesis
- **Silero VAD, OpenAI's Server VAD / Semantic VAD**: Voice activity detection
- **SIP Integration**: Phone system connectivity

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd senior-care-agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   # or using uv
   uv sync
   ```

3. **Environment Setup**:
   Copy the example environment file and configure your API keys:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` with your actual API keys and configuration:
   ```env
   # LiveKit Configuration
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   
   # OpenAI Configuration
   OPENAI_API_KEY=sk-your-openai-api-key
   
   # Speech Services
   CARTESIA_API_KEY=sk_car_your_cartesia_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   
   # Twilio SIP Configuration
   SIP_OUTBOUND_TRUNK_ID=your_twilio_sip_trunk_id
   
   # Human Agent Phone Number (for emergency transfers)
   HUMAN_AGENT_PHONE=+1234567890
   ```

## Prerequisites & Service Setup

This project requires configuration of external services for voice communication and telephony integration.

### LiveKit Setup

LiveKit provides the real-time communication infrastructure for voice agents.

1. **Create a LiveKit Cloud Account**:
   - Sign up at [LiveKit Cloud](https://cloud.livekit.io/)
   - Create a new project

2. **Get API Credentials**:
   - Navigate to your project settings
   - Copy the following values to your `.env` file:
     - `LIVEKIT_URL`: Your LiveKit server URL (e.g., `wss://your-project.livekit.cloud`)
     - `LIVEKIT_API_KEY`: Your API key
     - `LIVEKIT_API_SECRET`: Your API secret

3. **Enable SIP Integration**:
   - Check from [here](https://docs.livekit.io/sip/quickstarts/configuring-sip-trunk/). You'll need to create `SIP_OUTBOUND_TRUNK_ID` in order to run the agent.

### Twilio Elastic SIP Trunking Setup

Twilio Elastic SIP Trunking enables the system to make and receive phone calls.

1. **Create a Twilio Account**:
   - Sign up at [Twilio Console](https://console.twilio.com/)
   - Purchase a phone number for outbound calls

2. **Set up Elastic SIP Trunking**:
   - Check from [here](https://docs.livekit.io/sip/quickstarts/configuring-twilio-trunk/). 


### Testing Your Setup

After configuration, test your setup:

1. **Download VAD models with this command**
    ```bash
    python agent.py download-files
    ```
2. **Verify LiveKit Connection**:
   ```bash
   python agent.py dev
   ```
3. **Test Outbound Calling**:
   ```bash
   python make_call.py +821012345678
   ```

## Usage

### Running the Agent on LiveKit

Start with this command:

```bash
python agent.py dev
# or for the realtime version
python realtime_agent.py dev
# or using uv works as well
uv run agent.py dev
```

### Making Outbound Calls

Use the call script to initiate wellness check calls:

```bash
python make_call.py +1234567890
# or using uv
uv run make_call.py +1234567890
```

### Agent Variants

The project includes two agent implementations:

- **`agent.py`**: Standard implementation using separate STT/TTS/LLM components
- **`realtime_agent.py`**: Uses OpenAI's Realtime API for lower latency voice interactions

## Configuration

### Prompt Customization

Agent behavior is configured through YAML prompt files in the `prompts/` directory:

- `intake_prompt.yaml`: Identity verification agent instructions
- `check_in_prompt.yaml`: Wellness check agent instructions

### Data Storage

- **Conversation History**: Stored in `data/history/history.json`
- **User Requests**: Logged to `data/requests/requests.csv`

## Key Components

### Utilities (`utils.py`)
- Prompt loading from YAML files
- Conversation history management
- Request logging functionality

### Base Agent Class
- Common functionality for all agent types
- Context management and agent switching
- Chat history truncation and cleanup

### Function Tools
- `verify_identity()`: Name-based identity verification
- `register_request()`: Log user concerns and requests
- `transfer_call_to_human()`: Emergency transfer to human agents
- `end_call()`: Graceful call termination with history saving

## License
MIT © Marker-Inc-Korea
