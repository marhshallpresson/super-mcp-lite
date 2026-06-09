import os

with open('/home/mobot/super-mcp-lite/server.py', 'r') as f:
    code = f.read()

# 1. Add urllib if missing
if 'import urllib.request' not in code:
    code = code.replace('import json', 'import json\nimport urllib.request\nimport urllib.error')

# 2. Inject the powerful Dynamic Orchestrator function
dynamic_func = """
# ─── Dynamic Agent Factory & Orchestrator ───────────────────────────
def query_dynamic_orchestrator(prompt, history, previous_results=""):
    system = "You are the Master Orchestrator. The user has made a request.\\n"
    system += "You have the ability to SPAWN CUSTOM AGENTS on the fly.\\n"
    system += "If the task needs a specific expert (e.g., a Vue.js master, a Cybersecurity auditor), you can dynamically spin one off.\\n"
    system += "Respond ONLY with valid JSON:\\n"
    system += "{\\n"
    system += '  "manager_message": "Your public response to the user or team",\\n'
    system += '  "directives": [\\n'
    system += '    {\\n'
    system += '      "action": "spawn_agent",\\n'
    system += '      "agent_name": "Name of the expert",\\n'
    system += '      "model": "llama3 or qwen2.5-coder:7b or mistral",\\n'
    system += '      "system_prompt": "You are a senior expert in...",\\n'
    system += '      "task": "The exact task to perform"\\n'
    system += '    }\\n'
    system += "  ]\\n"
    system += "}\\n"
    
    context = f"User Request: {prompt}\\n"
    if previous_results:
         context += f"\\nAgent Feedback:\\n{previous_results}"
         
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"model": "llama3", "prompt": system + "\\n" + context, "stream": False, "format": "json"}).encode('utf-8')
        with urllib.request.urlopen(req, data=data, timeout=60) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            return json.loads(res_body.get("response", "{}"))
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

def execute_dynamic_agent(model, system_prompt, task):
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"model": model, "prompt": system_prompt + "\\nTask:\\n" + task, "stream": False}).encode('utf-8')
        with urllib.request.urlopen(req, data=data, timeout=120) as response:
            return json.loads(response.read().decode('utf-8')).get("response", "")
    except Exception as e:
        return f"[Dynamic Agent Error]: {e}"

# ─── Agent Routing """

code = code.replace('# ─── Agent Routing ', dynamic_func)

# 3. Replace the fallback block (lines 385-388)
fallback_target = """    # ── Natural language fallback ──
    # Default to Gemini for general questions
    response = execute_agent("gemini", final_prompt, mode)
    return [{"sender": "Gemini", "role": "gemini", "text": response}]"""

dynamic_loop = """    # ── Dynamic Multi-Agent Execution Loop ──
    responses = []
    previous_results = ""
    
    for iteration in range(2): # Up to 2 feedback rounds
        delegation = query_dynamic_orchestrator(final_prompt, history=[], previous_results=previous_results)
        
        if not delegation:
            # Fallback if Ollama is down
            response = execute_agent("gemini", final_prompt, mode)
            responses.append({"sender": "Gemini", "role": "gemini", "text": response})
            break
            
        manager_msg = delegation.get('manager_message', '')
        if manager_msg:
            responses.append({"sender": "Overwatch Manager", "role": "gemini", "text": manager_msg})
            
        directives = delegation.get('directives', [])
        if not directives:
            break # Manager is satisfied
            
        for d in directives:
            if d.get('action') == 'spawn_agent':
                agent_name = d.get('agent_name', 'Custom Agent')
                model = d.get('model', 'llama3')
                sys_prompt = d.get('system_prompt', '')
                task = d.get('task', '')
                
                # Execute the dynamically generated agent
                res_text = execute_dynamic_agent(model, sys_prompt, task)
                
                # Append to chat
                responses.append({"sender": agent_name, "role": "codex", "text": res_text})
                
                # Feed result back into loop
                previous_results += f"\\n[{agent_name} Output]: {res_text}\\n"
                
    return responses"""

if fallback_target in code:
    code = code.replace(fallback_target, dynamic_loop)
else:
    print("FAILED TO FIND FALLBACK TARGET")

with open('/home/mobot/super-mcp-lite/server.py', 'w') as f:
    f.write(code)
