Working Godot MCP



HOW TO USE

1. CLONE THE REPO
2. MAKE A GODOT PROJECT
3. ADD THE ADDONS FILE TO THE GODOT PROJECT, WHICH ALLOWS YOU TO ENABLE THE MCP PLUGIN
4. CREATE A VENV WITH PYTHON3 AND INSTALL ALL REQUIREMENTS
5. RUN SERVER.PY
6. ADD THE FOLLOWING TO YOUR CLAUDE_DESKTOP_CONFIG.JSON

{
  "mcpServers": {
    "godotMCP": {
      "command": "/Path/Togodot-mcp/python/venv/bin/python3",
      "args": [
        "/Path/To/server.py"
      ]
    }
  }
}
