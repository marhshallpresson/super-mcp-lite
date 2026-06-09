# Super MCP Lite 🚀

<div align="center">
  <img src="https://img.shields.io/badge/Status-Active-success.svg" alt="Status">
  <img src="https://img.shields.io/badge/Platform-Universal-blue.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</div>

**Super MCP Lite** is a state-of-the-art, fully autonomous, and local-first Agentic IDE designed to orchestrate massive Multi-Agent code generation pipelines securely inside your local machine.

Instead of binding you to a cloud provider's web IDE, Super MCP Lite runs natively on Linux, macOS, and Windows WSL. It intercepts your local codebase, spins up a dynamic Master Orchestrator, and delegates complex architectural tasks to a swarm of local (Ollama) and cloud (Claude/GPT) machine learning agents.

---

## ✨ Core Features

### 🛡️ 1. Secure & Hermetic execution
No more polluting your host machine. The **Universal Bootstrapper** builds a strictly sandboxed Python Virtual Environment, pulls portable static binaries (`ffmpeg`, `ollama`), and runs everything safely inside the `.super` folder without touching your `apt` or `brew` system packages.

### 🎙️ 2. Native Offline Speech-To-Text (Phase 1)
Talk directly to your IDE completely offline. We stripped out Google's Cloud Speech Recognition and implemented a native WebM pipeline. The frontend beams encrypted audio blobs to the backend, which transcodes them via a static FFmpeg binary into a local `Vosk` Machine Learning model for instant, zero-latency transcription.

### 🧠 3. Multi-Agent Orchestration 
Our Master Orchestrator operates as a dispatcher. You provide a prompt, and the Master thinks, delegates, and routes sub-tasks to the best available LLM or CLI agent (e.g., Aider, SWE-Agent, Claude Code) based on context limits and task complexity.

### 💻 4. Interactive "Approve & Run" Markdown
Code execution is entirely under your control. When an Agent wants to run a destructive terminal command or modify a massive file array, the frontend renders a beautiful interactive `[ Approve & Run ]` button alongside the Markdown code block. The system securely proxies the execution upon your explicit click.

---

## ⚡ Installation & Setup

We designed the Universal OS Bootstrapper to install the entire ecosystem in one click.

```bash
# 1. Clone the repository
git clone https://github.com/marhshallpresson/super-mcp-lite.git
cd super-mcp-lite

# 2. Run the Universal Bootstrapper
./scripts/universal_bootstrap.sh
```

### What the bootstrapper does:
* Auto-detects your OS architecture.
* Bypasses OS packaging locks (like Debian PEP 668) with an isolated `.venv`.
* Downloads the portable static Ollama engine and pulls `qwen2.5-coder`.
* Initiates an interactive CLI to securely vault your API keys.
* Installs a **Global CLI (`super`)** into your `~/.local/bin/` so you can launch it anywhere.
* Generates a **native Desktop App shortcut** for your Application Menu!

---

## 🏗️ Architecture Matrix

Super MCP Lite natively supports swapping the underlying neural engines dynamically:

| Agent / CLI | Purpose | Connectivity |
| :--- | :--- | :--- |
| **Aider** | Surgical git-native file refactoring | Local / Cloud |
| **SWE-Agent** | GitHub issue and PR resolution | Cloud |
| **Claude Code** | Multi-file reasoning & architectural design | Cloud |
| **OpenHands** | Deep sandboxed execution | Cloud |

| Models | Speciality |
| :--- | :--- |
| **Qwen 2.5 Coder** | Raw programming (Local Offline) |
| **DeepSeek Coder** | Python & Database structuring |
| **Claude 3.5 Sonnet**| Absolute best for Frontend & UX Design |

---

## 🔒 Security Posture

We take developer security extremely seriously. 
*   **Patched RCE:** The backend orchestration server is strictly bound to `127.0.0.1` (localhost), closing the massive `0.0.0.0` RCE vulnerabilities found in early Devika/OpenDevin clones.
*   **Sandboxed Dependencies:** Local static binaries prevent path-hijacking.

---

## 🤝 Contributing
Contributions are extremely welcome! If you want to integrate a new Agent CLI or tweak the React frontend, just open a Pull Request.

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.
