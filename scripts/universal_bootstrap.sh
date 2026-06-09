#!/usr/bin/env bash
set -e

echo "====================================================="
echo "🚀 Super MCP Lite: Universal Bootstrapper"
echo "====================================================="
echo "This script hermetically installs all dependencies"
echo "without touching your host OS system packages."
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$PROJECT_ROOT/bin"
VENV_DIR="$PROJECT_ROOT/.venv"
MODELS_DIR="$PROJECT_ROOT/models"

mkdir -p "$BIN_DIR" "$MODELS_DIR"

# 1. OS Detection
OS="$(uname -s)"
ARCH="$(uname -m)"
echo "[*] Detected OS: $OS ($ARCH)"

# 2. Hermetic Python Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Creating isolated Python Virtual Environment..."
    python3 -m venv "$VENV_DIR"
fi
echo "[*] Activating Virtual Environment..."
source "$VENV_DIR/bin/activate"

# 3. Installing Dependencies Hermetically
echo "[*] Installing native Python dependencies..."
pip install --upgrade pip > /dev/null
pip install vosk piper-tts sounddevice numpy > /dev/null
pip install requests flask > /dev/null
# Add CLI integrations (Aider)
pip install aider-chat > /dev/null

# 4. Downloading Portable Ollama (if not present)
if [ ! -f "$BIN_DIR/ollama" ]; then
    echo "[*] Downloading Portable Ollama static binary..."
    if [ "$OS" = "Linux" ]; then
        curl -sL https://ollama.com/download/ollama-linux-amd64.tgz -o "$BIN_DIR/ollama.tgz"
        tar -xzf "$BIN_DIR/ollama.tgz" -C "$BIN_DIR" bin/ollama --strip-components=1
        rm "$BIN_DIR/ollama.tgz"
        chmod +x "$BIN_DIR/ollama"
    elif [ "$OS" = "Darwin" ]; then
        echo "Please download Ollama for Mac directly from ollama.com"
    fi
fi

# 5. Interactive CLI Auth Flow
echo ""
echo "====================================================="
echo "🔑 Interactive Agent Authentication"
echo "====================================================="
ENV_FILE="$PROJECT_ROOT/.env"
touch "$ENV_FILE"

if ! grep -q "ANTHROPIC_API_KEY" "$ENV_FILE"; then
    read -p "Enter Anthropic API Key for Claude Code / Aider (or press enter to skip): " anthropic_key
    if [ -n "$anthropic_key" ]; then
        echo "ANTHROPIC_API_KEY=$anthropic_key" >> "$ENV_FILE"
        echo "[✓] Saved Anthropic Key."
    fi
fi

if ! grep -q "GITHUB_TOKEN" "$ENV_FILE"; then
    read -p "Enter GitHub PAT for SWE-Agent (or press enter to skip): " gh_token
    if [ -n "$gh_token" ]; then
        echo "GITHUB_TOKEN=$gh_token" >> "$ENV_FILE"
        echo "[✓] Saved GitHub Token."
    fi
fi

echo ""
echo "[✓] Bootstrapping Complete!"
echo "Run: source .venv/bin/activate && ./bin/ollama serve & python3 server.py"
echo "====================================================="
