import os

with open('/home/mobot/super-mcp-lite/server.py', 'r') as f:
    code = f.read()

# 1. Update Orchestrator Tone
old_pool = """    system += "DEEP ROTATION AGENT POOL:\\n"
    system += "You have equal access to a massive pool of specialized agents. You must orchestrate deep rotation, assigning tasks to the most optimal agent based strictly on their technical capability.\\n"
    system += "- 'codex': Frontend and UI Engineering\\n\""""

new_pool = """    system += "TONE & PERSONA:\\n"
    system += "You are managing a live company agentic group chat. All interactions must be 'professional casual'—exactly like colleagues talking in a real tech company's Slack or Microsoft Teams channel.\\n"
    system += "Keep it friendly, concise, and highly collaborative. Use conversational language when addressing the user and the team.\\n\\n"
    
    system += "DEEP ROTATION AGENT POOL:\\n"
    system += "You have equal access to a massive pool of specialized agents. You must orchestrate deep rotation, assigning tasks to the most optimal agent based strictly on their technical capability.\\n"
    system += "- 'codex': Frontend and UI Engineering\\n\""""

code = code.replace(old_pool, new_pool)

# 2. Inject Tone into Dynamic Agents
old_exec_dynamic = """def execute_dynamic_agent(model, system_prompt, task):
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"model": model, "prompt": system_prompt + "\\nTask:\\n" + task, "stream": False}).encode('utf-8')"""

new_exec_dynamic = """def execute_dynamic_agent(model, system_prompt, task):
    slack_tone = "\\nIMPORTANT TONE RULE: Speak in a 'professional casual' tone, as if you are a colleague replying in a tech company's Slack channel. Be friendly, concise, and skip the robotic AI disclaimers.\\n"
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"model": model, "prompt": system_prompt + slack_tone + "Task:\\n" + task, "stream": False}).encode('utf-8')"""

code = code.replace(old_exec_dynamic, new_exec_dynamic)

with open('/home/mobot/super-mcp-lite/server.py', 'w') as f:
    f.write(code)
