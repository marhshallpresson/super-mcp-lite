import os

# 1. Patch server.py
with open('/home/mobot/super-mcp-lite/server.py', 'r') as f:
    server_py = f.read()

# Replace do_GET global block
old_global = """        # ── Global Workspace Context Override ──
        global TARGET_DIR, SESSION_DIR, HISTORY_FILE, CONFIG_FILE, ARTIFACTS_DIR
        if 'cwd' in params:
            new_cwd = params['cwd'][0]
            if os.path.exists(new_cwd):
                TARGET_DIR = os.path.abspath(new_cwd)
                SESSION_DIR = os.path.join(TARGET_DIR, ".super")
                HISTORY_FILE = os.path.join(SESSION_DIR, "history.json")
                CONFIG_FILE = os.path.join(SESSION_DIR, "config.json")
                ARTIFACTS_DIR = os.path.join(SESSION_DIR, "artifacts")
                os.makedirs(SESSION_DIR, exist_ok=True)
                os.makedirs(ARTIFACTS_DIR, exist_ok=True)"""

new_global = """        # ── Global Workspace Context Override ──
        global TARGET_DIR, SESSION_DIR, HISTORY_FILE, CONFIG_FILE, ARTIFACTS_DIR
        if 'cwd' in params:
            new_cwd = params['cwd'][0]
            if os.path.exists(new_cwd):
                TARGET_DIR = os.path.abspath(new_cwd)
                SESSION_DIR = os.path.join(TARGET_DIR, ".super")
        
        session_id = params.get('session', ['history'])[0]
        HISTORY_FILE = os.path.join(SESSION_DIR, f"{session_id}.json")
        CONFIG_FILE = os.path.join(SESSION_DIR, "config.json")
        ARTIFACTS_DIR = os.path.join(SESSION_DIR, "artifacts")
        os.makedirs(SESSION_DIR, exist_ok=True)
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)"""

server_py = server_py.replace(old_global, new_global)

# Replace /api/sessions
old_sessions = """        if path == '/api/sessions':
            sessions = []
            # Optimize: only scan the home directory and ~/Projects to avoid hanging
            search_roots = [os.path.expanduser("~"), os.path.expanduser("~/Projects")]
            seen_paths = set()
            
            for root in search_roots:
                if not os.path.exists(root) or root in seen_paths: continue
                seen_paths.add(root)
                try:
                    with os.scandir(root) as it:
                        for entry in it:
                            if entry.is_dir():
                                super_dir = os.path.join(entry.path, ".super")
                                hist_file = os.path.join(super_dir, "history.json")
                                if os.path.exists(hist_file):
                                    sessions.append({
                                        "name": entry.name,
                                        "path": entry.path,
                                        "lastModified": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(hist_file)))
                                    })
                except Exception: continue
                
            self.send_json({"sessions": sessions})
            return"""

new_sessions = """        if path == '/api/sessions':
            sessions = []
            if os.path.exists(SESSION_DIR):
                for f in os.listdir(SESSION_DIR):
                    if f.endswith('.json') and f != 'config.json':
                        sess_name = f.replace('.json', '')
                        hist_file = os.path.join(SESSION_DIR, f)
                        sessions.append({
                            "name": sess_name,
                            "path": sess_name,
                            "lastModified": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(hist_file)))
                        })
            # Sort by last modified descending
            sessions.sort(key=lambda x: x['lastModified'], reverse=True)
            self.send_json({"sessions": sessions})
            return"""

server_py = server_py.replace(old_sessions, new_sessions)

# Add /api/terminal to do_POST
terminal_api = """        if self.path == '/api/terminal':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            res = execute_command(data.get('command', ''), TARGET_DIR, force=True)
            out = res.get('stdout', '')
            if res.get('stderr'): out += '\\n' + res.get('stderr')
            self.send_json({"output": out.strip()})
            return

        if self.path == '/api/approve':"""

server_py = server_py.replace("        if self.path == '/api/approve':", terminal_api)

with open('/home/mobot/super-mcp-lite/server.py', 'w') as f:
    f.write(server_py)

