#!/usr/bin/env bash
set -e

echo "====================================================="
echo "🤖 Super MCP Lite: Global Agent Installer & Updater"
echo "====================================================="
echo "This script installs and auto-updates all supported"
echo "AI coding CLIs across pip, npm, and binary managers."

# 1. Update Python Agents (pip)
echo "[*] Upgrading Python-based Agents..."
pip3 install --user --upgrade --break-system-packages aider-chat || true
pip3 install --user --upgrade --break-system-packages swe-agent || true

# 2. Update Node.js Agents (npm)
echo "[*] Upgrading Node.js-based Agents..."
if command -v npm &> /dev/null; then
    npm install -g @anthropic-ai/claude-code || true
    npm install -g @githubnext/github-copilot-cli || true
else
    echo "[!] npm not found. Skipping Claude Code and Copilot."
fi

# 3. Pull Latest Ollama Models
echo "[*] Upgrading Local Ollama Models..."
if command -v ollama &> /dev/null || [ -f "$HOME/.local/bin/ollama" ]; then
    OLLAMA_CMD="ollama"
    [ -f "$HOME/.local/bin/ollama" ] && OLLAMA_CMD="$HOME/.local/bin/ollama"
    
    $OLLAMA_CMD pull qwen2.5-coder:7b || true
    $OLLAMA_CMD pull deepseek-coder-v2 || true
    $OLLAMA_CMD pull mistral-nemo || true
    $OLLAMA_CMD pull llama3 || true
else
    echo "[!] Ollama daemon not found. Skipping local model pulls."
fi

echo "====================================================="
echo "[✓] All Agents Successfully Installed & Upgraded!"
echo "====================================================="
