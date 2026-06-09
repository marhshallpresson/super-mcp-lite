#!/bin/bash
# Super MCP Agentic App Launcher
# Industry Standard Desktop Wrapper

APP_DIR="/home/mobot/super-mcp-lite"
PORT=8080

echo "[Super MCP] Booting local agentic daemon..."

# Kill any existing server on this port just in case
pkill -f "python3 server.py" || true
pkill -f "python3 -m http.server" || true

cd $APP_DIR
python3 server.py > /dev/null 2>&1 &
sleep 2

echo "[Super MCP] Launching Desktop UI..."
# Try Chrome --app mode first for the desktop feel
if command -v google-chrome > /dev/null 2>&1; then
    google-chrome --app="http://localhost:$PORT" --window-size=1200,800 --class=SuperMCP &
elif command -v xdg-open > /dev/null 2>&1; then
    xdg-open "http://localhost:$PORT" &
else
    # Python fallback
    python3 -m webbrowser "http://localhost:$PORT" &
fi
