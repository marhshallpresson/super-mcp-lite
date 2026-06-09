import os

with open('/home/mobot/super-mcp-lite/server.py', 'r') as f:
    code = f.read()

# 1. Replace the orchestrator system prompt to treat all agents equally for Deep Rotation
old_system_prompt = """    system += "You have the ability to SPAWN CUSTOM AGENTS on the fly.\\n"
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
    system += "}\\n\""""

new_system_prompt = """    system += "DEEP ROTATION AGENT POOL:\\n"
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
    system += "}\\n\""""

code = code.replace(old_system_prompt, new_system_prompt)

# 2. Update the dynamic agent execution loop to handle the equalized pool including Aider
old_loop = """        for d in directives:
            if d.get('action') == 'spawn_agent':
                agent_name = d.get('agent_name', 'Custom Agent')
                model = d.get('model', 'llama3')
                sys_prompt = d.get('system_prompt', '')
                task = d.get('task', '')
                
                # Execute the dynamically generated agent
                res_text = execute_dynamic_agent(model, sys_prompt, task)"""

new_loop = """        for d in directives:
            if d.get('action') in ['spawn_agent', 'delegate']:
                agent_name = d.get('agent_name', 'Custom Agent')
                task = d.get('task', '')
                
                # Route to the appropriate tool based on equal rotation
                name_lower = agent_name.lower()
                res_text = ""
                
                if name_lower in ['codex', 'agy', 'gemini']:
                    res_text = execute_agent(name_lower, task, mode)
                elif 'aider' in name_lower:
                    # Aider execution wrapper
                    import subprocess
                    try:
                        res = subprocess.run(["python3", "-m", "aider", "--message", task, "--no-auto-commits"], capture_output=True, text=True, cwd=TARGET_DIR, timeout=45)
                        res_text = res.stdout if res.stdout else res.stderr
                    except Exception as e:
                        res_text = f"Aider Error: {e}"
                elif 'qwen' in name_lower:
                    res_text = execute_dynamic_agent("qwen2.5-coder:7b", "You are an expert coder.", task)
                elif 'mistral' in name_lower:
                    res_text = execute_dynamic_agent("mistral", "You are an expert QA and debugger.", task)
                elif 'deepseek' in name_lower:
                    res_text = execute_dynamic_agent("deepseek-r1:1.5b", "You are an expert database architect.", task)
                else:
                    # Dynamic Spawn Fallback
                    res_text = execute_dynamic_agent("llama3", f"You are a specialized {agent_name}.", task)"""

if old_loop in code:
    code = code.replace(old_loop, new_loop)

with open('/home/mobot/super-mcp-lite/server.py', 'w') as f:
    f.write(code)
