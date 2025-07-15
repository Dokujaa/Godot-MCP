# Godot MCP Server

A Model Context Protocol (MCP) server that enables Claude Desktop to control and interact with the Godot Engine editor. This allows you to use Claude to create scenes, manipulate objects, write scripts, and perform various editor operations directly through conversation.

## Architecture

This project consists of two components:

1. **Godot Plugin** (`addons/godot_mcp/`) - Runs inside Godot Editor and listens for commands on port 6400
2. **Python MCP Server** (`python/`) - Acts as a bridge between Claude Desktop and the Godot plugin

## Setup Instructions

### Prerequisites

- Godot Engine (4.x or later)
- Python 3.8+
- Claude Desktop app
- Meshy API account (optional, for AI-generated meshes)

### Step 1: Install Godot Plugin

1. Copy the `addons/godot_mcp/` folder to your Godot project's `addons/` directory
2. Open your Godot project
3. Go to `Project → Project Settings → Plugins`
4. Enable the "Godot MCP" plugin
5. You should see an "MCP" panel appear at the bottom of the editor
6. The plugin automatically starts listening on port 6400

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

3. Restart Claude Desktop

### Step 4: Set up Meshy API (Optional)

If you want to use AI-generated mesh features:

**For Testing (Free - No Credits Consumed):**
```bash
export MESHY_API_KEY="msy_dummy_api_key_for_test_mode_12345678"
```

**For Production:**
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

   **Option B: Using system environment variables**
   ```bash
   export MESHY_API_KEY="your_api_key_here"
   ```
   
   Or add it to your shell profile (`.zshrc`, `.bashrc`, etc.):
   ```bash
   echo 'export MESHY_API_KEY="your_api_key_here"' >> ~/.zshrc
   source ~/.zshrc
   ```

**Note**: The test API key (`msy_dummy_api_key_for_test_mode_12345678`) returns sample results without consuming credits, perfect for testing your integration before using your real API key.

### Step 5: Test the Setup

1. Make sure Godot is running with your project open and the MCP plugin enabled
2. Open Claude Desktop
3. Start a new conversation and try asking Claude to:
   - Get scene information: "Can you show me information about the current scene?"
   - Create objects: "Create a cube named 'TestCube' at position [2, 1, 0]"
   - Manipulate objects: "Set the material color of TestCube to red"
   - Generate AI meshes: "Generate a realistic medieval sword and place it at [0, 1, 0]"

## Usage

Once set up, you can ask Claude to perform various Godot operations:

### Scene Management
- Get current scene info
- Open/save scenes
- Create new scenes

### Object Operations
- Create 3D/2D objects and UI elements
- Set object transforms (position, rotation, scale)
- Create parent-child relationships
- Set object properties

### Script Management
- Create GDScript files
- View and edit existing scripts
- List scripts in the project

### Material and Asset Management
- Set material properties and colors
- Import external assets
- Create and instantiate packed scenes (prefabs)

### Environment Setup
- Configure WorldEnvironment settings
- Set up lighting and sky materials
- Adjust fog and atmospheric effects

### AI-Generated Meshes (with Meshy API)
- Generate 3D models from text descriptions
- Convert images to 3D meshes
- Refine generated meshes to higher quality
- Automatic import and placement in scenes

## Configuration

The server configuration can be modified in `python/config.py`:

- `godot_host`: Godot connection host (default: "localhost")
- `godot_port`: Godot plugin port (default: 6400)
- `connection_timeout`: Connection timeout in seconds (default: 300)
- `log_level`: Logging level (default: "INFO")

## Troubleshooting

### Connection Issues

1. **"Could not connect to Godot"**: 
   - Ensure Godot is running with your project open
   - Check that the MCP plugin is enabled
   - Verify the plugin is listening on port 6400 (check the MCP panel in Godot)

2. **"MCP server not responding"**:
   - Check the Claude Desktop configuration path is correct
   - Ensure Python virtual environment is activated
   - Check the server.py path in Claude Desktop config

3. **Permission Errors**:
   - Ensure the Python script has execute permissions
   - Check that the virtual environment is properly activated

### Debug Mode

To enable debug logging, modify `config.py`:
```python
log_level: str = "DEBUG"
```

This will provide detailed logs of all commands and responses between Claude and Godot.

## Available Commands

The MCP server provides these tools to Claude:

- **Scene Tools**: `get_scene_info`, `open_scene`, `save_scene`, `new_scene`
- **Object Tools**: `create_object`, `create_child_object`, `delete_object`, `find_objects_by_name`
- **Transform Tools**: `set_object_transform`, `set_parent`
- **Property Tools**: `set_property`, `set_nested_property`, `get_object_properties`
- **Material Tools**: `set_material`, `set_mesh`, `set_collision_shape`
- **Script Tools**: `create_script`, `view_script`, `update_script`, `list_scripts`
- **Asset Tools**: `import_asset`, `get_asset_list`, `create_prefab`, `instantiate_prefab`
- **Editor Tools**: `editor_action`, `play_scene`, `stop_scene`, `save_all`
- **AI Mesh Tools**: `generate_mesh_from_text`, `generate_mesh_from_image`, `refine_generated_mesh`

## Examples

Here are some example interactions you can have with Claude:

```
"Create a simple 3D scene with a ground plane, a player character, and some lighting"

"Set up a basic character controller with a CharacterBody3D, mesh, and collision shape"

"Create a simple inventory system script for an RPG game"

"Set up a beautiful sky environment with clouds and atmospheric lighting"

"Generate a realistic dragon model and place it in the scene"

"Create a low-poly fantasy village with houses, trees, and a well from text descriptions"
```

## License

[Your License Here]
