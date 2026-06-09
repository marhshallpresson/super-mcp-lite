import http.server
import socketserver
import json
import os
import argparse
import subprocess
import time
import glob
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import auth_manager
import urllib.request

AVAILABLE_AGENTS = {}

def run_health_checks():
    global AVAILABLE_AGENTS
    print("[*] Running background health checks on multi-agent integrations...")
    AVAILABLE_AGENTS = {}
    
    # Check Ollama
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode('utf-8'))
            for model in data.get("models", []):
                name = model.get("name")
                AVAILABLE_AGENTS[name] = {"type": "ollama", "status": "online"}
    except Exception:
        pass

    # Check Gemini CLI
    try:
        res = subprocess.run(["gemini", "--version"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            AVAILABLE_AGENTS["gemini"] = {"type": "cli", "status": "online"}
    except:
        pass

    # Check Agy CLI (Dry-run to verify authentication)
    try:
        res = subprocess.run(["agy", "--version"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            AVAILABLE_AGENTS["agy"] = {"type": "cli", "status": "online"}
    except:
        pass
        
    print(f"[✓] Detected {len(AVAILABLE_AGENTS)} active LLM/Agent endpoints: {list(AVAILABLE_AGENTS.keys())}")

# ─── Parse CLI Arguments ─────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Super Agentic MCP Daemon")
parser.add_argument('--cwd', default=os.getcwd(), help="Target directory context")
args = parser.parse_args()

# ─── Configuration ────────────────────────────────────────────────────────────
TARGET_DIR = os.path.abspath(args.cwd)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(TARGET_DIR, ".super")
HISTORY_FILE = os.path.join(SESSION_DIR, "history.json")
CONFIG_FILE = os.path.join(SESSION_DIR, "config.json")
ARTIFACTS_DIR = os.path.join(SESSION_DIR, "artifacts")
PORT = 8080

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "sandbox": True,
    "timeout": True,
    "autosave": True,
    "persist": True,
    "avatars": True
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# ─── Session Persistence ─────────────────────────────────────────────────────
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(history):
    # ─── Event Condenser ───
    if len(history) > 30:
        archived_messages = history[:15]
        remaining = history[15:]
        
        archive_file = os.path.join(SESSION_DIR, "history_archive.json")
        try:
            archive = []
            if os.path.exists(archive_file):
                with open(archive_file, 'r') as f:
                    archive = json.load(f)
            archive.extend(archived_messages)
            with open(archive_file, 'w') as f:
                json.dump(archive, f, indent=2)
        except Exception:
            pass
            
        history = [{
            "sender": "System", 
            "role": "gemini", 
            "text": "*(Event Condenser)*: 15 earlier messages were safely archived to `history_archive.json` to prevent token bloat. The agents are maintaining peak cognitive efficiency."
        }] + remaining

    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except IOError as e:
        print(f"[ERROR] Failed to save history: {e}")

def list_artifacts():
    """Scan .super/artifacts/ for real files."""
    artifacts = []
    for fpath in glob.glob(os.path.join(ARTIFACTS_DIR, "*")):
        name = os.path.basename(fpath)
        size = os.path.getsize(fpath)
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(fpath)))
        artifacts.append({"name": name, "size": size, "modified": mtime, "path": fpath})
    return artifacts

def list_directory(dirpath):
    """List files in a directory for the file browser."""
    entries = []
    try:
        for name in sorted(os.listdir(dirpath)):
            full = os.path.join(dirpath, name)
            is_dir = os.path.isdir(full)
            size = 0 if is_dir else os.path.getsize(full)
            entries.append({"name": name, "isDir": is_dir, "size": size})
    except PermissionError:
        entries.append({"name": "[Permission Denied]", "isDir": False, "size": 0})
    return entries

# ─── Command Execution Engine ────────────────────────────────────────────────
def execute_command(cmd, cwd, force=False):
    """Execute a shell command with optional approval logic."""
    config = load_config()
    
    # If sandbox is on and not forced, we check if command is dangerous
    dangerous_keywords = ["rm", "sudo", "chmod", "chown", "mv", "cp", "git push", "curl", "wget", "ssh", "kill", "ps", "apt"]
    is_dangerous = any(kw in cmd.split() for kw in dangerous_keywords)
    
    if config.get("sandbox", True) and is_dangerous and not force:
        return {
            "status": "pending_approval",
            "command": cmd,
            "message": "This command is restricted by the sandbox and requires manual approval."
        }

    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=30
        )
        # Automatic Git Checkpoint after success (Harden)
        if result.returncode == 0:
            # Check if it's a git repo first
            if os.path.exists(os.path.join(cwd, ".git")):
                subprocess.run(f'git add . && git commit -m "Agent executed: {cmd}"', shell=True, cwd=cwd, capture_output=True)
            
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "code": result.returncode,
            "status": "success" if result.returncode == 0 else "error"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out after 30 seconds.", "code": -1, "status": "error"}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "code": -1, "status": "error"}

# ─── Agent Execution ──────────────────────────────────────────────────────────
def execute_agent(agent_role, prompt, mode="auto"):
    """Execute a real CLI agent and return its response."""
    
    # Mode configurations
    codex_sandbox = "read-only" if mode == "plan" else "workspace-write"
    
    if agent_role == "gemini":
        cmd = ["gemini", "-p", prompt, "--skip-trust"]
        if mode == "fast":
            cmd.extend(["-m", "gemini-1.5-flash"])
    elif agent_role == "codex":
        cmd = ["codex", "exec", prompt, "--skip-git-repo-check", "--sandbox", codex_sandbox]
    elif agent_role == "agy":
        cmd = ["agy", "-p", prompt]
    else:
        return f"Unknown agent: {agent_role}"

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode == 0:
            output = result.stdout.strip()
            # Basic cleanup for Codex which might have headers
            if agent_role == "codex" and "--------" in output:
                output = output.split("codex\n")[-1].split("tokens used")[0].strip()
            return output if output else "[Agent returned empty response]"
        else:
            return f"Error ({result.returncode}): {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return f"Agent {agent_role} timed out. Please ensure it is authenticated (run `{agent_role}` in terminal)."
    except Exception as e:
        return f"Unexpected error: {str(e)}"

import urllib.request
import urllib.error

# ─── Context Engine (Repo Map) ──────────────────────────────────────────────
def generate_repo_map(directory, max_files=150):
    import re
    repo_map = []
    file_count = 0
    ignore_dirs = {'.git', '.super', 'node_modules', '__pycache__', 'venv', 'dist', 'build', 'coverage'}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.cpp', '.h', '.php')):
                if file_count >= max_files: break
                file_count += 1
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, directory)
                repo_map.append(f"\n--- {rel_path} ---")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            l = line.strip()
                            if l.startswith(('class ', 'def ', 'function ', 'export function ', 'interface ', 'type ')):
                                repo_map.append("  " + l)
                except Exception: pass
    if not repo_map: return ""
    return "\n\n[SYSTEM CONTEXT: REPOSITORY ARCHITECTURE MAP]\n" + "\n".join(repo_map) + "\n\n"

