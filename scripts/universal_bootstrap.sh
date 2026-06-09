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
echo "====================================================="
echo "🖥️  Installing Global CLI & Desktop App"
echo "====================================================="

# Create global CLI 'super' in ~/.local/bin
mkdir -p "$HOME/.local/bin"
CLI_PATH="$HOME/.local/bin/super"
cat << 'EOF' > "$CLI_PATH"
#!/usr/bin/env bash
PROJECT_ROOT="__ROOT__"
source "$PROJECT_ROOT/.venv/bin/activate"
export PATH="$PROJECT_ROOT/bin:$PATH"
cd "$PROJECT_ROOT"
nohup python3 server.py > daemon.log 2>&1 &
echo "[*] Super MCP Daemon started on port 8080."
xdg-open "http://localhost:8080" 2>/dev/null || open "http://localhost:8080" 2>/dev/null
EOF
sed -i.bak "s|__ROOT__|$PROJECT_ROOT|g" "$CLI_PATH"
rm -f "${CLI_PATH}.bak"
chmod +x "$CLI_PATH"
echo "[✓] Global CLI installed! You can now type 'super' in any terminal."

# Desktop App Shortcut
if [ "$OS" = "Linux" ]; then
    DESKTOP_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"
    DESKTOP_FILE="$DESKTOP_DIR/super-mcp-lite.desktop"
    cat << EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Name=Super MCP Lite
Comment=Universal Agentic IDE
Exec=$CLI_PATH
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Development;
EOF
    chmod +x "$DESKTOP_FILE"
    echo "[✓] Linux Desktop App created in applications menu."
elif [ "$OS" = "Darwin" ]; then
    APP_DIR="$HOME/Applications/Super MCP.app"
    mkdir -p "$APP_DIR/Contents/MacOS"
    cat << EOF > "$APP_DIR/Contents/MacOS/launcher"
#!/usr/bin/env bash
$CLI_PATH
EOF
    chmod +x "$APP_DIR/Contents/MacOS/launcher"
    echo "[✓] macOS App created in ~/Applications."
fi

echo ""
echo "[✓] Bootstrapping Complete!"
echo "Run 'super' in your terminal, or click 'Super MCP Lite' in your apps menu."
echo "====================================================="
