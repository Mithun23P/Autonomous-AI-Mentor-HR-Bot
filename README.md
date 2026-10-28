# Autonomous AI Mentor & HR Review Bot 

An autonomous, multi-modal conversational AI agent named **Priya** designed to conduct end-to-end technical project reviews and intern code evaluations over **Google Meet**. 

The system operates in real-time: it joins scheduled Google Meet calls autonomously, converses with natural human prosody, dynamically ingests and audits technical project report PDFs via FastAPI, executes live oral defenses against candidate architectures, and dispatches detailed evaluation scorecards directly to the candidate's inbox.

---

## Key System Capabilities

- **Autonomous Google Meet Ingress:** Uses Playwright to navigate into Google Meet sessions, handle audio/video device permissions, bypass waiting lobbies, and unmute hardware streams programmatically.
- **Sub-Second Audio Pipeline:**
  - **Ears:** Localized `faster-whisper` (`tiny.en` quantized to `int8`) running on-device for ultra-low latency, zero-cloud transcription.
  - **Brain:** Low-latency inference via Google Gemini (`google-genai` SDK) configured with an automatic multi-model failover engine to eliminate `503 Service Unavailable` and `429 Quota Exhaustion` interruptions.
  - **Voice:** High-fidelity expressive neural audio synthesis using Microsoft `edge-tts` with natural pitch adjustments and human conversation fillers ("Awesome!", "Got it", "Right").
- **Dynamic Project PDF Audit:** Candidate submits their architecture report PDF via a local FastAPI portal (`localhost:8000`). The document is parsed via the Gemini Files API into an architectural briefing containing highlights, potential red flags, and tailored verification questions.
- **Hardware-Level Acoustic Echo Suppression:** Splits audio routing between virtual audio cables and real physical monitor speakers while using state tracking (`is_speaking`) to completely eliminate audio self-feedback.
- **Automated Scorecard Dispatch:** Following call termination, the complete dialogue transcript is evaluated across four core engineering pillars (Architecture, Code Quality, Live Oral Defense, and Verdict) and emailed via secure SMTP SSL (`port 465`).

---

## Architecture Flow

[Candidate in Google Meet]
│
▼ (Realtek Audio Mic / Listen Dev 1)
[faster-whisper int8 STT]
│ (Streamed User Transcript)
▼
[Priya Core Brain: Gemini 3.5 Flash / Model Pool] ◄── [PDF Audit Briefing from localhost:8000]
│ (Sub-25 Word Natural Conversational Turn)
▼
[edge-tts Speech Synthesizer]
│ (Generated Audio Buffer)
▼
┌──────────────────────────────────────────────┐
│       Dual Hardware Audio Routing            │
├──────────────────────┬───────────────────────┤
│  VB-Audio Cable      │ Realtek Laptop        │
│  (Device Index 5)    │ Speakers (Dev 4)      │
│  → Feeds Meet Mic    │ → Real-time Monitor   │
└──────────────────────┴───────────────────────┘
│
(Call Ends)
▼
[Post-Session Evaluator] ──► [Gmail SMTP_SSL: Port 465] ──► [Candidate Inbox Scorecard]


---

## Project Structure

```bash
ai_intern_mentor/
├── app.py                 # FastAPI server for candidate project PDF upload & Gemini audit
├── meet_live_audio.py     # Main runner: Playwright automation, audio routing, live bot loop
├── mailer.py              # SSL-encrypted SMTP performance scorecard generator & mailer
├── scheduler.py           # Automated execution scheduler for bi-weekly meeting cadence
├── report_analyzer.py     # Standalone PDF extraction & architectural gap analysis utility
├── check_devices.py       # Hardware sound device diagnostic utility
├── list_my_models.py      # Active Gemini model discovery script
├── current_briefing.json  # Runtime active briefing shared between FastAPI and Priya
├── .gitignore             # Strict exclusion for secrets (.env) and sessions
├── .env.example           # Template for required environment variables
└── static/
    └── index.html         # Candidate upload UI
Hardware Audio Routing Setup
To route synthesized AI speech into the Google Meet microphone stream without cutting off your ability to monitor what the bot is saying, configure a virtual audio bridge:

Install VB-Audio Virtual Cable.

Run python check_devices.py to identify your exact audio indices:

SPEAK_DEVICE_INDEX (e.g., 5): Set to CABLE Input (VB-Audio Virtual Cable). This routes Priya's voice directly into Google Meet.

LAPTOP_SPEAKER_INDEX (e.g., 4): Set to your physical speaker output (Realtek Audio) so you can hear Priya speaking locally.

LISTEN_DEVICE_INDEX (e.g., 1): Set to your microphone hardware (Microphone Array) to capture the candidate's speech.

Setup & Installation
1. Prerequisites
Python 3.10+

Google Chrome browser installed

A Google Cloud Gemini API key (Google AI Studio)

A Gmail account with an App Password enabled (16-character code)

2. Clone the Repository
Bash
git clone [https://github.com/Mithun23P/Autonomous-AI-Mentor-HR-Bot.git](https://github.com/Mithun23P/Autonomous-AI-Mentor-HR-Bot.git)
cd Autonomous-AI-Mentor-HR-Bot
3. Create a Virtual Environment & Install Dependencies
Bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/macOS

pip install fastapi uvicorn playwright sounddevice soundfile edge-tts faster-whisper numpy google-genai python-dotenv schedule
playwright install chromium
4. Configure Environment Variables
Copy .env.example to .env:

Bash
cp .env.example .env
Populate .env with your actual secrets:

Code snippet
GEMINI_API_KEY=your_gemini_api_key_here
SENDER_EMAIL=your_email@gmail.com
SENDER_APP_PASSWORD=your_16_digit_app_password
Running the System
Step 1: Start the Candidate PDF Submission Portal
In Terminal 1:

Bash
python app.py
Accessible at http://localhost:8000. The student uploads their project architecture report PDF here.

Step 2: Launch the Google Meet AI Mentor
In Terminal 2:

Bash
python meet_live_audio.py
Priya will launch a dedicated browser session, bypass lobby checks, enter the call, unmute her microphone, and initiate the review.

Step 3: Call Wrap-Up & Evaluation
When the session is complete, press Ctrl + C in the meet_live_audio.py terminal. Priya will:

Aggregate the complete dialogue history.

Synthesize an objective technical review scorecard across architecture, code quality, and verbal defense.

Dispatch an HTML evaluation email to the candidate's email address.
