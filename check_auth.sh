#!/bin/bash

echo "=== Super CLI Authentication Audit ==="

# 1. Check Gemini
echo -n "[1/3] Checking Gemini CLI... "
if timeout 10s gemini -p "ping" --skip-trust > /dev/null 2>&1; then
    echo "✅ Authenticated"
else
    echo "❌ NOT AUTHENTICATED or ERROR"
    echo "    Run: gemini (complete login in browser)"
fi

# 2. Check Codex
echo -n "[2/3] Checking Codex CLI... "
if timeout 10s codex exec "ping" --skip-git-repo-check > /dev/null 2>&1; then
    echo "✅ Authenticated"
else
    echo "❌ NOT AUTHENTICATED or ERROR"
    echo "    Run: codex login"
fi

# 3. Check Agy
echo -n "[3/3] Checking Agy CLI... "
# agy -p seems to be quiet if successful but can fail
if timeout 10s agy -p "ping" > /dev/null 2>&1; then
    echo "✅ Authenticated"
else
    # Try a simple subcommand
    if agy models > /dev/null 2>&1; then
        echo "✅ Authenticated (Models listed)"
    else
        echo "❌ NOT AUTHENTICATED or ERROR"
        echo "    Run: agy (complete login in browser)"
    fi
fi

echo "========================================"
