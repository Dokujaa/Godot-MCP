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
         "command": "/path/to/your/godot-mcp/python/venv/bin/python",
         "args": ["/path/to/your/godot-mcp/python/server.py"],
         "env": {}
       }
     }
   }
   ```
   
   Replace `/path/to/your/godot-mcp/python/server.py` with the actual path to your server.py file.

3. Restart Claude Desktop and happy prompting!

## Available Tools

### Editor Control
- **editor_action** — Execute an editor command (PLAY, STOP, SAVE)
- **play_scene** — Start playing the current scene
- **stop_scene** — Stop the currently playing scene
- **save_all** — Save all open resources
- **show_message** — Display a message dialog in the editor
- **capture_screenshot** — Capture the editor viewport as an image
- **send_game_input** — Send input commands to the running game (`move <direction> [steps]`, `interact`)

### Scene Management
- **get_scene_info** — Get info about the currently open scene
- **open_scene** — Open a scene from the project
- **save_scene** — Save the current scene
- **new_scene** — Create a new empty scene
- **create_object** — Create a new node in the scene
- **delete_object** — Delete a node from the scene
- **find_objects_by_name** — Search for nodes by name
- **set_object_transform** — Set position, rotation, and scale of a node
- **get_object_properties** — Get all properties of a node

### Object Manipulation
- **get_hierarchy** — Get the full node hierarchy of the current scene
- **rename_node** — Rename a node in the scene
- **set_property** — Set a property value on a node
- **set_nested_property** — Set a nested property (e.g. material sub-properties)
- **create_child_object** — Create a child node under a specified parent
- **set_mesh** — Assign a mesh to a MeshInstance3D node
- **set_collision_shape** — Set the collision shape on a collision node

### Scripts
- **view_script** — View the contents of a script file
- **create_script** — Create a new GDScript file
- **update_script** — Overwrite the contents of a script file
- **list_scripts** — List all scripts in a folder

### Materials
- **set_material** — Apply or create a material on a node
- **list_materials** — List all material assets in the project

### Assets
- **get_asset_list** — List assets in the project by type or pattern
- **import_asset** — Import an external file into the project
- **create_prefab** — Save a node as a packed scene (.tscn)
- **instantiate_prefab** — Add a packed scene to the current scene
- **import_3d_model** — Import a GLB/FBX/OBJ model into the scene
- **list_generated_meshes** — List Meshy-generated meshes in the project

### Meshy API (optional)
- **generate_mesh_from_text** — Generate a 3D mesh from a text prompt
- **generate_mesh_from_image** — Generate a 3D mesh from an image
- **check_mesh_generation_progress** — Poll the status of a mesh generation job
- **refine_generated_mesh** — Request a higher-quality refinement pass on a mesh
- **download_and_import_mesh** — Download a completed mesh and import it into Godot

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



