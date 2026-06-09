import os

with open('/home/mobot/super-mcp-lite/server.py', 'r') as f:
    server_py = f.read()

# 1. Update execute_agent to handle local agents vs cloud agents
old_execute = """def execute_agent(agent_role, prompt, mode="auto"):
    # Mock CLI execution for now.
    import subprocess
    cmd = []
    
    if agent_role == "gemini":
        cmd = ["gemini", "-p", prompt, "--skip-trust"]
    elif agent_role == "codex":
        # Assumes codex is a wrapper around the agent execution
        codex_sandbox = "/home/mobot/super-mcp-lite/.super"
        cmd = ["codex", "exec", prompt, "--skip-git-repo-check", "--sandbox", codex_sandbox]
    elif agent_role == "agy":
        cmd = ["agy", "-p", prompt]
    else:
        return f"Unknown agent: {agent_role}"
        
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=TARGET_DIR, timeout=30)
        return res.stdout if res.stdout else res.stderr
    except subprocess.TimeoutExpired:
        return f"Agent {agent_role} timed out."
    except Exception as e:
        return f"Unexpected error: {e}" """

new_execute = """def query_local_ollama_model(model_name, prompt):
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"model": model_name, "prompt": prompt, "stream": False}).encode('utf-8')
        with urllib.request.urlopen(req, data=data, timeout=120) as response:
            return json.loads(response.read().decode('utf-8')).get("response", "")
    except Exception as e:
        return f"[Ollama Error on {model_name}]: {e}"

def log_agent_usage(agent_role, is_cloud):
    metrics_file = os.path.join(SESSION_DIR, "agent_metrics.json")
    try:
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
        else:
            metrics = {"cloud_tasks": 0, "local_tasks": 0, "agent_breakdown": {}}
            
        if is_cloud: metrics["cloud_tasks"] += 1
        else: metrics["local_tasks"] += 1
        
        metrics["agent_breakdown"][agent_role] = metrics["agent_breakdown"].get(agent_role, 0) + 1
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
    except Exception:
        pass

def execute_agent(agent_role, prompt, mode="auto"):
    import subprocess
    cmd = []
    
    # ── Cloud Agents ──
    if agent_role == "cloud_gemini":
        log_agent_usage("cloud_gemini", True)
        cmd = ["gemini", "-p", prompt, "--skip-trust"]
    elif agent_role == "cloud_codex":
        log_agent_usage("cloud_codex", True)
        codex_sandbox = "/home/mobot/super-mcp-lite/.super"
        cmd = ["codex", "exec", prompt, "--skip-git-repo-check", "--sandbox", codex_sandbox]
    elif agent_role == "cloud_agy":
        log_agent_usage("cloud_agy", True)
        cmd = ["agy", "-p", prompt]
        
    # ── Local Ollama Agents ──
    elif agent_role == "local_frontend":
        log_agent_usage("local_frontend", False)
        return query_local_ollama_model("qwen2.5-coder:7b", "You are a Frontend Developer. " + prompt)
    elif agent_role == "local_backend":
        log_agent_usage("local_backend", False)
        return query_local_ollama_model("qwen2.5-coder:7b", "You are a Backend Developer. " + prompt)
    elif agent_role == "qa_tester":
        log_agent_usage("qa_tester", False)
        return query_local_ollama_model("mistral", "You are a QA Tester and Debugger. " + prompt)
    elif agent_role == "db_admin":
        log_agent_usage("db_admin", False)
        return query_local_ollama_model("deepseek-r1:1.5b", "You are a Database Admin. " + prompt)
    elif agent_role == "security_auditor":
        log_agent_usage("security_auditor", False)
        return query_local_ollama_model("mistral", "You are a Security Auditor. " + prompt)
    elif agent_role == "local_gemini":
        log_agent_usage("local_gemini", False)
        return query_local_ollama_model("llama3", "You are a Product Designer. " + prompt)
    else:
        return f"Unknown agent: {agent_role}"
        
    # Execute cloud commands
    if cmd:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, cwd=TARGET_DIR, timeout=30)
            output = res.stdout if res.stdout else res.stderr
            # Auto-Failover if Cloud Agent timed out or failed heavily
            if "Unexpected error" in output or "timed out" in output.lower():
                log_agent_usage("cloud_failover", True)
                return "CLOUD FAILURE: Falling back to local Llama3...\\n" + query_local_ollama_model("llama3", prompt)
            return output
        except subprocess.TimeoutExpired:
            return "CLOUD TIMEOUT: Falling back to local Llama3...\\n" + query_local_ollama_model("llama3", prompt)
        except Exception as e:
            return f"Unexpected error: {e}"
    return "Agent executed silently." """

server_py = server_py.replace(old_execute, new_execute)

# 2. Update the Manager Prompt to use the new 10 Agents
old_manager_prompt = """    system += "- 'codex': Frontend Engineer (UI, React, CSS)\\n"
    system += "- 'agy': Backend & DevOps Engineer (Python, Node, DBs, Infra)\\n"
    system += "- 'gemini': Product Design & General Chat\\n\\n"
    
    system += "Respond ONLY with a valid JSON object in this exact format:\\n"
    system += "{\\n"
    system += '  "manager_message": "Your conversational reply to the group outlining the plan or giving feedback",\\n'
    system += '  "directives": [\\n'
    system += '    {"agent": "<codex|agy|gemini>", "task": "<specific technical task>"} \\n'"""

new_manager_prompt = """    system += "TEAM ROSTER (10 Agents):\\n"
    system += "[Cloud Agents - Expensive, use sparingly for highly complex tasks]\\n"
    system += "- 'cloud_codex': Complex UI generation\\n"
    system += "- 'cloud_agy': Advanced system architectures\\n"
    system += "- 'cloud_gemini': Deep product strategy\\n"
    system += "[Local Agents - 100% FREE, prioritize these for most work!]\\n"
    system += "- 'local_frontend': (Qwen Coder) Simple UI edits, CSS fixes\\n"
    system += "- 'local_backend': (Qwen Coder) Simple API scaffolding\\n"
    system += "- 'qa_tester': (Mistral) Unit testing and bug fixes\\n"
    system += "- 'db_admin': (DeepSeek) SQL queries and schema review\\n"
    system += "- 'security_auditor': (Mistral) Code vulnerability scanning\\n"
    system += "- 'local_gemini': (Llama3) General chat\\n\\n"
    
    system += "Respond ONLY with a valid JSON object in this exact format:\\n"
    system += "{\\n"
    system += '  "manager_message": "Your conversational reply to the group outlining the plan or giving feedback",\\n'
    system += '  "directives": [\\n'
    system += '    {"agent": "<agent_id_from_roster>", "task": "<specific technical task>"} \\n'"""

server_py = server_py.replace(old_manager_prompt, new_manager_prompt)

# 3. Update the fallback logic parser
old_parser = """            if agent_role in ['codex', 'agy', 'gemini']:"""
new_parser = """            if agent_role in ['cloud_codex', 'cloud_agy', 'cloud_gemini', 'local_frontend', 'local_backend', 'qa_tester', 'db_admin', 'security_auditor', 'local_gemini']:"""

server_py = server_py.replace(old_parser, new_parser)

with open('/home/mobot/super-mcp-lite/server.py', 'w') as f:
    f.write(server_py)