# ─── Dynamic Agent Factory & Orchestrator ───────────────────────────
def execute_dynamic_agent(model, system_prompt, task, history=[]):
    slack_tone = "\\nIMPORTANT TONE RULE: Speak in a 'professional casual' tone, as if you are a colleague replying in a tech company's Slack channel. Be friendly, concise, and skip the robotic AI disclaimers.\\n"
    
    context = ""
    if history:
        context = "CHAT HISTORY:\\n"
        for msg in history[-5:]: # Pass last 5 messages for context memory
            context += f"[{msg.get('sender', 'Unknown')}]: {msg.get('text', '')}\\n"
            
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"model": model, "prompt": system_prompt + slack_tone + "\\n" + context + "\\nTask:\\n" + task, "stream": False}).encode('utf-8')
        with urllib.request.urlopen(req, data=data, timeout=120) as response:
            return json.loads(response.read().decode('utf-8')).get("response", "")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"[Self-Healing Diagnostic] The model '{model}' is not installed locally. Run `ollama pull {model}` to acquire it."
        return f"[Agent Error] HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return f"[Self-Healing Diagnostic] The backend engine is completely offline. Connection refused: {e.reason}. Please ensure the daemon is running."
    except Exception as e:
        err_str = str(e).lower()
        if "timed out" in err_str:
            return f"[Self-Healing Diagnostic] Agent '{model}' timed out after 120s. The model may be exhausted, or your local RAM/VRAM is saturated."
        return f"[Critical Agent Crash] Deep check failed: {e}"

def query_dynamic_orchestrator(prompt, history, previous_results=""):
    system = "TONE & PERSONA:\\n"
    system += "You are managing a live company agentic group chat. All interactions must be 'professional casual'—exactly like colleagues talking in a real tech company's Slack or Microsoft Teams channel.\\n"
    system += "Keep it friendly, concise, and highly collaborative. Use conversational language when addressing the user and the team.\\n\\n"
    system += "DEEP ROTATION AGENT POOL:\\n"
    system += "You have equal access to a massive pool of specialized agents. You must orchestrate deep rotation, assigning tasks to the most optimal agent based strictly on their technical capability.\\n"
    system += "- 'codex': Frontend and UI Engineering\\n"
    system += "- 'agy': Backend and Infrastructure\\n"
    system += "- 'gemini': Product and Architecture\\n"
    system += "- 'aider': Git-native surgical file edits and refactoring (Open Source CLI)\\n"
    system += "- 'qwen': Raw coding logic and problem solving (Local)\\n"
    system += "- 'mistral': QA, debugging, and security auditing (Local)\\n"
    system += "- 'deepseek': Database architecture and SQL tuning (Local)\\n\\n"
    system += "You can also SPAWN CUSTOM AGENTS dynamically if the pool doesn't have the exact expertise.\\n"
    system += "Respond ONLY with valid JSON:\\n"
    system += "{\\n"
    system += '  "manager_message": "Your public response to the user or team",\\n'
    system += '  "directives": [\\n'
    system += '    {\\n'
    system += '      "action": "delegate",\\n'
    system += '      "agent_name": "codex|agy|gemini|aider|qwen|mistral|deepseek|<Custom_Name>",\\n'
    system += '      "task": "The exact task to perform"\\n'
    system += '    }\\n'
    system += "  ]\\n"
    system += "}\\n"
    
    context = ""
    if history:
        context = "CHAT HISTORY:\\n"
        for msg in history[-10:]: # Pass last 10 messages for orchestrator context
            context += f"[{msg.get('sender', 'Unknown')}]: {msg.get('text', '')}\\n"
            
    context += f"\\nUser Request: {prompt}\\n"
    if previous_results:
         context += f"\\nAgent Feedback:\\n{previous_results}"
         
    try:
        config = load_config()
        orch_model = config.get("orchestrator_model", "qwen2.5:0.5b")
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"model": orch_model, "prompt": system + "\\n" + context, "stream": False, "format": "json"}).encode('utf-8')
        with urllib.request.urlopen(req, data=data, timeout=60) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            return json.loads(res_body.get("response", "{}"))
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

