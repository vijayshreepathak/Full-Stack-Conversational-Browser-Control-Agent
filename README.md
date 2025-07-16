# Conversational Browser Control Agent

> An end-to-end AI agent that **controls a real Chrome browser** through natural-language conversation and visibly sends emails from the Gmail web UI.  
> **Absolutely no Gmail API, SMTP, or indirect form requests** are used—every action is pure Playwright-driven automation that a human could replicate by hand.

## 📑 Table of Contents
1. [Key Features](#key-features)  
2. [System Architecture](#system-architecture)  
3. [Technology Stack](#technology-stack)  
4. [Setup Guide](#setup-guide)  
5. [Running the Project](#running-the-project)  
6. [How It Works – End-to-End Flow](#how-it-works--endtoend-flow)  
7. [Screenshots / Demo](#screenshots--demo)  
8. [Troubleshooting](#troubleshooting)  
9. [Notable Challenges & Solutions](#notable-challenges--solutions)  
10. [License & Credits](#license--credits)

## Key Features
- **Natural-language commands** (e.g., “Email my manager about Monday’s leave”).
- **Dynamic information gathering**: prompts the user for any missing details.
- **Playwright-powered browser control**:
  - Opens Chrome, navigates to Gmail.
  - Logs in, handles optional “Sign-in faster / Passkey” dialogs.
  - Writes & sends the email, taking a screenshot after every major step.
- **Inline visual feedback**: screenshots appear directly in the chat stream.
- **AI-generated subject & body**: OpenAI crafts professional-sounding messages.
- **100% Gmail-UI driven**—no hidden programmatic email endpoints.

## System Architecture

```mermaid
graph TD
    A[User] -->|Chat| B(Frontend: React Chat UI)
    B -->|WebSocket| C(Backend WebSocket Server)

    C --> D[Conversation Manager]
    C --> E[OpenAI Service]
    C --> F[Browser Controller (Playwright)]

    F --> G[Real Chrome Browser]
    F --> H[Screenshot Handler]
    H -->|Base64| C
    C -->|Status + Images| B
```

**Why it matters:** every arrow from F onward represents real clicks, typing, and waits inside a live browser session—providing complete transparency and human-level capability.

## Technology Stack

| Layer               | Tech            | Rationale |
|---------------------|-----------------|-----------|
| Frontend            | React (Vite)    | Lightweight SPA, fast dev-reload, native PWA support. |
| Realtime Channel    | WebSocket       | Pushes status & screenshots with sub-second latency. |
| Backend Runtime     | Python 3.10     | Rapid prototyping, rich ecosystem for AI & automation. |
| Browser Automation  | Playwright      | Modern, fast, resilient selectors, Chrome support. |
| AI Content Engine   | OpenAI GPT-4    | Generates subject lines & polished email bodies. |
| Secrets Management  | `python-dotenv` | Keeps API keys & credentials outside the codebase. |

## Setup Guide

### 1 -  Clone
```bash
git clone https://github.com//conversational-browser-agent.git
cd conversational-browser-agent
```

### 2 -  Backend
```bash
cd backend
pip install -r ../requirements.txt
playwright install  # downloads Chrome driver
```

Create `backend/.env`:

```dotenv
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3 -  Frontend
```bash
cd ../frontend
npm install
```

## Running the Project

```bash
# ① start backend websocket server
cd backend
python websocket_server.py
```

```bash
# ② start React frontend
cd ../frontend
npm start          # http://localhost:3000
```

Default ports  
| Service | Port |
|---------|------|
| Backend WebSocket | **8765** |
| React Dev-Server | **3000** |

## How It Works – End-to-End Flow

1. **User** types:  
   `“Send a leave request to my manager for 14-16 Aug.”`
2. **Conversation Manager** extracts intent & missing slots → asks follow-up questions.
3. Once all details are collected, **GPT-4** drafts subject & body.
4. **Browser Controller**:
   1. Launches Chrome with Playwright.  
   2. Navigates → `https://mail.google.com`.  
   3. Logs in (handling optional passkey prompts).  
   4. Opens **Compose**, fills **To → Subject → Body** (Tab confirms recipient chip).  
   5. Clicks **Send** (Ctrl + Enter fallback).  
   6. Captures a screenshot after each action.
5. **Screenshots & status** stream back to the chat UI, giving users live proof of every step.

**No APIs, no SMTP, no hidden form-posts**—just visible browser automation.

## Screenshots / Demo

| Step | Preview |
|------|---------|
| Gmail Login Loaded | `gmail_homepage.png` |
| Password Entered   | `gmail_password_filled.png` |
| Inbox Ready        | `gmail_inbox_loaded.png` |
| Compose Window     | `gmail_compose_clicked.png` |
| Recipient & Subject Filled | `recipient_subject_filled.png` |
| Email Sent Confirmation | `sent_ok.png` |

*(See the `screenshots/` folder for the full sequence.)*

## Troubleshooting

| Issue | Checklist |
|-------|-----------|
| **Gmail asks for 2FA / phone** | Use a dedicated test account without 2FA, or complete the prompt manually once—Playwright will resume. |
| **Email stuck in Drafts** | Check selector updates in `browser_controller.py`; Google may have renamed classes. |
| **Screenshots not showing** | Confirm WebSocket connection (`ws://localhost:8765`) isn’t blocked by a firewall. |
| **OpenAI errors** | Verify `OPENAI_API_KEY`, usage quota, and model availability. |
| **Port already in use** | Set `WS_PORT` or `VITE_PORT` env vars before start-up. |

## Notable Challenges & Solutions

| Challenge | Fix |
|-----------|-----|
| Frequent Gmail DOM changes | Multiple fallback selectors + fail-fast screenshots for quicker debugging. |
| Subject text typed into *To* field | After filling *To*, script presses **Tab** to create the chip before moving on. |
| Windows-invalid screenshot names | Sanitization function strips illegal characters across OSes. |
| Slow network causing timeouts | Adaptive waits (`wait_for` + generous timeouts) and retry logic. |
| User transparency | Inline images in chat keep users informed—no “black-box” actions. |


Built with ♥ by **Vijayshree**.

Special thanks to:
- Microsoft **Playwright** team – for rock-solid automation tools.  
- **OpenAI** – for world-class language models.  
- **Proxy Convergence AI** – inspirational UX reference.

> *“Real agents don’t call APIs, they move pixels.”*