import os

with open('/home/mobot/super-mcp-lite/server.py', 'r') as f:
    server_py = f.read()

old_ollama_func = """# ─── Ollama Master Orchestrator (Company Hierarchy) ─────────────────────
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

new_ollama_func = """# ─── Ollama Overwatch Round-Table ─────────────────────
def query_ollama_overwatch(prompt, history, previous_results=""):
    system = "You are the Overwatch Manager of a collaborative AI Group Chat. \\n"
    system += "Everyone in the room (you + agents) has read the user's prompt.\\n"
    system += "Your job is to OVERSEE the conversation, declare the plan, and optionally issue directives to the specialized agents to perform actions.\\n"
    system += "Your team:\\n"
    system += "- 'codex': Frontend Engineer (UI, React, CSS)\\n"
    system += "- 'agy': Backend & DevOps Engineer (Python, Node, DBs, Infra)\\n"
    system += "- 'gemini': Product Design & General Chat\\n\\n"
    
    system += "Respond ONLY with a valid JSON object in this exact format:\\n"
    system += "{\\n"
    system += '  "manager_message": "Your conversational reply to the group outlining the plan or giving feedback",\\n'
    system += '  "directives": [\\n'
    system += '    {"agent": "<codex|agy|gemini>", "task": "<specific technical task>"} \\n'
    system += "  ] // Leave empty if no actions are needed\\n"
    system += "}\\n"
    
    context = f"User Prompt Broadcast: {prompt}\\n"
    if previous_results:
        context += f"\\nAgent Execution Results:\\n{previous_results}\\n\\nBased on these results, what is your feedback to the group? Are we done?"
        
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
        print(f"Ollama overwatch error: {e}")
        return None"""

server_py = server_py.replace(old_ollama_func, new_ollama_func)

old_fallback = """    # ── Natural language fallback (OLLAMA COMPANY LOOP) ──
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

new_fallback = """    # ── Group Chat Overwatch (OLLAMA ROUND-TABLE) ──
    responses = []
    previous_results = ""
    
    for iteration in range(2): # 1 initial planning pass + 1 feedback/review pass
        delegation = query_ollama_overwatch(final_prompt, history=[], previous_results=previous_results)
        
        if not delegation:
            # Fallback if Ollama is down
            response = execute_agent("gemini", final_prompt, mode)
            responses.append({"sender": "Gemini", "role": "gemini", "text": response})
            break
            
        # Manager speaks to the room
        manager_msg = delegation.get('manager_message', '')
        if manager_msg:
            responses.append({
                "sender": "Overwatch Manager",
                "role": "gemini",
                "text": manager_msg
            })
            
        directives = delegation.get('directives', [])
        if not directives:
            # If no directives, the manager is satisfied and the room can close for this turn
            break
            
        for directive in directives:
            agent_role = directive.get('agent')
            agent_task = directive.get('task')
            
            if agent_role in ['codex', 'agy', 'gemini']:
                agent_name = agent_role.capitalize()
                
                # Execute the assigned agent
                agent_response = execute_agent(agent_role, agent_task, mode)
                
                # Agent posts their result to the group chat
                responses.append({
                    "sender": agent_name,
                    "role": agent_role,
                    "text": agent_response
                })
                
                # Append to context for the Manager's next review cycle
                previous_results += f"\\n[{agent_name}'s Action]: {agent_response}\\n"
                
    return responses"""

server_py = server_py.replace(old_fallback, new_fallback)

# Patch shell routing as well
old_shell_routing = """        delegation = query_ollama_manager(prompt, history=[], previous_results="")
        if delegation and delegation.get('agent') in ['codex', 'agy', 'gemini']:
            agent_role = delegation['agent']
            agent_name = agent_role.capitalize()
        else:
            agent_name, agent_role = route_to_agent(prompt)"""

new_shell_routing = """        delegation = query_ollama_overwatch(prompt, history=[], previous_results="")
        if delegation and delegation.get('directives'):
            agent_role = delegation['directives'][0].get('agent', 'gemini')
            agent_name = agent_role.capitalize()
        else:
            agent_name, agent_role = route_to_agent(prompt)"""

server_py = server_py.replace(old_shell_routing, new_shell_routing)

with open('/home/mobot/super-mcp-lite/server.py', 'w') as f:
    f.write(server_py)
