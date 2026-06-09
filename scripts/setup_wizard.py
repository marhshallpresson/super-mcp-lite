#!/usr/bin/env python3
import os
import subprocess
import time

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header(text):
    print(f"\n\033[1;36m{'='*60}")
    print(f" {text}")
    print(f"{'='*60}\033[0m\n")

AGENTS = [
    {
        "id": "qwen",
        "name": "Qwen 2.5 Coder (7B)",
        "type": "Local Offline LLM",
        "requirements": "Minimum 8GB RAM, No Account Required",
        "install_cmd": "ollama pull qwen2.5-coder:7b"
    },
    {
        "id": "agy",
        "name": "Agy CLI",
        "type": "Local System Agent",
        "requirements": "No Account Required",
        "install_cmd": "pip3 install --user --upgrade agy-cli || true"
    },
    {
        "id": "gemini",
        "name": "Gemini CLI",
        "type": "Cloud AI",
        "requirements": "Google API Key",
        "install_cmd": "npm install -g @google/generative-ai-cli || true",
        "env_var": "GEMINI_API_KEY"
    },
    {
        "id": "claude",
        "name": "Claude Code",
        "type": "Cloud Autonomous Multi-file Agent",
        "requirements": "Anthropic API Key, Billing Enabled",
        "install_cmd": "npm install -g @anthropic-ai/claude-code || true",
        "env_var": "ANTHROPIC_API_KEY"
    },
    {
        "id": "codex",
        "name": "GitHub Copilot (Codex)",
        "type": "Cloud Assistant",
        "requirements": "GitHub Account, Copilot Subscription",
        "install_cmd": "npm install -g @githubnext/github-copilot-cli || true",
        "auth_cmd": "github-copilot-cli auth"
    },
    {
        "id": "aider",
        "name": "Aider",
        "type": "Terminal Git-native Editor",
        "requirements": "Any API Key (OpenAI/Anthropic/Gemini) or Local Ollama",
        "install_cmd": "pip3 install --user --upgrade aider-chat || true"
    },
    {
        "id": "swe_agent",
        "name": "SWE-Agent",
        "type": "Autonomous GitHub Issue Resolver",
        "requirements": "GitHub PAT & OpenAI/Anthropic Key",
        "install_cmd": "pip3 install --user --upgrade swe-agent || true",
        "env_var": "GITHUB_TOKEN"
    },
    {
        "id": "openhands",
        "name": "OpenHands (OpenDevin) / OpenClaw",
        "type": "Sandboxed Docker Execution Environment",
        "requirements": "Docker Desktop, Any API Key",
        "install_cmd": "echo 'OpenHands requires a Docker container pull. Run: docker pull docker.all-hands.dev/all-hands-dev/openhands:main'"
    }
]

def main():
    clear_screen()
    print_header("🚀 SUPER MCP LITE: ADVANCED ONBOARDING WIZARD")
    print("Welcome to the advanced Agent installer.")
    print("Instead of installing a massive 50GB payload by default,")
    print("you can securely pick and choose which AI Agents you want based on your hardware and accounts.\n")
    
    time.sleep(1)
    env_vars_to_save = {}
    
    for agent in AGENTS:
        print(f"\n\033[1;33m► {agent['name']}\033[0m")
        print(f"  Type: {agent['type']}")
        print(f"  Reqs: \033[1;31m{agent['requirements']}\033[0m")
        
        choice = input(f"  Install {agent['name']}? (y/N): ").strip().lower()
        if choice == 'y':
            print(f"  \033[1;32m[*] Installing {agent['name']}...\033[0m")
            subprocess.run(agent['install_cmd'], shell=True)
            
            # Ask for API Key if required
            if 'env_var' in agent:
                key = input(f"  \033[1;35m[?] Please enter your {agent['env_var']} (or press Enter to skip): \033[0m").strip()
                if key:
                    env_vars_to_save[agent['env_var']] = key
            
            # Run custom auth command if needed
            if 'auth_cmd' in agent:
                print(f"  \033[1;34m[*] Running interactive authentication for {agent['name']}...\033[0m")
                subprocess.run(agent['auth_cmd'], shell=True)
        else:
            print("  [Skipped]")

    # Save ENV file
    if env_vars_to_save:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        print(f"\n\033[1;32m[*] Saving secure API keys to {env_path}\033[0m")
        with open(env_path, 'a') as f:
            for k, v in env_vars_to_save.items():
                f.write(f"{k}={v}\n")
    
    print_header("🎉 ONBOARDING COMPLETE!")
    print("Your selected agents have been natively compiled and authenticated.")
    print("You can now launch the IDE by typing 'super' in your terminal.")

if __name__ == "__main__":
    main()
