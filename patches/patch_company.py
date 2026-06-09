import os

with open('/home/mobot/super-mcp-lite/server.py', 'r') as f:
    server_py = f.read()

# Replace the old ollama func and natural language fallback
import re

# We will just replace the entire query_ollama_orchestrator function
old_ollama_func = """# ─── Ollama Master Orchestrator ─────────────────────────────────────────────
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
        return None"""

new_ollama_func = """# ─── Ollama Master Orchestrator (Company Hierarchy) ─────────────────────
def query_ollama_manager(prompt, history, previous_results=""):
    system = "You are a Senior Engineering Manager overseeing a tech company. \\n"
    system += "Your team:\\n"
    system += "- 'codex': Frontend Engineer (UI, React, CSS)\\n"
    system += "- 'agy': Backend & DevOps Engineer (Python, Node, Infrastructure)\\n"
    system += "- 'gemini': Product Manager & General chat\\n\\n"
    
    system += "The user has made a request. You must decide whether to ASSIGN a task to an agent, or REPLY to the user because the work is done.\\n"
    system += "If you need an agent to do work, output ONLY JSON: {\\"action\\": \\"assign\\", \\"agent\\": \\"<codex|agy|gemini>\\", \\"task\\": \\"<detailed technical instruction>\\"}\\n"
    system += "If the agents have finished the work or you just need to chat with the user, output ONLY JSON: {\\"action\\": \\"reply\\", \\"message\\": \\"<your final response to the user>\\"}\\n"
    
    context = f"User Request: {prompt}\\n"
    if previous_results:
        context += f"\\nPrevious Agent Results:\\n{previous_results}\\n\\nBased on these results, what is your next step?"
        
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({
            "model": "llama3",
            "prompt": system + "\\n" + context,
            "stream": False,
            "format": "json"
        }).encode('utf-8')
        
        with urllib.request.urlopen(req, data=data, timeout=60) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            raw_resp = res_body.get("response", "{}")
            return json.loads(raw_resp)
    except Exception as e:
        print(f"Ollama orchestrator error: {e}")
        return None"""

server_py = server_py.replace(old_ollama_func, new_ollama_func)

# Replace the fallback routing logic to implement the loop
old_fallback = """    # ── Natural language fallback (OLLAMA ORCHESTRATED) ──
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

new_fallback = """    # ── Natural language fallback (OLLAMA COMPANY LOOP) ──
    responses = []
    previous_results = ""
    
    for iteration in range(3): # Max 3 back-and-forth iterations to prevent infinite loops
        delegation = query_ollama_manager(final_prompt, history=[], previous_results=previous_results)
        
        if not delegation:
            # Fallback if Ollama is down or busy
            response = execute_agent("gemini", final_prompt, mode)
            responses.append({"sender": "Gemini", "role": "gemini", "text": response})
            break
            
        action = delegation.get('action')
        
        if action == "reply":
            msg = delegation.get('message', 'Task completed.')
            responses.append({
                "sender": "Senior Manager (Ollama)",
                "role": "gemini",
                "text": f"**Report to User:**\\n{msg}"
            })
            break
            
        elif action == "assign" and delegation.get('agent') in ['codex', 'agy', 'gemini']:
            agent_role = delegation['agent']
            agent_name = agent_role.capitalize()
            agent_task = delegation.get('task', '')
            
            # Announce the delegation
            responses.append({
                "sender": "Senior Manager (Ollama)",
                "role": "gemini",
                "text": f"*(Assigning task to **{agent_name}**...)*\\n> {agent_task}"
            })
            
            # Execute the assigned agent
            agent_response = execute_agent(agent_role, agent_task, mode)
            responses.append({"sender": agent_name, "role": agent_role, "text": agent_response})
            
            # Add to previous results so the manager can review it next iteration
            previous_results += f"\\n--- {agent_name} replied ---\\n{agent_response}\\n"
        else:
            break
            
    return responses"""

server_py = server_py.replace(old_fallback, new_fallback)

# Fix shell command routing that still called query_ollama_orchestrator
old_shell_routing = """        delegation = query_ollama_orchestrator(prompt, history=[])
        if delegation and delegation.get('agent') in ['codex', 'agy', 'gemini']:"""

new_shell_routing = """        delegation = query_ollama_manager(prompt, history=[], previous_results="")
        if delegation and delegation.get('agent') in ['codex', 'agy', 'gemini']:"""

server_py = server_py.replace(old_shell_routing, new_shell_routing)

with open('/home/mobot/super-mcp-lite/server.py', 'w') as f:
    f.write(server_py)
