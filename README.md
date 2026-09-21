# KITOFLUX.AI

> **FLOW. ADAPT. EXECUTE.**  
> Real-time, invisible AI copilot for high-stakes job interviews, technical screens, and customer support escalations.

---

## Technical Manifesto & Architectural Specification

For the complete, authoritative, multi-page systems engineering blueprint, see:
* **[MANIFESTO.md](./MANIFESTO.md)**: The 15-chapter confidential systems architecture document covering the Conversational Execution Specification (CES), DAG execution graph, state machines, stealth mechanics, driver model, and persistence engines.

---

## Key Capabilities

1. **Undetectable Screen Overlay (`WDA_EXCLUDEFROMCAPTURE`):**
   * Uses native Windows Desktop Window Manager affinity flags to exclude the assistive HUD from Zoom, Microsoft Teams, Google Meet, OBS, and Discord screen sharing.
   * Visible only to your eyes; completely transparent to recording and screen-share pipelines.

2. **Real-Time Acoustic Transcription & Zero-Latency Reasoning:**
   * Ingests audio via built-in Chromium Web Speech API (free, zero setup) or local Faster-Whisper.
   * Sub-second time-to-first-token (TTFT) reasoning powered by Groq (Llama-3.1-70B/8B) or OpenAI (GPT-4o-mini).

3. **Local In-Memory RAG (Resume & Knowledge Grounding):**
   * Automatically grounds AI answers in your personal resume, previous project histories, and target job descriptions using sub-30ms hybrid vector/lexical retrieval.

4. **Biological Cadence Autotyper:**
   * Simulates human keystrokes with natural Gaussian jitter, digraph speeds, micro-pauses, and self-correcting typos (`Ctrl+Shift+Space`).
   * Emergency break-glass panic hide shortcut (`Ctrl+Shift+X` or double `Escape`).

---

## How to Download and Run on Your Desktop

### Option A: Clone with Git (Recommended)
Open your terminal (PowerShell, Command Prompt, or Bash) on your desktop and run:

```bash
git clone https://github.com/Alekieh/kitoflux.ai.git -b arena/01a0c2e9-kitoflux-ai
cd kitoflux.ai
```

### Option B: Download as ZIP
1. Visit the repository branch on GitHub:  
   `https://github.com/Alekieh/kitoflux.ai/tree/arena/01a0c2e9-kitoflux-ai`
2. Click the green **Code** button and select **Download ZIP**.
3. Extract the ZIP archive onto your Desktop.

---

## 3-Step Setup & Launch

### Prerequisites
* **Python 3.10+** (ensure "Add Python to PATH" is checked during installation)
* **Node.js 18+** (LTS version from [nodejs.org](https://nodejs.org))
* **Windows 10/11** (for native `WDA_EXCLUDEFROMCAPTURE` stealth overlay) or macOS/Linux (for development mode)

### Step 1: Run the App
* **On Windows:**  
  Double-click **`start.bat`**.  
  *(This script automatically creates a Python virtual environment, installs dependencies, launches the Python kernel, and starts the Electron HUD).*
* **On macOS / Linux:**  
  Run:
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

### Step 2: Configure Keys and Context
1. In the floating HUD, click the **Config** button.
2. Enter your **Groq API Key** (free at [console.groq.com](https://console.groq.com)) or **OpenAI API Key**.
3. Paste your **Resume** or **Key Project Notes** into the knowledge box.
4. Click **Save & Initialize**.

### Step 3: Run During an Interview
1. **Audio Capture:** Click **Mic: ON** in the top bar. As the interviewer speaks, the live words will stream into **Channel 1 (Transcript)**.
2. **AI Strategy:** When a question or problem is detected, **Channel 2 (Strategic Reasoning)** instantly generates concise bullet points, architecture concepts, and code outlines.
3. **Autotyping Code or Text:** If asked to write an answer or code snippet in a live coding interview (e.g., CoderPad, HackerRank, Google Docs):
   * Focus the code editor window.
   * Press **`Ctrl + Shift + Space`**.
   * Kitoflux types out the response using humanized cadence with micro-delays and natural typing speed.
4. **Panic Killswitch:** Press **`Ctrl + Shift + X`** (or click **Hide**) at any point to instantly make the overlay vanish.

---

## Verifying Stealth Invisibility Before Your Interview

To verify that the HUD is 100% invisible to others:
1. Open **OBS Studio**, **Zoom**, or **Microsoft Teams**.
2. Start a test meeting or screen-sharing preview of your primary monitor.
3. Observe that your desktop and browser windows are shared normally, but the **KITOFLUX HUD is completely invisible** on the preview/recording stream.

---

## Architecture Overview

```
                 +-----------------------------------+
                 |    Electron Transparent HUD       |
                 | (Win32 WDA_EXCLUDEFROMCAPTURE)    |
                 +-----------------+-----------------+
                                   | WebSocket IPC (ws://127.0.0.1:8765)
                                   v
                 +-----------------------------------+
                 |    Kitoflux Asynchronous Kernel   |
                 |      (Python 3.11 + asyncio)      |
                 +--------+-----------------+--------+
                          |                 |
            +-------------+                 +-------------+
            v                                             v
  +-------------------+                         +-------------------+
  |  Conversational   |                         | Hardware Drivers  |
  |  Agents (CES)     |                         | * Audio Capture   |
  |  * Listener       |                         | * Web Speech STT  |
  |  * Strategist     |                         | * Groq / OpenAI   |
  |  * Executor       |                         | * Win32 Input     |
  +-------------------+                         +-------------------+
```

---

## License & Security
Proprietary & Confidential. All execution models, stealth hooks, and autotyping formulations are confidential property of Kitoflux.ai.
