import subprocess
import os

def check_gemini():
    try:
        # We use a very simple prompt and skip trust to avoid hanging
        result = subprocess.run(
            ["gemini", "-p", "ping", "--skip-trust"],
            capture_output=True, text=True, timeout=60
        )
        print(f"DEBUG Gemini: {result.stdout}")
        return result.returncode == 0 and "pong" in result.stdout.lower()
    except Exception as e:
        print(f"DEBUG Gemini Error: {e}")
        return False

def check_codex():
    try:
        result = subprocess.run(
            ["codex", "exec", "ping", "--skip-git-repo-check"],
            capture_output=True, text=True, timeout=60
        )
        print(f"DEBUG Codex: {result.stdout}")
        return result.returncode == 0 and "pong" in result.stdout.lower()
    except Exception as e:
        print(f"DEBUG Codex Error: {e}")
        return False

def check_agy():
    try:
        # agy is a bit tricky, let's just check if it can list models
        result = subprocess.run(
            ["agy", "models"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0 and len(result.stdout) > 0
    except:
        return False

def get_auth_status():
    return {
        "gemini": check_gemini(),
        "codex": check_codex(),
        "agy": check_agy()
    }

if __name__ == "__main__":
    print(get_auth_status())
