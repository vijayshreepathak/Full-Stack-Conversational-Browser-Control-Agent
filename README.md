# Conversational Browser Control Agent

> An end-to-end AI agent that **controls a real Chrome browser** through natural-language conversation and visibly sends emails from the Gmail web UI.
> No Gmail API, no SMTP, no hidden form-posts — every action is pure Playwright-driven automation that a human could replicate by hand.

---

## Table of Contents

1. [Key Features](#key-features)
2. [System Architecture](#system-architecture)
3. [Detailed Component Architecture](#detailed-component-architecture)
4. [Data Flow — End to End](#data-flow--end-to-end)
5. [Component Breakdown](#component-breakdown)
6. [Project Structure](#project-structure)
7. [Tech Stack](#tech-stack)
8. [Setup & Installation](#setup--installation)
9. [Running the Project](#running-the-project)
10. [Environment Variables](#environment-variables)
11. [Key Design Decisions](#key-design-decisions)
12. [Bug Fixes Applied](#bug-fixes-applied)
13. [Troubleshooting](#troubleshooting)
14. [Future Enhancements](#future-enhancements)
15. [Credits](#credits)

---

## Key Features

- **Natural-language conversation** — the agent asks for any missing details instead of demanding them upfront
- **Step-by-step visual feedback** — every browser action (field filled, button clicked, 2FA wait) streams a screenshot back into the chat in real time
- **2FA / Google Prompt support** — detects the phone-approval screen and polls every 3 seconds for up to 120 seconds, continuing automatically once approved
- **AI-generated email content** — OpenAI GPT-3.5-turbo writes a professional subject and body from your context; falls back gracefully to hardcoded strings with no API key
- **Password masking** — input switches to `type="password"` when the agent asks for credentials; only `••••••••` is stored in chat history
- **Resilient selector strategy** — multiple CSS selector fallbacks handle Gmail UI changes without breaking the flow
- **100% browser-UI driven** — no hidden API endpoints, no SMTP relay

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER'S WEB BROWSER                               │
│                        localhost:3000  (React)                          │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  App.js  →  ChatInterface.jsx                                     │  │
│  │               │                                                   │  │
│  │    ┌──────────▼──────────┐     ┌──────────────────────────────┐  │  │
│  │    │   MessageBubble     │     │  websocket_client.js         │  │  │
│  │    │   .jsx              │     │  ┌──────────────────────┐    │  │  │
│  │    │  ┌───────────────┐  │     │  │ connectWebSocket()   │    │  │  │
│  │    │  │ScreenshotDisp │  │     │  │ sendMessage()        │    │  │  │
│  │    │  │lay.jsx        │  │     │  │ subscribeToMessages()│    │  │  │
│  │    │  │<img base64…/> │  │     │  │ pendingMessages[]    │    │  │  │
│  │    │  └───────────────┘  │     │  │ onclose/onerror →   │    │  │  │
│  │    └─────────────────────┘     │  │   system chat msg   │    │  │  │
│  │                                └──────────────────────────┘  │  │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
                         WebSocket     │   ws://localhost:9000
                         JSON frames   │   { sender, text, screenshot }
                                       │
┌──────────────────────────────────────▼──────────────────────────────────┐
│                          PYTHON BACKEND                                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    websocket_server.py                             │  │
│  │                   (asyncio + websockets 15.x)                     │  │
│  │                                                                    │  │
│  │   handle_client(websocket)                                         │  │
│  │    │                                                               │  │
│  │    ├─ PHASE 1: Browser startup                                     │  │
│  │    │   launch_browser() → navigate_to_gmail()                      │  │
│  │    │   → send screenshot of Gmail homepage                         │  │
│  │    │                                                               │  │
│  │    ├─ PHASE 2: Conversational field collection                     │  │
│  │    │   required_fields = [email, password, recipient,              │  │
│  │    │                      purpose, leave_dates, manager_email]     │  │
│  │    │   while missing fields:                                       │  │
│  │    │     send prompt → recv answer → store in context              │  │
│  │    │                                                               │  │
│  │    ├─ PHASE 3: AI content generation                               │  │
│  │    │   generate_subject(context) → subject string                  │  │
│  │    │   generate_body(context)    → body string                     │  │
│  │    │                                                               │  │
│  │    ├─ PHASE 4: Login with live streaming                           │  │
│  │    │   login(email, pwd, step_callback)                            │  │
│  │    │   step_callback(text, png) → WebSocket send                   │  │
│  │    │                                                               │  │
│  │    └─ PHASE 5: Compose + send with live streaming                  │  │
│  │        compose_email(to, subj, body, step_callback)                │  │
│  │        step_callback(text, png) → WebSocket send                   │  │
│  └──────────────┬────────────────┬──────────────────────────────────┘   │
│                 │                │                                        │
│  ┌──────────────▼──┐  ┌──────────▼──────────────────────────────────┐   │
│  │  AIIntegration  │  │          BrowserController                  │   │
│  │                 │  │         (browser_controller.py)             │   │
│  │  OpenAI         │  │                                             │   │
│  │  GPT-3.5-turbo  │  │  launch_browser()                           │   │
│  │                 │  │   └─ Playwright → real Chrome (headless=F)  │   │
│  │  generate_      │  │   └─ Anti-bot: navigator.webdriver = undef  │   │
│  │  subject(ctx)   │  │                                             │   │
│  │                 │  │  login(email, pwd, step_callback)           │   │
│  │  generate_      │  │   ├─ fill email → click Next                │   │
│  │  body(ctx)      │  │   ├─ dismiss passkey/sign-in dialogs        │   │
│  │                 │  │   ├─ fill password → click Next             │   │
│  │  No API key?    │  │   ├─ detect 2FA prompt (7 selectors)        │   │
│  │  → fallback     │  │   │   poll inbox every 3s (max 120s)        │   │
│  │    strings      │  │   └─ confirm inbox loaded                   │   │
│  └─────────────────┘  │                                             │   │
│                        │  compose_email(to, subj, body, callback)   │   │
│  ┌──────────────────┐  │   ├─ dismiss popups                        │   │
│  │ Conversation     │  │   ├─ open compose window (5 selectors)     │   │
│  │ Manager          │  │   ├─ fill To / Subject / Body              │   │
│  │                  │  │   └─ click Send (fallback: Ctrl+Enter)     │   │
│  │ context = {      │  │                                             │   │
│  │   email,         │  │  try_click(selectors[], timeout)           │   │
│  │   password,      │  │   └─ loops through selector list,          │   │
│  │   recipient,     │  │      tolerates Gmail DOM changes           │   │
│  │   purpose,       │  │                                             │   │
│  │   leave_dates,   │  │  ScreenshotHandler                         │   │
│  │   manager_email  │  │   capture(page, filename)                  │   │
│  │ }                │  │   → page.screenshot() → PNG file           │   │
│  └──────────────────┘  │   → base64 encode → embed in JSON frame    │   │
│                        └────────────────────────┬────────────────────┘  │
└────────────────────────────────────────────────-│───────────────────────┘
                                                  │
                                   Playwright CDP │ (Chrome DevTools Protocol)
                                                  │
┌─────────────────────────────────────────────────▼───────────────────────┐
│                    Real Chrome Browser (headless=False)                  │
│                                                                          │
│    https://mail.google.com                                               │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│    │  Login page  │→ │  2FA prompt  │→ │    Inbox     │                 │
│    │  email+pwd   │  │  (optional)  │  │  + Compose   │                 │
│    └──────────────┘  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Architecture

```
websocket_server.py
│
│  CONVERSATION STATE MACHINE
│  ┌─────────────────────────────────────────────────────────────┐
│  │  State: last_prompted_field                                 │
│  │                                                             │
│  │  INIT ──► prompt "email?"                                   │
│  │    │                                                        │
│  │  recv(email) → context['email'] = val                       │
│  │    │                                                        │
│  │  missing = next(f for f in fields                           │
│  │               if not context.get(f))                        │
│  │    │                                                        │
│  │  ┌─── missing found ──► prompt next field ──► recv ──┐     │
│  │  │                                                    │     │
│  │  └────────────────────────────────────────────────────┘     │
│  │                                                             │
│  │  all fields filled ──► AI ──► login ──► compose ──► break  │
│  └─────────────────────────────────────────────────────────────┘
│
│  step_callback PATTERN
│  ┌─────────────────────────────────────────────────────────────┐
│  │  async def step_callback(text, screenshot_filename):        │
│  │      await websocket.send(json.dumps({                      │
│  │          "sender": "agent",                                 │
│  │          "text": text,                                      │
│  │          "screenshot": encode_screenshot(filename)          │
│  │      }))                                                    │
│  │                                                             │
│  │  Passed into login() and compose_email()                    │
│  │  Called after EVERY micro-action in the browser             │
│  └─────────────────────────────────────────────────────────────┘

browser_controller.py
│
│  try_click(selectors[], timeout)
│  ┌──────────────────────────────────────────────────┐
│  │  for sel in selectors:                           │
│  │      try:                                        │
│  │          wait_for_selector(sel, timeout)         │
│  │          click(sel)                              │
│  │          return True                             │
│  │      except PlaywrightTimeout:                   │
│  │          continue   # try next selector          │
│  │  return False                                    │
│  └──────────────────────────────────────────────────┘
│
│  2FA POLLING LOOP
│  ┌──────────────────────────────────────────────────┐
│  │  detect 2FA prompt (7 selectors)                 │
│  │       │                                          │
│  │       ▼  detected                                │
│  │  while waited < 120s:                            │
│  │      try wait_for inbox selector (2s)            │
│  │          → success: step_callback + break        │
│  │      check if 2FA prompt still visible           │
│  │          → step_callback("Still waiting…")       │
│  │      sleep(3s)                                   │
│  │      waited += 3                                 │
│  │  else: return timeout message                    │
│  └──────────────────────────────────────────────────┘

websocket_client.js
│
│  SINGLETON + SUBSCRIBER PATTERN
│  ┌──────────────────────────────────────────────────┐
│  │  module-level: socket, subscribers[], pending[]  │
│  │                                                  │
│  │  connectWebSocket(url)                           │
│  │   ├─ guard: skip if already OPEN/CONNECTING      │
│  │   ├─ onopen  → flush pendingMessages[]           │
│  │   ├─ onmessage → parse JSON → notify all subs    │
│  │   ├─ onclose → inject system message to chat     │
│  │   └─ onerror → inject system message to chat     │
│  │                                                  │
│  │  sendMessage(payload)                            │
│  │   ├─ OPEN       → send immediately               │
│  │   └─ CONNECTING → push to pendingMessages[]      │
│  │                                                  │
│  │  subscribeToMessages(fn) → returns unsubscribe() │
│  └──────────────────────────────────────────────────┘
```

---

## Data Flow — End to End

```
 User opens http://localhost:3000
         │
         ▼
 ChatInterface mounts
 → connectWebSocket('ws://localhost:9000')
         │
         │ TCP handshake
         ▼
 handle_client(websocket) fires on backend
 → try: launch_browser() + navigate_to_gmail()
 → capture gmail_homepage.png
 → SEND { text: "Opening Gmail...", screenshot: <base64> }
 → SEND { text: "What's your Gmail email?" }
         │
         │
  ┌──────▼──────────────────────────────────────────────┐
  │   FIELD COLLECTION LOOP (6 iterations)              │
  │                                                     │
  │  RECV user answer                                   │
  │  → context[last_prompted_field] = answer            │
  │  → find next missing field                          │
  │  → SEND prompt for next field                       │
  │                                                     │
  │  Fields: email → password → recipient               │
  │          → purpose → leave_dates → manager_email    │
  └──────────────────────────────────────────────────────┘
         │
         ▼  all 6 fields collected
 AIIntegration.generate_subject(context) → OpenAI / fallback
 AIIntegration.generate_body(context)    → OpenAI / fallback
         │
         ▼
 BrowserController.login(email, password, step_callback)
 ┌────────────────────────────────────────────────────────┐
 │  fill email → SEND { "Email filled", email_filled.png }│
 │  click Next → SEND { "Clicked Next", None }            │
 │  fill pwd   → SEND { "Password filled", pwd.png }      │
 │  click Next → SEND { "Clicked Next", None }            │
 │                                                        │
 │  2FA? ──yes──► SEND { "2FA detected", 2fa.png }        │
 │               poll every 3s:                          │
 │                 SEND { "Still waiting (Ns)", png }     │
 │               inbox loads:                            │
 │                 SEND { "2FA approved", inbox.png }     │
 │                                                        │
 │  SEND { "Inbox loaded", inbox_loaded.png }             │
 └────────────────────────────────────────────────────────┘
         │
         ▼
 BrowserController.compose_email(to, subject, body, step_callback)
 ┌────────────────────────────────────────────────────────┐
 │  dismiss popups → SEND { "Dismissed popups", None }    │
 │  open compose  → SEND { "Compose opened", None }       │
 │  fill To       → SEND { "Recipient filled", to.png }   │
 │  fill Subject  → SEND { "Subject filled", subj.png }   │
 │  fill Body     → SEND { "Body filled", body.png }      │
 │  click Send    → SEND { "Clicked Send", None }         │
 │  confirmation  → SEND { "Email sent!", confirm.png }   │
 └────────────────────────────────────────────────────────┘
         │
         ▼
 controller.close()   → Chrome window closes
 WebSocket connection ends
```

---

## Component Breakdown

### Backend

| File | Role | Key Methods |
|------|------|-------------|
| `websocket_server.py` | Orchestrator. Asyncio event loop, conversation state machine, drives AI + browser, streams every step over WebSocket | `handle_client()`, `encode_screenshot()`, `main()` |
| `browser_controller.py` | All Playwright automation. Login with 2FA, compose, send. Accepts `step_callback` to report micro-steps | `launch_browser()`, `login()`, `compose_email()`, `try_click()`, `dismiss_popups()` |
| `ai_integration.py` | OpenAI GPT-3.5-turbo wrapper. Generates subject + body. Graceful fallback when no API key | `generate_subject()`, `generate_body()` |
| `conversation_manager.py` | Thin dict wrapper for the 6 context fields | `update_context()` |
| `screenshot_handler.py` | Playwright screenshot → PNG file → base64 string | `capture()` |
| `app.py` | Standalone test harness (no WebSocket) for local browser testing | `main()` |

### Frontend

| File | Role |
|------|------|
| `ChatInterface.jsx` | Root chat UI. Connects WebSocket on mount, renders messages, detects password prompts and masks input |
| `MessageBubble.jsx` | Renders one chat bubble. Passes `screenshot` prop to `ScreenshotDisplay` |
| `ScreenshotDisplay.jsx` | `<img src={base64}>` — renders the live screenshot inline in the bubble |
| `websocket_client.js` | Singleton WebSocket manager with subscriber pattern, message queue, and error surfacing |

---

## Project Structure

```
Full-Stack-Conversational-Browser-Control-Agent/
│
├── backend/
│   ├── websocket_server.py      # Main entry point — WS server + orchestrator
│   ├── browser_controller.py    # Playwright automation (login, 2FA, compose, send)
│   ├── ai_integration.py        # OpenAI GPT-3.5-turbo integration
│   ├── conversation_manager.py  # Context dict (email, password, recipient…)
│   ├── screenshot_handler.py    # PNG capture → base64
│   └── app.py                   # Standalone test harness
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── App.js
│       ├── index.js
│       ├── components/
│       │   ├── ChatInterface.jsx     + ChatInterface.css
│       │   ├── MessageBubble.jsx     + MessageBubble.css
│       │   └── ScreenshotDisplay.jsx + ScreenshotDisplay.css
│       └── services/
│           └── websocket_client.js
│
├── requirements.txt             # Python dependencies
└── README.md
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend framework | React 19 (Create React App) | SPA, component-based UI |
| Frontend transport | Browser WebSocket API | Persistent connection for real-time screenshot streaming |
| Backend language | Python 3.9+ | asyncio-native |
| Backend WebSocket server | `websockets` 15.x | Asyncio-based server |
| Browser automation | Playwright (Chromium/Chrome) | CDP protocol, headless=False |
| AI text generation | OpenAI GPT-3.5-turbo (`openai` >= 1.0) | Subject + body generation; graceful fallback |
| Environment config | `python-dotenv` | Keeps API keys out of source |

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`
  *(adjust path in `browser_controller.py` line 17 if different)*
- (Optional) OpenAI API key

### Backend

```bash
cd backend
pip install -r ../requirements.txt
python -m playwright install chromium
```

### Frontend

```bash
cd frontend
npm install
```

---

## Running the Project

Open **two terminals**:

**Terminal 1 — Backend WebSocket server**
```bash
cd backend
python websocket_server.py
```

**Terminal 2 — React frontend**
```bash
cd frontend
npm start
```

Open **http://localhost:3000**. The chat connects automatically, Chrome launches, and the agent starts the conversation.

| Service | Port | URL |
|---------|------|-----|
| Backend WebSocket | **9000** | `ws://localhost:9000` |
| React dev server | **3000** | `http://localhost:3000` |

---

## Environment Variables

Create `backend/.env`:

```dotenv
OPENAI_API_KEY=sk-...your-key-here...
```

If `OPENAI_API_KEY` is absent, `AIIntegration` falls back to hardcoded subject/body strings. The full browser automation flow still completes — no API key required to demo the project.

---

## Key Design Decisions

**WebSocket over HTTP polling**
Screenshot streaming happens at sub-second intervals during browser actions. A persistent WebSocket connection pushes each frame immediately; polling would introduce visible lag and unnecessary complexity.

**`step_callback` pattern**
Every micro-action in `BrowserController` calls `step_callback(text, filename)` which the server wires to `websocket.send`. This decouples browser logic from transport logic cleanly — the controller doesn't know about WebSocket, it just calls a callback.

**Multiple selector fallbacks in `try_click()`**
Gmail updates its DOM selectors without notice. Looping through an ordered list of selectors and catching `PlaywrightTimeout` on each means the agent adapts to UI changes without code changes in most cases.

**2FA polling loop (120s, 3s intervals)**
Google's phone-approval prompt can take anywhere from 5 to 60+ seconds. Polling every 3s rather than a fixed sleep means the agent proceeds the moment the user approves, with no wasted time.

**Graceful AI fallback**
The project is fully demonstrable without spending API credits. Hardcoded subject and body strings let you test and show the browser automation independently of OpenAI availability.

**Password masking in chat**
The agent detects when its last message contained the word "password" and switches the HTML input to `type="password"`. The chat history stores `••••••••` instead of the real value — credentials are never persisted in React state as plain text.

**Anti-bot measures in Chrome launch**
The browser launches with `--disable-blink-features=AutomationControlled` and overrides `navigator.webdriver` via an init script, reducing the chance Gmail flags the session as automated.

---

## Bug Fixes Applied

| # | File | Bug | Impact | Fix |
|---|------|-----|--------|-----|
| 1 | `ai_integration.py` | `openai.ChatCompletion.create` removed in `openai >= 1.0` | Hard crash on every AI call | Migrated to `OpenAI()` client, `client.chat.completions.create`, `.message.content` |
| 2 | `websocket_server.py` | `handle_client(websocket, path)` — `path` param dropped in `websockets >= 14` (installed: 15.0.1) | Hard crash on every connection | Removed unused `path` parameter |
| 3 | `websocket_server.py` | Browser launch outside `try/except` — startup crash silently killed connection | User saw nothing, no feedback | Wrapped startup in try/except; error sent as chat message |
| 4 | `websocket_client.js` | No `onclose` / `onerror` handlers | Connection failures completely invisible to user | Added handlers that inject system messages into the chat |
| 5 | `websocket_client.js` | `sendMessage` silently dropped messages during `CONNECTING` state | First user message lost if sent too quickly | Added `pendingMessages[]` queue flushed on `onopen` |
| 6 | `ChatInterface.jsx` | Password typed and shown as plain text in chat history | Security — credentials visible in UI | Auto-detects password prompt, switches `type="password"`, stores `••••••••` in history |
| 7 | `requirements.txt` | `asyncio` listed (Python stdlib, not a pip package); `websockets` entirely missing | Fresh `pip install` fails silently for websockets | Removed `asyncio`, added `websockets>=10.0`, pinned `openai>=1.0.0` |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `AttributeError: module 'openai' has no attribute 'ChatCompletion'` | Fixed — was caused by openai v1.0 API change |
| `TypeError: handle_client() missing 1 required positional argument` | Fixed — was caused by websockets v14+ dropping the `path` param |
| Gmail asks for 2FA / phone approval | Supported — agent waits up to 120s, polling every 3s |
| Screenshots not appearing in chat | Confirm backend is running on port 9000 and no firewall blocks it |
| `OpenAI` quota / key errors | Check `backend/.env` exists; project works without a key using fallback strings |
| Chrome not launching | Verify Chrome path in `browser_controller.py` line 17 matches your install |
| `Email stuck in Drafts` | Gmail selector may have changed; update selector lists in `compose_email()` |

---

## Future Enhancements

- Support other email providers (Outlook, Yahoo Mail)
- Multi-language conversation support
- Email templates and scheduled sends
- Session persistence across reconnects
- Voice command input
- Docker container for one-command startup
- Support for attachments

---

## Credits

Built by **Vijayshree Pathak**

- [Microsoft Playwright](https://playwright.dev/) — browser automation framework
- [OpenAI](https://openai.com/) — language model API
- [React](https://react.dev/) — frontend framework
- [websockets](https://websockets.readthedocs.io/) — Python async WebSocket server

---

*"Real agents don't call APIs, they move pixels."*

**Star this repo if you found it useful!**