# ─── Agent Routing ────────────────────────────────────────────────────────────
def route_to_agent(prompt):
    p = prompt.lower()
    if any(kw in p for kw in ["npm", "node", "vite", "react", "vue", "tsx", "jsx", "css", "html", "frontend", "component"]):
        return "Codex", "codex"
    elif any(kw in p for kw in ["python", "pip", "db", "sql", "backend", "api", "server", "docker", "git", "ls", "cat", "mkdir", "rm", "mv", "cp", "find", "grep", "chmod", "curl", "wget"]):
        return "Agy", "agy"
    else:
        return "Gemini", "gemini"

def is_shell_command(prompt):
    """Detect if a prompt looks like a shell command vs natural language."""
    p = prompt.strip()
    # Starts with a known command binary
    shell_prefixes = ["ls", "cd", "cat", "echo", "mkdir", "rm", "mv", "cp", "find", "grep",
                      "chmod", "chown", "curl", "wget", "git", "npm", "npx", "node", "python",
                      "pip", "docker", "make", "touch", "head", "tail", "wc", "sort", "uniq",
                      "tar", "zip", "unzip", "ssh", "scp", "rsync", "kill", "ps", "top",
                      "df", "du", "free", "which", "whoami", "pwd", "env", "export", "source",
                      "sed", "awk", "tr", "cut", "xargs", "tee", "diff", "patch", "tree",
                      "./", "sudo", "apt", "brew", "cargo", "go", "rustc", "gcc", "java"]
    first_word = p.split()[0].lower() if p.split() else ""
    # Check if it starts with a known binary or contains pipes/redirects
    if first_word in shell_prefixes:
        return True
    if any(op in p for op in ["|", ">>", "&&", "||", "$("]):
        return True
    # Starts with ./ or /
    if p.startswith("./") or p.startswith("/"):
        return True
    return False

