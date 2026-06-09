import os
import re

with open('/home/mobot/super-mcp-lite/server.py', 'r') as f:
    server_py = f.read()

# Add urllib import if missing
if 'import urllib.request' not in server_py:
    server_py = server_py.replace('import json', 'import json\nimport urllib.request\nimport urllib.error')

# Inject Ollama Orchestrator Function
ollama_func = """# ─── Ollama Master Orchestrator ─────────────────────────────────────────────
def query_ollama_orchestrator(prompt, history):
    system = "You are the Master Orchestrator for an AI team. Your job is to read the user's prompt and delegate it. \\n"
    system += "Available agents:\\n"
    system += "- 'codex': Frontend (HTML, CSS, React, UI)\\n"
    system += "- 'agy': Backend (Python, Node, DBs, Shell commands, Infrastructure)\\n"
    system += "- 'gemini': General chat, architecture design, product decisions\\n"
    system += 'Respond ONLY with a valid JSON object in this exact format: {"agent": "<agent_name>", "task": "<detailed instruction for the agent>"}\\n'
    
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({
            "model": "llama3",
            "prompt": system + "\\nUser Request: " + prompt,
            "stream": False,
            "format": "json"
        }).encode('utf-8')
        
        with urllib.request.urlopen(req, data=data, timeout=30) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            raw_resp = res_body.get("response", "{}")
            return json.loads(raw_resp)
    except Exception as e:
        print(f"Ollama orchestrator error: {e}")
        return None

# ─── Agent Routing """

server_py = server_py.replace('# ─── Agent Routing ', ollama_func)

# Patch the routing inside process_chat
old_routing = """    # ── Shell commands: detect and execute ──
    if is_shell_command(prompt.strip()):
        agent_name, agent_role = route_to_agent(prompt)"""

new_routing = """    # ── Shell commands: detect and execute ──
    if is_shell_command(prompt.strip()):
        # Use Ollama to intelligently route the shell command if possible
        delegation = query_ollama_orchestrator(prompt, history=[])
        if delegation and delegation.get('agent') in ['codex', 'agy', 'gemini']:
            agent_role = delegation['agent']
            agent_name = agent_role.capitalize()
        else:
            agent_name, agent_role = route_to_agent(prompt)"""

server_py = server_py.replace(old_routing, new_routing)

# Patch the Natural Language Fallback to use Ollama fully
old_fallback = """    # ── Natural language fallback ──
    # Default to Gemini for general questions
    response = execute_agent("gemini", final_prompt, mode)
    return [{"sender": "Gemini", "role": "gemini", "text": response}]"""

new_fallback = """    # ── Natural language fallback (OLLAMA ORCHESTRATED) ──
    # Let Ollama decide who handles this natural language request
    delegation = query_ollama_orchestrator(final_prompt, history=[])
    
    if delegation and delegation.get('agent') in ['codex', 'agy', 'gemini']:
        agent_role = delegation['agent']
        agent_name = agent_role.capitalize()
        agent_task = delegation.get('task', final_prompt)
        
        # Announce the delegation
        responses = []
        responses.append({
            "sender": "Orchestrator",
            "role": "gemini",
            "text": f"*(Ollama analysis complete. Delegating task to **{agent_name}**...)*"
        })
        
        # Execute the assigned agent
        agent_response = execute_agent(agent_role, agent_task, mode)
        responses.append({"sender": agent_name, "role": agent_role, "text": agent_response})
        return responses
    else:
        # Fallback if Ollama is down or busy
        response = execute_agent("gemini", final_prompt, mode)
        return [{"sender": "Gemini", "role": "gemini", "text": response}]"""

server_py = server_py.replace(old_fallback, new_fallback)

with open('/home/mobot/super-mcp-lite/server.py', 'w') as f:
    f.write(server_py)
