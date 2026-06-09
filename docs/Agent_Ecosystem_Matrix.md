# Super MCP Lite: Agent Ecosystem & Universal Bootstrapping

To fulfill the vision of a "Universal, Run-Anywhere" Agentic IDE, the system must not pollute the user's host OS. All dependencies, models, and CLI binaries must be hermetically sealed within the project directory.

## 1. Universal Bootstrapping Architecture (Self-Contained)

The upcoming `universal_bootstrap.sh` will perform the following heavy lifting entirely in the background:
1. **Hermetic Python Environment:** Creates an isolated `.venv` inside the project to bypass OS restrictions (like Debian's PEP 668) without needing `sudo`.
2. **Static Binary Injection:** Downloads portable, pre-compiled static binaries (like `ffmpeg`, `ollama`) directly into the `super-mcp-lite/bin/` folder. No system-level apt/brew installs required.
3. **Automated LLM Provisioning:** Automatically spins up the portable Ollama daemon and pulls the baseline required models into a local `./models` cache.
4. **Interactive CLI Auth Flow:** A beautiful terminal UI that loops through the supported Cloud Agents, asking the user for API keys only once, and securely storing them in a local `.env` vault.

---

## 2. Supported Agent CLI Integrations
These are the dedicated terminal-based coding agents that the Master Orchestrator can dynamically invoke to solve complex repositories:

### Open-Source / Local CLIs
*   **Aider (`aider-chat`)**
    *   *Purpose:* Git-native, surgical file editing and massive refactoring.
    *   *Auth:* Supports local Ollama models (No auth needed) or Cloud APIs (Anthropic/OpenAI keys).
*   **OpenHands / OpenDevin**
    *   *Purpose:* Heavy-duty workspace sandbox execution.
    *   *Auth:* Requires Docker (static binary) and an API key for the driving model.
*   **SWE-Agent**
    *   *Purpose:* Princeton's architecture for resolving GitHub Issues completely autonomously.
    *   *Auth:* GitHub PAT and LLM API Key.

### Proprietary / Cloud CLIs
*   **Claude Code (`@anthropic-ai/claude-code`)**
    *   *Purpose:* Anthropic's official CLI for vast codebase understanding and multi-file reasoning.
    *   *Auth:* Anthropic API Key (`ANTHROPIC_API_KEY`).
*   **GitHub Copilot CLI**
    *   *Purpose:* Semantic terminal command generation and git assistance.
    *   *Auth:* GitHub OAuth Device Flow (`gh auth login`).
*   **Superpower CLI (`super-mcp-cli`)**
    *   *Purpose:* Your native system agent.
    *   *Auth:* Pre-authenticated locally.

---

## 3. Supported Machine Learning Models (LLMs)
The Master Orchestrator will seamlessly route tasks to these models based on hardware availability and API keys.

### Local (Hermetic Ollama)
*These run entirely offline on the user's GPU/CPU.*
*   **`qwen2.5-coder:7b`**: The absolute best open-weight model for raw coding, frontend/backend generation.
*   **`deepseek-coder-v2`**: Exceptional at database structuring, Python, and C++.
*   **`mistral-nemo`**: High-context window, perfect for reading massive log files and QA debugging.
*   **`llama-3-instruct`**: General-purpose reasoning and Master Orchestrator routing logic.

### Cloud (Fallback / Heavy Lifting)
*These are used for tasks exceeding local hardware limits.*
*   **`claude-3-5-sonnet`**: The undisputed champion of agentic coding and UI/UX frontend design.
*   **`gpt-4o`**: Extremely fast reasoning and fallback architectural planning.
*   **`gemini-1.5-pro`**: Massive 2-million token context window. Used when the Master Orchestrator needs to read an entire repository at once.

---

### The Setup Flow UX
When a user clones the repository and runs `./scripts/universal_bootstrap.sh`:
1. "Detecting OS... Linux AMD64 identified."
2. "Downloading Portable Binaries [Ollama, FFmpeg, Node.js]..."
3. "Creating Isolated Python Environment..."
4. "Pulling baseline local model: qwen2.5:0.5b..."
5. "Do you want to enable Cloud Agents? (y/n) -> If yes, please paste your Anthropic API Key:"
6. **"Setup Complete. Booting Super MCP Daemon."**