# 2. Patch index.html
with open('/home/mobot/super-mcp-lite/index.html', 'r') as f:
    index_html = f.read()

# Nav item Terminal
nav_files = """    <div class="nav-item" data-view="files">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
        Files
    </div>"""

nav_terminal = """    <div class="nav-item" data-view="files">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
        Files
    </div>
    <div class="nav-item" data-view="terminal">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 9l3 3-3 3m5 0h3M4 6h16v12H4z"/></svg>
        Terminal
    </div>"""

index_html = index_html.replace(nav_files, nav_terminal)

# Terminal view
view_files = """    <!-- ── Files View ── -->
    <div class="view" id="view-files">"""

view_terminal = """    <!-- ── Terminal View ── -->
    <div class="view" id="view-terminal" style="display:flex; flex-direction:column; height:100%;">
        <div class="view-header">
            <h2>Terminal</h2>
            <p>Direct shell access to the workspace</p>
        </div>
        <div id="terminal-output" style="flex:1; background:#000; color:#0f0; padding:12px; font-family:'JetBrains Mono', monospace; font-size:12px; overflow-y:auto; white-space:pre-wrap;"></div>
        <div style="display:flex; border-top:1px solid #333; background:#000;">
            <span style="color:#0f0; padding:8px; font-family:'JetBrains Mono', monospace;">$</span>
            <input type="text" id="terminal-input" style="flex:1; background:transparent; border:none; color:#0f0; outline:none; font-family:'JetBrains Mono', monospace; padding:8px 0;" autocomplete="off" />
        </div>
    </div>

    <!-- ── Files View ── -->
    <div class="view" id="view-files">"""

index_html = index_html.replace(view_files, view_terminal)

# Modal changes
old_modal = """<h3 style="margin:0 0 10px 0; color:var(--text-primary); font-size:16px;">Create New Workspace Session</h3>
        <p style="color:var(--text-muted); font-size:12px; margin-bottom:16px;">Enter the absolute path to the directory you want to open. A new `.super` environment will be initialized there.</p>
        <input type="text" id="new-session-path" placeholder="/home/mobot/my-new-project" """

new_modal = """<h3 style="margin:0 0 10px 0; color:var(--text-primary); font-size:16px;">Create New Chat Session</h3>
        <p style="color:var(--text-muted); font-size:12px; margin-bottom:16px;">Enter a name for the new session thread in this workspace.</p>
        <input type="text" id="new-session-path" placeholder="Feature implementation..." """

index_html = index_html.replace(old_modal, new_modal)

# Session URL mapping
old_href = """onclick="window.location.href='?cwd=${encodeURIComponent(s.path)}'"""
new_href = """onclick="const cp = new URLSearchParams(window.location.search).get('cwd'); window.location.href='?session='+encodeURIComponent(s.path)+(cp?'&cwd='+cp:'')\""""

index_html = index_html.replace(old_href, new_href)

# Btn create session logic
old_btn = """$('#btn-create-session').addEventListener('click', () => {
    const val = $('#new-session-path').value.trim();
    if (val) window.location.href = '?cwd=' + encodeURIComponent(val);
});"""

new_btn = """$('#btn-create-session').addEventListener('click', () => {
    const val = $('#new-session-path').value.trim();
    if (val) {
        const cp = new URLSearchParams(window.location.search).get('cwd');
        window.location.href = '?session=' + encodeURIComponent(val) + (cp ? '&cwd='+cp : '');
    }
});

// Terminal logic
$('#terminal-input').addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        const cmd = e.target.value;
        if (!cmd.trim()) return;
        e.target.value = '';
        $('#terminal-output').textContent += `\\n$ ${cmd}\\n`;
        try {
            const res = await fetch('/api/terminal', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: cmd})
            });
            const data = await res.json();
            $('#terminal-output').textContent += data.output + '\\n';
            $('#terminal-output').scrollTop = $('#terminal-output').scrollHeight;
        } catch (err) {
            $('#terminal-output').textContent += `Error: ${err}\\n`;
        }
    }
});"""

index_html = index_html.replace(old_btn, new_btn)

with open('/home/mobot/super-mcp-lite/index.html', 'w') as f:
    f.write(index_html)
