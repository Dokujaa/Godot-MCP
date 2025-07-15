# Godot MCP Server

A Model Context Protocol (MCP) server that enables Claude Desktop to control and interact with the Godot Engine editor.


# DEMO VIDEO 



https://github.com/user-attachments/assets/07424399-31b5-47ee-a20d-808b2e789731


# NEW UPDATE!!!! ADDED MESHY API INTEGRATION

<img width="324" height="331" alt="Screenshot 2025-07-14 at 9 07 13 PM" src="https://github.com/user-attachments/assets/f907d709-8f09-46b7-a70e-754b4f4cbbf1" />

GENERATE DYNAMIC SCENES BY CALLING THE MESHY API, DIRECTLY IMPORTED INTO GODOT






## Setup Instructions

### Prerequisites

- Godot Engine (4.x or later)
- Python 3.8+
- Claude Desktop app
- Meshy API account (optional, for AI-generated meshes)


### STEP 0: Clone the repo and navigate to the directory

```bash
git clone https://github.com/Dokujaa/Godot-MCP.git

```




### Step 1: Install Godot Plugin

1. Copy the `addons/godot_mcp/` folder to your Godot project's `addons/` directory
2. Open your Godot project
3. Go to `Project → Project Settings → Plugins`
4. Enable the "Godot MCP" plugin
5. You should see an "MCP" panel appear at the bottom of the editor
6. The plugin automatically starts listening on a port

### Step 2: Set up Python Environment

1. Navigate to the `python/` directory:
   ```bash
   cd python
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

### Step 3: Configure Claude Desktop

1. Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the Godot MCP server configuration:
   ```json
   {
     "mcpServers": {
       "godot": {
         "command": "python",
         "args": ["/path/to/your/godot-mcp/python/server.py"],
         "env": {}
       }
     }
   }
   ```
   
   Replace `/path/to/your/godot-mcp/python/server.py` with the actual path to your server.py file.

3. Restart Claude Desktop and happy prompting!

### OPTIONAL: Set up Meshy API

1. Sign up for a Meshy API account at [https://www.meshy.ai/](https://www.meshy.ai/)
2. Get your API key from the dashboard (format: `msy-<random-string>`)
3. Set up your API key using one of these methods:

   **Option A: Using .env file (Recommended)**
   ```bash
   # Copy the example file
   cp python/.env.example python/.env
   
   # Edit the .env file and add your API key
   nano python/.env  # or use your preferred editor
   ```
   
   Then add your key to the `.env` file:
   ```
   MESHY_API_KEY=your_actual_api_key_here
   ```



