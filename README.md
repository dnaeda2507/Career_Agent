# AI Career Assistant Agent

AI Career Assistant Agent is a dual-agent conversational system built with FastAPI and React.  
It represents the professional persona of Eda Dana by leveraging her CV and contextual summaries to answer recruiter-style and technical questions intelligently.

The system includes automatic response evaluation and a human-in-the-loop safety mechanism for sensitive queries.

---

## 🚀 Project Overview

This project provides a web-based conversational AI agent that:

- Reads and understands a CV PDF
- Uses a professional summary for context
- Generates contextual responses
- Evaluates its own responses using a secondary LLM
- Escalates sensitive or low-confidence cases via Telegram notification

The frontend provides a clean chat interface for real-time interaction.

---

## 🌟 Key Features

### 🧠 Primary Career Agent
- Represents Eda Dana’s professional persona
- Uses:
  - `EDA_DANA_CV.pdf`
  - `summary.txt`
- Answers academic, technical, and career-related questions

### 🧪 LLM-as-a-Judge (Evaluator Agent)
- A second LLM evaluates each generated response
- Scores responses from **1–10**
- If score < **7.0**, the response is automatically revised

### 👩‍💻 Human-in-the-Loop System
- Detects:
  - Sensitive questions (salary, private address, etc.)
  - Unknown or low-confidence answers
- Sends Telegram notification for manual intervention

### 📲 Real-Time Notifications
- Integrated with Telegram Bot API
- Sends instant alerts to a predefined chat ID

### 🧩 Volatile Memory
- Conversation history stored **in-memory per `user_id`**
- Enables contextual multi-turn conversations
- No database persistence (ephemeral session-based memory)

### 📝 Logging
- All interactions are recorded in: `career_agent_logs.txt`

---

## 🗂️ System Architecture Overview

### Simple Workflow Diagram

```text
[ Employer ]
    |
    v
( React UI )
    |
    v
[ FastAPI Backend ]
    |
    v
[ Career Agent (GPT-4o-mini) ]
    |
    v
[ Response Evaluator Agent ]
   /                       \
(Score < 7)            (Score >= 7)
    |                       |
[ Automatic Revision ]  [ Final Response ]
                              |
                              v
                 [ Telegram Notification ]
                              |
                        ( Your Phone )
```

Or visually:

![System Architecture Diagram](./simple_architecture.svg)

---

## 🛠️ Technology Stack

### Backend

- FastAPI
- OpenAI GPT-4o-mini
- PyPDF
- Uvicorn

### Frontend

- React (TypeScript)
- Tailwind CSS

### Notifications

- Telegram Bot API

### Deployment

- Docker
- Hugging Face Spaces
- https://huggingface.co/spaces/edahug/career_agent 
---

## 📂 Repository Structure

```
Career_Agent/
├── backend/
│   ├── app.py              # FastAPI core & Dual-Agent logic
│   ├── EDA_DANA_CV.pdf     # Knowledge base for the agent
│   ├── summary.txt         # Professional context summary
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/                # React components & API service
│   └── package.json        # Frontend dependencies
├── simple_architecture.svg # Simple logic diagram
└── README.md               # Project documentation
```

---

## ⚙️ Quick Start

### 1️⃣ Environment Configuration

Create a `.env` file inside the `backend/` directory:
```
OPENAI_API_KEY=your_openai_key
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

### 2️⃣ Run Backend

```bash
cd backend
python -m venv venv
pip install -r requirements.txt
uvicorn app:app --reload
```

Backend runs at:  
http://localhost:8000

---

### 3️⃣ Run Frontend

```bash
cd frontend
npm install
npm start
```

Frontend runs at:  
http://localhost:3000

---

**Environment Variables**
- `OPENAI_API_KEY` — OpenAI API key used by the backend OpenAI client.
- `TELEGRAM_TOKEN` — Telegram bot token (optional; used for notifications).
- `TELEGRAM_CHAT_ID` — Telegram chat id to receive

**Architecture (high level)**
- Browser (React) <-> FastAPI backend <-> OpenAI API
- Notifications: FastAPI -> Telegram (optional)
- Data: CV PDF and `summary.txt` are read at startup; conversation memory is ephemeral (in-memory).