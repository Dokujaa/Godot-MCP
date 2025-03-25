# 🎮 Godot MCP 

A plugin that allows external processes to communicate with the Godot engine in a modular and programmable way.

🎥 [Watch the video on Twitter](https://twitter.com/yourusername/status/1234567890123456789) (FOLLOW ME PLS PLS)

---


https://github.com/user-attachments/assets/28137c5b-251b-4d83-a2c0-0741bb5e9096


## 🚀 Getting Started

Follow these steps to get the plugin up and running:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/godot-mcp.git
cd Godot-MCP
```


### 2. Create a Godot Project
Open Godot Engine

Create a new project or open an existing one

### 3. Add the Addon to Your Project
Copy the addons/ folder from this repo into your Godot project directory

In the Godot editor, go to Project -> Project Settings -> Plugins and enable the MCP Plugin


### 4. Set-up your virtual environment

```bash
cd python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Run the MCP Server

```bash
python3 server.py
or
python server.py
```


## ⚙️ Claude Desktop Integration
To integrate with Claude Desktop, add the following to your claude_desktop_config.json:

```json
{
  "mcpServers": {
    "godotMCP": {
      "command": "/Path/To/godot-mcp/venv/bin/python3",
      "args": ["/Path/To/server.py"]
    }
  }
}
```



## RESTART CLAUDE AND HAPPY PROMPTING!!