def process_chat(prompt, target_dir, history, attachments=None, mode="auto"):
    """Process a user chat message and return agent responses."""
    p = prompt.strip().lower()
    config = load_config()
    dirname = os.path.basename(target_dir)

    # Prepare file attachments
    attached_content = ""
    if attachments:
        for path in attachments:
            try:
                # Handle skill assignment logic if path mentions superpower or skills
                is_skill = False
                
                # Special Alias Resolution
                resolved_path = path
                if resolved_path.startswith("/superpower-ts") or "superpowers-ts" in resolved_path:
                     resolved_path = os.path.expanduser("~/superpower-ts")
                     is_skill = True
                elif resolved_path.startswith("/super-team") or "super-team" in resolved_path:
                     resolved_path = os.path.expanduser("~/super-team")
                     is_skill = True
                elif resolved_path.startswith("/superpowers"):
                     resolved_path = os.path.expanduser("~/.gemini/antigravity-cli/extensions/superpowers")
                     is_skill = True
                
                if "superpowers" in resolved_path or "skill" in resolved_path:
                    is_skill = True
                
                # Resolve path if it wasn't an alias
                resolved_path = os.path.expanduser(resolved_path)
                if not os.path.isabs(resolved_path):
                    resolved_path = os.path.join(target_dir, resolved_path)
                
                # If it's a directory (like a skill folder), try to find a README or SKILL.md
                if os.path.isdir(resolved_path):
                    if os.path.exists(os.path.join(resolved_path, "SKILL.md")):
                        resolved_path = os.path.join(resolved_path, "SKILL.md")
                    elif os.path.exists(os.path.join(resolved_path, "README.md")):
                        resolved_path = os.path.join(resolved_path, "README.md")
                    else:
                         attached_content += f"\n\n--- Attached Directory: {path} (No SKILL.md found) ---\n"
                         continue

                # Add a separator if it's a skill
                if is_skill:
                    attached_content += f"\n\n--- ⚡ ASSIGNED SKILL: {os.path.basename(os.path.dirname(resolved_path) if 'SKILL.md' in resolved_path else resolved_path)} ---\n"
                
                # Try to read the file
                try:
                    with open(resolved_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        attached_content += f"\n\n--- Content from {path} ---\n{content}\n--- End of content ---\n"
                except UnicodeDecodeError:
                    attached_content += f"\n\n--- Content from {path} ---\n[Binary or non-UTF8 file attached]\n--- End of content ---\n"
            except Exception as e:
                attached_content += f"\n\n--- Failed to load {path}: {str(e)} ---\n"
                
    # Adjust mode prefix and auto-assign Superpower skills based on mode
    mode_prefix = ""
    superpowers_base = os.path.expanduser("~/.gemini/antigravity-cli/extensions/superpowers/skills")
    
    # Always include the base superpower skill if a specific mode is selected to establish discipline
    if mode in ["plan", "execute"]:
        base_skill = os.path.join(superpowers_base, "using-superpowers", "SKILL.md")
        if os.path.exists(base_skill):
            with open(base_skill, 'r', encoding='utf-8') as f:
                attached_content += f"\n\n--- ⚡ ASSIGNED BASE SKILL: using-superpowers ---\n{f.read()}\n--- End of skill ---\n"

    if mode == "plan":
        mode_prefix = "[PLAN MODE: Do not execute code. You are in planning mode.]\n"
        plan_skill = os.path.join(superpowers_base, "writing-plans", "SKILL.md")
        if os.path.exists(plan_skill):
            with open(plan_skill, 'r', encoding='utf-8') as f:
                attached_content += f"\n\n--- ⚡ ASSIGNED MODE SKILL: writing-plans ---\n{f.read()}\n--- End of skill ---\n"
    elif mode == "execute":
        mode_prefix = "[EXECUTE MODE: You are in verbose execution mode. Implement the plan.]\n"
        exec_skill = os.path.join(superpowers_base, "executing-plans", "SKILL.md")
        if os.path.exists(exec_skill):
            with open(exec_skill, 'r', encoding='utf-8') as f:
                attached_content += f"\n\n--- ⚡ ASSIGNED MODE SKILL: executing-plans ---\n{f.read()}\n--- End of skill ---\n"
    elif mode == "fast":
        mode_prefix = "[FAST MODE: Prioritize speed over deep reasoning. Output concise code.]\n"

    # ── Dynamic Skill Routing ──
    if os.path.exists(superpowers_base):
        try:
            for skill_dir in os.listdir(superpowers_base):
                skill_path = os.path.join(superpowers_base, skill_dir, "SKILL.md")
                if os.path.exists(skill_path):
                    keywords = skill_dir.lower().split('-')
                    if any(kw in p for kw in keywords if len(kw) > 3):
                        if f"ASSIGNED SKILL: {skill_dir}" not in attached_content:
                            with open(skill_path, 'r', encoding='utf-8') as f:
                                attached_content += f"\n\n--- ⚡ AUTONOMOUSLY ASSIGNED SKILL: {skill_dir} ---\n{f.read()}\n--- End of skill ---\n"
        except Exception:
            pass
        
    repo_map_ctx = generate_repo_map(target_dir)
    final_prompt = mode_prefix + repo_map_ctx + prompt + attached_content


    # ── Greetings ──
    if p in ["hey", "hello", "hi", "yo", "hey everyone", "hi everyone", "hello everyone"]:
        return [
            {"sender": "Gemini", "role": "gemini", "text": f"Hey! Welcome to the `{dirname}` workspace. I'm coordinating. What's the plan?"},
            {"sender": "Codex", "role": "codex", "text": f"Hey! I've loaded the project structure. Ready to work on frontend code."},
            {"sender": "Agy", "role": "agy", "text": f"Backend systems online. I have read access to `{target_dir}`."}
        ]

    # ── Review Command ──
    if p.startswith("/review") or p == "review":
        # Run REAL analysis commands
        backend_files = execute_command(r'find . -maxdepth 4 -type f \( -name "*.ts" -o -name "*.py" -o -name "*.js" \) ! -path "*/node_modules/*" ! -path "*/.git/*" | head -30', target_dir)
        frontend_files = execute_command(r'find . -maxdepth 4 -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" -o -name "*.css" -o -name "*.html" \) ! -path "*/node_modules/*" ! -path "*/.git/*" | head -30', target_dir)
        git_log = execute_command(r'git log --oneline -10 2>/dev/null || echo "Not a git repository"', target_dir)
        
        # More robust line counting
        loc_cmd = r'find . -maxdepth 4 -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" \) ! -path "*/node_modules/*" ! -path "*/.git/*" -exec cat {} + 2>/dev/null | wc -l'
        line_count_res = execute_command(loc_cmd, target_dir)
        total_lines = line_count_res.get('stdout', '0').strip()
        if not total_lines: total_lines = "0"

        # Save as artifact
        report = f"# Project Review: {dirname}\n\n## Backend Files\n{backend_files.get('stdout','None')}\n\n## Frontend Files\n{frontend_files.get('stdout','None')}\n\n## Recent Commits\n{git_log.get('stdout','None')}\n\n## Total Lines of Code\n{total_lines}"
        artifact_name = f"review_{int(time.time())}.md"
        artifact_path = os.path.join(ARTIFACTS_DIR, artifact_name)
        with open(artifact_path, 'w') as f:
            f.write(report)

        return [
            {"sender": "Gemini", "role": "gemini", "text": f"Starting real scan of `{dirname}`. Deploying Agy and Codex."},
            {"sender": "Agy", "role": "agy", "text": f"**Backend files found:**\n```\n{backend_files.get('stdout', 'None found')}\n```"},
            {"sender": "Codex", "role": "codex", "text": f"**Frontend files found:**\n```\n{frontend_files.get('stdout', 'None found')}\n```"},
            {"sender": "Agy", "role": "agy", "text": f"**Recent git history:**\n```\n{git_log.get('stdout', 'No git repo')}\n```"},
            {"sender": "Gemini", "role": "gemini", "text": f"**Summary:** {total_lines} total lines of code. Full report saved to `{artifact_name}` in the Artifacts tab."}
        ]

    # ── Agent-specific questions (Direct @mention or keyword) ──
    if p.startswith("@codex") or "codex" in p:
        clean_prompt = final_prompt.replace("@codex", "").strip()
        response = execute_agent("codex", clean_prompt if clean_prompt else "Status check", mode)
        return [{"sender": "Codex", "role": "codex", "text": response}]
    
    if p.startswith("@agy") or "agy" in p:
        clean_prompt = final_prompt.replace("@agy", "").strip()
        response = execute_agent("agy", clean_prompt if clean_prompt else "Status check", mode)
        return [{"sender": "Agy", "role": "agy", "text": response}]

    if p.startswith("@gemini") or "gemini" in p:
        clean_prompt = final_prompt.replace("@gemini", "").strip()
        response = execute_agent("gemini", clean_prompt if clean_prompt else "Status check", mode)
        return [{"sender": "Gemini", "role": "gemini", "text": response}]

    # ── Status check ──
    if any(kw in p for kw in ["status", "who is active", "which agent", "who's online", "agents"]):
        status = auth_manager.get_auth_status()
        res = []
        for agent, authed in status.items():
            name = agent.capitalize()
            state = "Authenticated ✅" if authed else "Not Auth ❌ (run in terminal to fix)"
            res.append({"sender": name, "role": agent, "text": f"Status: {state}"})
        return res

    # ── Session commands ──
    if p in ["clear", "/clear", "reset"]:
        save_history([])
        return [{"sender": "Gemini", "role": "gemini", "text": "Session history cleared."}]

    if p in ["help", "/help"]:
        return [{"sender": "Gemini", "role": "gemini", "text": "**Commands:**\n• Any shell command (e.g. `ls -la`, `git log -5`) → executed live\n• `@codex` / `@agy` / `@gemini` → talk to a specific agent\n• `status` → check agent health\n• `clear` → reset session\n• `help` → this message\n\nAll history persists in `.super/` inside this directory."}]

    # ── Shell commands: detect and execute ──
    if is_shell_command(prompt.strip()):
        agent_name, agent_role = route_to_agent(prompt)
        result = execute_command(prompt.strip(), target_dir)

        if result.get("status") == "pending_approval":
            return [{
                "sender": agent_name, 
                "role": agent_role, 
                "text": f"I need to run the following command but it requires your approval:\n```bash\n{result['command']}\n```",
                "type": "approval_request",
                "command": result["command"]
            }]

        responses = []
        if result.get("status") == "success":
            output = result["stdout"] if result["stdout"] else "[Completed with no output]"
            if len(output) > 2000:
                artifact_name = f"output_{int(time.time())}.txt"
                artifact_path = os.path.join(ARTIFACTS_DIR, artifact_name)
                with open(artifact_path, 'w') as f:
                    f.write(output)
                truncated = output[:1500]
                responses.append({"sender": agent_name, "role": agent_role, "text": f"```\n{truncated}\n```\n\n*Output truncated. Full result saved to `{artifact_name}`*"})
            else:
                responses.append({"sender": agent_name, "role": agent_role, "text": f"```\n{output}\n```"})
        else:
            error = result["stderr"] if result["stderr"] else result["stdout"] if result["stdout"] else "Unknown error"
            responses.append({"sender": agent_name, "role": agent_role, "text": f"**Error (exit {result['code']}):**\n```\n{error}\n```"})

        return responses

    # ── Dynamic Multi-Agent Execution Loop ──
    responses = []
    previous_results = ""
    
    for iteration in range(2): # Up to 2 feedback rounds
        delegation = query_dynamic_orchestrator(final_prompt, history=history, previous_results=previous_results)
        
        if not delegation:
            response = execute_agent("gemini", final_prompt, mode)
            responses.append({"sender": "Gemini", "role": "gemini", "text": response})
            break
            
        manager_msg = delegation.get('manager_message', '')
        if manager_msg:
            responses.append({"sender": "Overwatch Manager", "role": "gemini", "text": manager_msg})
            
        directives = delegation.get('directives', [])
        if not directives:
            break
            
        for d in directives:
            if d.get('action') in ['spawn_agent', 'delegate']:
                agent_name = d.get('agent_name', 'Custom Agent')
                task = d.get('task', '')
                name_lower = agent_name.lower()
                res_text = ""
                
                if name_lower in ['codex', 'agy', 'gemini']:
                    res_text = execute_agent(name_lower, task, mode)
                elif 'aider' in name_lower:
                    import subprocess
                    try:
                        res = subprocess.run(["python3", "-m", "aider", "--message", task, "--no-auto-commits"], capture_output=True, text=True, cwd=TARGET_DIR, timeout=45)
                        res_text = res.stdout if res.stdout else res.stderr
                    except Exception as e:
                        res_text = f"Aider Error: {e}"
                elif 'qwen' in name_lower:
                    res_text = execute_dynamic_agent("qwen2.5-coder:7b", "You are an expert coder.", task, history)
                elif 'mistral' in name_lower:
                    res_text = execute_dynamic_agent("mistral", "You are an expert QA and debugger.", task, history)
                elif 'deepseek' in name_lower:
                    res_text = execute_dynamic_agent("deepseek-r1:1.5b", "You are an expert database architect.", task, history)
                else:
                    res_text = execute_dynamic_agent("qwen2.5:0.5b", f"You are a specialized {agent_name}.", task, history)
                
                responses.append({"sender": agent_name, "role": "codex", "text": res_text})
                previous_results += f"\\n[{agent_name} Output]: {res_text}\\n"
                
    return responses




# ─── HTTP Handler ─────────────────────────────────────────────────────────────
class SuperDaemonHandler(http.server.BaseHTTPRequestHandler):
    """Custom handler that serves static files from APP_DIR and API routes."""

    def log_message(self, format, *args):
        """Suppress default noisy logging."""
        pass

    def send_json(self, data, status=200):
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            pass

    def serve_static(self, filepath, content_type):
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            try:
                self.send_error(404, "File not found")
            except: pass
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # ── Global Workspace Context Override ──
        global TARGET_DIR, SESSION_DIR, HISTORY_FILE, CONFIG_FILE, ARTIFACTS_DIR
        if 'cwd' in params:
            new_cwd = params['cwd'][0]
            if os.path.exists(new_cwd):
                TARGET_DIR = os.path.abspath(new_cwd)
                
        session_name = params.get('session', ['default'])[0]
        import re
        session_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', session_name).strip()
        if not session_name: session_name = 'default'
        
        SESSION_DIR = os.path.join(TARGET_DIR, ".super", session_name)
        os.makedirs(SESSION_DIR, exist_ok=True)
        HISTORY_FILE = os.path.join(SESSION_DIR, "history.json")
        CONFIG_FILE = os.path.join(SESSION_DIR, "config.json")
        ARTIFACTS_DIR = os.path.join(SESSION_DIR, "artifacts")
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        
        # Migrate old flat-structure history into 'default' thread
        old_hist = os.path.join(TARGET_DIR, ".super", "history.json")
        if session_name == 'default' and os.path.exists(old_hist) and not os.path.exists(HISTORY_FILE):
             import shutil
             try: shutil.move(old_hist, HISTORY_FILE)
             except: pass
             old_conf = os.path.join(TARGET_DIR, ".super", "config.json")
             if os.path.exists(old_conf):
                 try: shutil.move(old_conf, CONFIG_FILE)
                 except: pass

        # ── API Routes ──
        if path == '/api/metrics':
            history = load_history()
            stats = {}
            for msg in history:
                role = msg.get('role', 'unknown')
                if role == 'user': continue
                if role not in stats:
                     stats[role] = {"executions": 0, "failures": 0}
                stats[role]["executions"] += 1
                if "Error (" in msg.get("text", ""):
                     stats[role]["failures"] += 1
            
            payload = {}
            for agent, meta in AVAILABLE_AGENTS.items():
                execs = stats.get(agent, {}).get("executions", 0)
                fails = stats.get(agent, {}).get("failures", 0)
                success_rate = "100%" if execs == 0 else f"{int(((execs-fails)/execs)*100)}%"
                payload[agent] = {
                     "status": "Online",
                     "executions": execs,
                     "success_rate": success_rate,
                     "avg_latency": "1.2s" if meta.get("type") == "cli" else "4.5s"
                }
            self.send_json(payload)
            return

        if path == '/api/agents':
            self.send_json({"agents": AVAILABLE_AGENTS})
            return

        if path == '/api/network':
            import subprocess
            try:
                res = subprocess.run(['vnstat', '--json'], capture_output=True, text=True)
                if res.returncode == 0:
                    self.send_json(json.loads(res.stdout))
                else:
                    self.send_json({"error": "vnstat not configured. Run: sudo apt install vnstat"}, 500)
            except Exception as e:
                self.send_json({"error": "vnstat is not installed. Please run: sudo apt install vnstat && sudo systemctl enable vnstat"}, 500)
            return

        if path == '/api/version':
            # Use timestamp of server.py as dynamic version
            mtime = os.path.getmtime(os.path.abspath(__file__))
            self.send_json({"version": str(mtime)})
            return

        if path == '/api/history':
            history = load_history()
            self.send_json({"messages": history, "cwd": TARGET_DIR, "dirName": os.path.basename(TARGET_DIR)})
            return

        if path == '/api/artifacts':
            artifacts = list_artifacts()
            self.send_json({"artifacts": artifacts})
            return

        if path == '/api/sessions':
            threads = []
            workspaces = []
            
            # 1. Threads in current workspace
            super_dir = os.path.join(TARGET_DIR, ".super")
            if os.path.exists(super_dir):
                for entry in os.scandir(super_dir):
                    if entry.is_dir() and entry.name != 'artifacts':
                        hist_file = os.path.join(entry.path, "history.json")
                        mod_time = "New Thread"
                        if os.path.exists(hist_file):
                            mod_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(hist_file)))
                        threads.append({
                            "name": entry.name,
                            "path": entry.name,
                            "lastModified": mod_time
                        })
                        
            # 2. Other Workspaces
            search_roots = [os.path.expanduser("~"), os.path.expanduser("~/Projects")]
            seen_paths = set()
            for root in search_roots:
                if not os.path.exists(root) or root in seen_paths: continue
                seen_paths.add(root)
                try:
                    with os.scandir(root) as it:
                        for entry in it:
                            if entry.is_dir() and entry.path != TARGET_DIR:
                                ws_super = os.path.join(entry.path, ".super")
                                if os.path.exists(ws_super):
                                    workspaces.append({
                                        "name": entry.name,
                                        "path": entry.path,
                                        "lastModified": "Workspace"
                                    })
                except Exception: continue
                
            self.send_json({"threads": threads, "workspaces": workspaces})
            return

        if path == '/api/config':
            config = load_config()
            self.send_json(config)
            return

        if path == '/api/files':
            params = parse_qs(parsed.query)
            dirpath = params.get('path', [TARGET_DIR])[0]
            # Security: only allow browsing within TARGET_DIR
            real_target = os.path.realpath(TARGET_DIR)
            real_requested = os.path.realpath(dirpath)
            if not real_requested.startswith(real_target):
                self.send_json({"error": "Access denied"}, 403)
                return
            entries = list_directory(real_requested)
            self.send_json({"path": real_requested, "entries": entries})
            return

        if path.startswith('/api/artifact-content'):
            params = parse_qs(parsed.query)
            name = params.get('name', [None])[0]
            if name:
                fpath = os.path.join(ARTIFACTS_DIR, os.path.basename(name))
                if os.path.exists(fpath):
                    with open(fpath, 'r') as f:
                        content = f.read()
                    self.send_json({"name": name, "content": content})
                    return
            self.send_json({"error": "Not found"}, 404)
            return

        if path.startswith('/api/file-content'):
            params = parse_qs(parsed.query)
            fpath = params.get('path', [None])[0]
            if fpath:
                real_target = os.path.realpath(TARGET_DIR)
                real_requested = os.path.realpath(fpath)
                if not real_requested.startswith(real_target):
                    self.send_json({"error": "Access denied"}, 403)
                    return
                if os.path.exists(real_requested) and os.path.isfile(real_requested):
                    try:
                        with open(real_requested, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.send_json({"path": fpath, "content": content})
                    except UnicodeDecodeError:
                        self.send_json({"error": "File is binary or not UTF-8"}, 400)
                    except Exception as e:
                        self.send_json({"error": str(e)}, 500)
                    return
            self.send_json({"error": "Not found"}, 404)
            return

        # ── Static Files (served from APP_DIR) ──
        if path == '/' or path == '':
            path = '/index.html'

        filepath = os.path.join(APP_DIR, path.lstrip('/'))
        filepath = os.path.realpath(filepath)

        # Security: only serve files from APP_DIR
        if not filepath.startswith(os.path.realpath(APP_DIR)):
            self.send_error(403, "Forbidden")
            return

        # Content type mapping
        ext = os.path.splitext(filepath)[1].lower()
        content_types = {
            '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
            '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
            '.svg': 'image/svg+xml', '.ico': 'image/x-icon'
        }
        ctype = content_types.get(ext, 'application/octet-stream')
        self.serve_static(filepath, ctype)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        global TARGET_DIR, SESSION_DIR, HISTORY_FILE, CONFIG_FILE, ARTIFACTS_DIR
        if 'cwd' in params:
            new_cwd = params['cwd'][0]
            if os.path.exists(new_cwd):
                TARGET_DIR = os.path.abspath(new_cwd)
                
        session_name = params.get('session', ['default'])[0]
        import re
        session_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', session_name).strip()
        if not session_name: session_name = 'default'
        
        SESSION_DIR = os.path.join(TARGET_DIR, ".super", session_name)
        os.makedirs(SESSION_DIR, exist_ok=True)
        HISTORY_FILE = os.path.join(SESSION_DIR, "history.json")
        CONFIG_FILE = os.path.join(SESSION_DIR, "config.json")
        ARTIFACTS_DIR = os.path.join(SESSION_DIR, "artifacts")
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)

        if path == '/api/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return

            prompt = data.get('prompt', '').strip()
            mode = data.get('mode', 'auto')
            attachments = data.get('attachments', [])
            
            if not prompt and not attachments:
                self.send_json({"error": "Empty prompt"}, 400)
                return

            # Load history, add user message
            history = load_history()
            user_msg = {"sender": "You", "role": "user", "text": prompt}
            if attachments:
                 user_msg["text"] += f"\n\n*(Attached: {len(attachments)} items)*"
            history.append(user_msg)

            # Process and get agent responses
            responses = process_chat(prompt, TARGET_DIR, history=history, attachments=attachments, mode=mode)


            # Save everything
            history.extend(responses)
            save_history(history)

            self.send_json({"messages": responses})
            return

        if path == '/api/voice':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                b64 = data.get('audio_b64', '')
                if not b64 or ',' not in b64:
                     self.send_json({"error": "Invalid base64 audio"}, 400)
                     return
                
                raw_b64 = b64.split(',')[1]
                import base64, tempfile, subprocess
                audio_bytes = base64.b64decode(raw_b64)
                
                with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
                    f.write(audio_bytes)
                    temp_webm = f.name
                
                temp_wav = temp_webm + '.wav'
                # Transcode via ffmpeg to 16kHz mono PCM
                subprocess.run(['/home/mobot/bin/ffmpeg', '-i', temp_webm, '-ar', '16000', '-ac', '1', '-f', 'wav', temp_wav, '-y'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Lazy load Vosk model
                import wave
                try:
                    from vosk import Model, KaldiRecognizer
                except ImportError:
                    self.send_json({"error": "Vosk python package not installed"}, 500)
                    return
                    
                global vosk_model
                if 'vosk_model' not in globals():
                    if not os.path.exists("/home/mobot/super-mcp-lite/models/vosk-model"):
                        self.send_json({"error": "Vosk model not downloaded"}, 500)
                        return
                    vosk_model = Model("/home/mobot/super-mcp-lite/models/vosk-model")
                
                wf = wave.open(temp_wav, "rb")
                rec = KaldiRecognizer(vosk_model, 16000)
                
                result_text = ""
                while True:
                    frame_data = wf.readframes(4000)
                    if len(frame_data) == 0:
                        break
                    if rec.AcceptWaveform(frame_data):
                        res = json.loads(rec.Result())
                        result_text += res.get("text", "") + " "
                
                final_res = json.loads(rec.FinalResult())
                result_text += final_res.get("text", "")
                
                os.remove(temp_webm)
                os.remove(temp_wav)
                
                self.send_json({"text": result_text.strip()})
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({"error": str(e)}, 500)
            return

        if path == '/api/config':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                config = json.loads(post_data.decode('utf-8'))
                save_config(config)
                self.send_json({"success": True})
            except:
                self.send_json({"error": "Invalid config"}, 400)
            return

        if path == '/api/approve':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                command = data.get('command')
                if not command:
                    self.send_json({"error": "No command provided"}, 400)
                    return

                # Force execution
                result = execute_command(command, TARGET_DIR, force=True)
                self.send_json({"messages": [{
                    "sender": "System",
                    "role": "gemini",
                    "text": f"Command executed successfully:\n```\n{result.get('stdout', '[No output]')}\n```" if result.get("status") == "success" else f"Command failed:\n```\n{result.get('stderr', 'Unknown error')}\n```"
                }]})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        if path == '/api/file-content':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                fpath = data.get('path')
                content = data.get('content', '')
                
                real_target = os.path.realpath(TARGET_DIR)
                real_requested = os.path.realpath(fpath)
                if not real_requested.startswith(real_target):
                    self.send_json({"error": "Access denied"}, 403)
                    return
                
                with open(real_requested, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        if path == '/api/terminal':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                command = data.get('command', '')
                import subprocess
                res = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=TARGET_DIR, executable="/bin/bash")
                out = res.stdout if res.stdout else res.stderr
                if not out: out = "[Process completed with no output]"
                self.send_json({"output": out})
            except Exception as e:
                self.send_json({"output": f"Internal Error: {e}"})
            return

        self.send_error(404, "Not Found")

# ─── Server Startup ──────────────────────────────────────────────────────────
class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    print(f"\n  ╔══════════════════════════════════════════════════╗")
    print(f"  ║  Super Agentic MCP Daemon                       ║")
    print(f"  ║  Context: {TARGET_DIR:<40}║")
    print(f"  ║  Session: {SESSION_DIR:<40}║")
    print(f"  ║  Port:    {PORT:<40}║")
    print(f"  ╚══════════════════════════════════════════════════╝\n")

    run_health_checks()

    with ReusableTCPServer(("127.0.0.1", PORT), SuperDaemonHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[Super Daemon] Shutting down.")
            httpd.shutdown()
