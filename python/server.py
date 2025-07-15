# server.py
from mcp.server.fastmcp import FastMCP, Context, Image
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List
import json
import socket
import os
from config import config
from tools import register_all_tools
from godot_connection import get_godot_connection, GodotConnection

# Configure logging using settings from config
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format=config.log_format
)
logger = logging.getLogger("GodotMCP")

# Global connection state
_godot_connection: GodotConnection = None

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Handle server startup and shutdown."""
    global _godot_connection
    logger.info("GodotMCP server starting up")
    try:
        _godot_connection = get_godot_connection()
        logger.info("Connected to Godot on startup")
    except Exception as e:
        logger.warning(f"Could not connect to Godot on startup: {str(e)}")
        _godot_connection = None
    try:
        yield {}
    finally:
        if _godot_connection:
            _godot_connection.disconnect()
            _godot_connection = None
        logger.info("GodotMCP server shut down")

# Initialize MCP server
mcp = FastMCP(
    "GodotMCP",
    description="Godot Editor integration via Model Context Protocol",
    lifespan=server_lifespan
)

# Register all tools
register_all_tools(mcp)

# Editor Strategies and Best Practices Prompt
@mcp.prompt()
def godot_editor_strategy() -> str:
    """Guide for working with the Godot Engine editor through MCP."""
    return (
        "Godot MCP Server Tools and Best Practices:\n\n"
        "1. **Editor Control**\n"
        "   - `editor_control(command)` - Performs editor-wide actions such as `PLAY`, `STOP`, `SAVE`\n"
        "   - Commands available: PLAY, STOP, SAVE\n\n"
        
        "2. **Scene Management**\n"
        "   - `get_scene_info()` - Get current scene details\n"
        "   - `open_scene(scene_path)`, `save_scene()` - Open/save scenes\n"
        "   - `new_scene(scene_path, overwrite=False)` - Create new scenes\n\n"
        
        "3. **Object Management**\n"
        "   - ALWAYS use `find_objects_by_name(name)` to check if an object exists before creating or modifying it\n"
        "   - `create_object(type, name=None, location=None, rotation=None, scale=None)` - Create objects (e.g. `CUBE`, `SPHERE`, `EMPTY`, `CAMERA`)\n"
        "   - For adding children to existing objects, use: `create_child_object(parent_name, type, name=None, location=None, rotation=None, scale=None)` instead of creating and then parenting\n"
        "   - `delete_object(name)` - Remove objects\n"
        "   - `set_object_transform(name, location=None, rotation=None, scale=None)` - Modify object position, rotation, and scale\n"
        "   - `get_object_properties(name)` - Get object properties\n"
        "   - `find_objects_by_name(name)` - Find objects by name\n"
        "   - `set_parent(child_name, parent_name, keep_global_transform=True)` - Change a node's parent while maintaining proper ownership\n\n"
        
        "4. **Property Management**\n"
        "   - `set_property(node_name, property_name, value, force_type=None)` - Set properties on nodes\n"
        "   - Use dot notation for component properties: `set_property(node_name, \"position:y\", 5.0)` to set just the y component\n"
        "   - For type-specific values, use force_type parameter: `set_property(node_name, \"mass\", \"10.5\", force_type=\"float\")`\n"
        "   - For meshes, use the dedicated mesh function: `set_mesh(node_name, mesh_type, radius=None, height=None, size=None)`\n"
        "   - For example: `set_mesh(\"PlayerMesh\", \"CapsuleMesh\", radius=0.5, height=2.0)` or `set_mesh(\"Floor\", \"BoxMesh\", size=[10, 0.1, 10])`\n"
        "   - For collision shapes, use: `set_collision_shape(node_name, shape_type, radius=None, height=None, size=None)`\n"
        "   - For example: `set_collision_shape(\"Player/PlayerCollision\", \"CapsuleShape3D\", radius=0.4, height=1.8)`\n\n"
        
        "   **Advanced Property Handling:**\n"
        "   - For simple properties: `set_property(node_name, property_name, value)`\n"
        "   - For component-wise properties: `set_property(node_name, \"position:x\", 5.0)`\n"
        "   - For nested properties like environment settings:\n"
        "     `set_nested_property(node_name, nested_property_path, value)`\n"
        "   - Example: `set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material\", \"ProceduralSkyMaterial\")`\n\n"
        
        "   **Environment Properties Guide:**\n"
        "   - Basic environment properties:\n"
        "     • `environment/background_mode` - Background mode (0-6), use integers\n"
        "     • `environment/background_color` - Background color [r, g, b]\n"
        "     • `environment/ambient_light_color` - Ambient light color [r, g, b]\n"
        "     • `environment/fog_enabled` - Enable/disable fog (true/false)\n"
        "     • `environment/fog_density` - Fog density (float)\n"
        "     • `environment/fog_color` - Fog color [r, g, b]\n"
        "     • `environment/glow_enabled` - Enable/disable glow (true/false)\n"
        "     • `environment/glow_intensity` - Glow intensity (float)\n"
        "   - Sky material properties:\n"
        "     • `environment/sky/sky_material` - Material type (\"ProceduralSkyMaterial\", \"PanoramaSkyMaterial\")\n"
        "     • `environment/sky/sky_material/sky_top_color` - Color at the top of the sky [r, g, b]\n"
        "     • `environment/sky/sky_material/sky_horizon_color` - Color at the horizon [r, g, b]\n"
        "     • `environment/sky/sky_material/ground_bottom_color` - Color of the ground [r, g, b]\n"
        "     • `environment/sky/sky_material/ground_horizon_color` - Color of the ground at horizon [r, g, b]\n"
        "     • `environment/sky/sky_material/sun_angle_max` - Maximum sun angle (degrees)\n"
        "     • `environment/sky/sky_material/sky_curve` - Sky gradient curve (0.0-1.0)\n\n"
        "   - Setting up complete environment example:\n"
        "     ```\n"
        "     # Create environment\n"
        "     create_object(\"WorldEnvironment\", name=\"WorldEnvironment\")\n"
        "     \n"
        "     # Set sky material\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material\", \"ProceduralSkyMaterial\")\n"
        "     \n"
        "     # Set sky colors\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material/sky_top_color\", [0.1, 0.3, 0.8])\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material/sky_horizon_color\", [0.6, 0.7, 0.9])\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material/ground_horizon_color\", [0.5, 0.35, 0.15])\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material/ground_bottom_color\", [0.3, 0.2, 0.1])\n"
        "     \n"
        "     # Set ambient lighting\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/ambient_light_color\", [0.2, 0.3, 0.4])\n"
        "     \n"
        "     # Enable fog\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/fog_enabled\", true)\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/fog_density\", 0.02)\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/fog_color\", [0.5, 0.6, 0.7])\n"
        "     ```\n\n"
        
        "5. **Script Management**\n"
        "   - ALWAYS use `list_scripts(folder_path)` or `view_script(path)` to check if a script exists before creating or updating it\n"
        "   - `create_script(script_name, script_type=\"Node\", namespace=None, script_folder=\"res://scripts\", overwrite=False, content=None)` - Create scripts\n"
        "   - `view_script(script_path)`, `update_script(script_path, content, create_if_missing=False)` - View/modify scripts\n"
        "   - `list_scripts(folder_path=\"res://\")` - List scripts in folder\n\n"
        
        "6. **Asset Management**\n"
        "   - ALWAYS use `get_asset_list(type, search_pattern, folder)` to check if an asset exists before creating or importing it\n"
        "   - `import_asset(source_path, target_path, overwrite=False)` - Import external assets\n"
        "   - `import_3d_model(model_path, name=None, position_x=0, position_y=0, position_z=0)` - Import 3D models (GLB, FBX, OBJ) into the scene\n"
        "   - `instantiate_prefab(prefab_path, position_x=0, position_y=0, position_z=0, rotation_x=0, rotation_y=0, rotation_z=0)` - Instantiate packed scenes (.tscn files)\n"
        "   - `create_prefab(object_name, prefab_path, overwrite=False)` - Create packed scenes (Godot's equivalent to Unity prefabs)\n"
        "   - `get_asset_list(type=None, search_pattern=\"*\", folder=\"res://\")` - List project assets\n"
        "   - Use relative paths for Godot assets starting with \"res://\" (e.g., 'res://scenes/MyScene.tscn')\n"
        "   - Use absolute paths for external files\n"
        "   - **Important:** Use `import_3d_model` for GLB/FBX files, NOT `instantiate_prefab` which is only for .tscn files\n\n"
        
        "7. **Material Management**\n"
        "   - ALWAYS check if a material exists before creating or modifying it\n"
        "   - `set_material(object_name, material_name=None, color=None, create_if_missing=True)` - Apply/create materials\n"
        "   - Use RGB or RGBA colors (0.0-1.0 range)\n\n"
        
        "8. **Common Workflows**\n"
        "   - For hierarchical objects (like a character with collision): Use `create_object` for the parent, then `create_child_object` for the children\n"
        "   - For setting node properties: First check the property exists with `get_object_properties`, then use `set_property`\n"
        "   - For component-wise property changes: Use colon notation like `position:x` or `rotation:y`\n\n"
        
        "9. **Best Practices**\n"
        "   - ALWAYS verify existence before creating or updating any objects, scripts, assets, or materials\n"
        "   - Use `create_child_object` instead of `create_object` followed by `set_parent` for better hierarchy management\n"
        "   - Use meaningful names for nodes and scripts\n"
        "   - Keep scripts organized in dedicated folders\n"
        "   - Use correct node types (Node3D, MeshInstance3D, etc.)\n"
        "   - In Godot, Unity's prefabs are called 'packed scenes' (.tscn files)\n"
        "   - Godot uses different terminology than Unity: GameObjects are Nodes, Components are either built-in properties or scripts\n"
        "   - Paths in Godot start with 'res://' for project resources\n"
        "   - Use consistent capitalization; Godot node types are CamelCase (Node3D, MeshInstance3D)\n"
        "   - Verify transforms are applied to 3D nodes only (inheriting from Node3D)\n"
        "   - Keep scene hierarchies clean and logical\n"
        "   - Use Vector3 notation for position, rotation, and scale [x, y, z]\n\n"
        
        "10. **Godot MCP Best Practices**\n"
        "   **Node Creation and Hierarchy:**\n"
        "   - Create parent nodes first, then create children using `create_child_object`\n"
        "   - For character controllers: Create a CharacterBody3D parent → Then add MeshInstance3D and CollisionShape3D as children\n"
        "   - Example hierarchy pattern: `Player (CharacterBody3D) → [PlayerMesh (MeshInstance3D), PlayerCollision (CollisionShape3D)]`\n"
        "   - Use simple, clear hierarchies - avoid deeply nested objects when possible\n"
        "   - Put related objects (like a character and its components) under a common parent\n\n"
        
        "   **Working with Properties:**\n"
        "   - Always use specialized functions for complex objects instead of generic `set_property`:\n"
        "     • For meshes: `set_mesh(\"PlayerMesh\", \"CapsuleMesh\", radius=0.5, height=2.0)`\n"
        "     • For collision shapes: `set_collision_shape(\"PlayerCollision\", \"CapsuleShape3D\", radius=0.4, height=1.8)`\n"
        "     • For materials: `set_material(\"PlayerMesh\", color=[0.8, 0.2, 0.2])`\n"
        "     • For environment: `set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material\", \"ProceduralSkyMaterial\")`\n"
        "   - For node paths (Parent/Child), use node references, not string concatenation\n"
        "   - For vector components: Use `set_property(node_name, \"position:y\", 10.0)` syntax\n"
        "   - When getting properties, use `get_object_properties` first to understand what's available\n"
        "   - Verify property types before setting them; pass correct data types (arrays for vectors, etc.)\n\n"
        
        "   **Resource Handling:**\n"
        "   - Resource creation pattern: 1) Create parent node 2) Create child node 3) Set resource on child node\n"
        "   - Example for character: ```\n"
        "     create_object(\"CharacterBody3D\", name=\"Player\")\n"
        "     create_child_object(\"Player\", \"MeshInstance3D\", name=\"PlayerMesh\")\n"
        "     create_child_object(\"Player\", \"CollisionShape3D\", name=\"PlayerCollision\")\n"
        "     set_mesh(\"PlayerMesh\", \"CapsuleMesh\", radius=0.5, height=2.0)\n"
        "     set_collision_shape(\"PlayerCollision\", \"CapsuleShape3D\", radius=0.4, height=1.8)\n"
        "     ```\n"
        "   - For asset references, ensure they exist (use `get_asset_list`) before trying to use them\n"
        "   - Create texture resources with proper paths before assigning to materials\n\n"
        
        "11. **AI-Generated Mesh Integration (Meshy API)**\n"
        "   - `generate_mesh_from_text(prompt, name=None, art_style=\"realistic\", import_to_godot=True, position=None)` - Generate 3D meshes from text descriptions\n"
        "   - `generate_mesh_from_image(image_url, name=None, import_to_godot=True, position=None)` - Generate 3D meshes from images\n"
        "   - `refine_generated_mesh(task_id, name=None, import_to_godot=True, position=None)` - Refine previously generated meshes to higher quality\n"
        "   - Art styles available: \"realistic\", \"cartoon\", \"low-poly\", \"sculpture\"\n"
        "   - Requires MESHY_API_KEY environment variable to be set\n"
        "   - Generated meshes are automatically imported to `res://assets/generated_meshes/`\n\n"
        "   **⚠️ CRITICAL: API CREDIT USAGE WARNINGS**\n"
        "   - **NEVER automatically refine meshes when something goes wrong!**\n"
        "   - **Preview generation is FREE with test API key, refinement costs real credits**\n"
        "   - **Only use `refine_generated_mesh()` when explicitly requested by the user**\n"
        "   - **If a mesh generation fails or has issues, do NOT attempt refinement as a fix**\n"
        "   - **Always ask the user before refining a mesh to avoid wasting API credits**\n"
        "   - Use the test key `msy_dummy_api_key_for_test_mode_12345678` for testing without cost\n\n"
        "   - Example usage:\n"
        "     • `generate_mesh_from_text(\"a medieval sword with ornate handle\", name=\"MedievalSword\", art_style=\"realistic\")`\n"
        "     • `generate_mesh_from_text(\"cute cartoon mushroom house\", art_style=\"cartoon\", position=[5, 0, 3])`\n"
        "     • `generate_mesh_from_image(\"https://example.com/chair.jpg\", name=\"GeneratedChair\")`\n\n"
        "   - **Workflow for AI-Generated Content:**\n"
        "     1. Start with preview generation (faster, lower quality, often free)\n"
        "     2. **ONLY IF the user is satisfied AND explicitly requests it**: use `refine_generated_mesh()` for higher quality\n"
        "     3. **Never refine as an error recovery mechanism - this wastes API credits**\n"
        "     4. Meshes are automatically imported as MeshInstance3D objects\n"
        "     5. Generated meshes support PBR materials when available\n\n"
        
        "   **Scene Management:**\n"
        "   - Save current scene before opening a different one\n"
        "   - Use `get_scene_info` at the start of major operations to understand scene structure\n"
        "   - Create prefabs (packed scenes) for reusable objects\n"
        "   - Prefer scene instancing over duplicating node creation code\n\n"
        
        "   **Script Handling:**\n"
        "   - Create scripts in dedicated folders grouped by functionality\n"
        "   - Attach scripts to the highest logical node in a functional group\n"
        "   - Use `view_script` to understand existing scripts before modifying\n"
        "   - Follow Godot naming conventions: lowercase with underscores for filenames\n\n"
        
        "   **Common Pitfalls to Avoid:**\n"
        "   - DON'T set mesh/shape resources directly with `set_property` - use the specialized functions\n"
        "   - DON'T use forward slashes in node names (they're interpreted as paths)\n"
        "   - DON'T create nodes without properly setting their owners (use `create_child_object`)\n"
        "   - DON'T access paths like 'Parent/Child' with string operations - use proper node paths\n"
        "   - DON'T try to set read-only properties; check documentation if uncertain\n\n"
        
        "   **Type Conversion Guide:**\n"
        "   - Boolean: `true`/`false` or `1`/`0`\n"
        "   - Vector3: `[x, y, z]` as array of floats\n"
        "   - Vector2: `[x, y]` as array of floats\n"
        "   - Color: `[r, g, b]` or `[r, g, b, a]` as array of floats (0.0-1.0)\n"
        "   - Transform3D: Use individual position, rotation, scale properties instead\n\n"
        
        "   **Workflow Examples:**\n"
        "   - Creating a simple platform: ```\n"
        "     create_object(\"StaticBody3D\", name=\"Platform\", location=[0, -1, 0], scale=[10, 0.5, 10])\n"
        "     create_child_object(\"Platform\", \"MeshInstance3D\", name=\"PlatformMesh\")\n"
        "     create_child_object(\"Platform\", \"CollisionShape3D\", name=\"PlatformCollision\")\n"
        "     set_mesh(\"PlatformMesh\", \"BoxMesh\", size=[10, 0.5, 10])\n"
        "     set_collision_shape(\"PlatformCollision\", \"BoxShape3D\", size=[10, 0.5, 10])\n"
        "     ```\n"
        "   - Creating a light: ```\n"
        "     create_object(\"DirectionalLight3D\", name=\"Sun\", location=[10, 15, 5])\n"
        "     set_property(\"Sun\", \"light_energy\", 1.5)\n"
        "     set_property(\"Sun\", \"shadow_enabled\", true)\n"
        "     ```\n"
        "   - Creating a camera: ```\n"
        "     create_object(\"Camera3D\", name=\"MainCamera\", location=[0, 5, 10])\n"
        "     set_property(\"MainCamera\", \"rotation:x\", -30.0 * 0.0174533) # Convert degrees to radians\n"
        "     set_property(\"MainCamera\", \"current\", true)\n"
        "     ```\n"
        "   - Setting up environment: ```\n"
        "     create_object(\"WorldEnvironment\", name=\"WorldEnvironment\")\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material\", \"ProceduralSkyMaterial\")\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material/sky_top_color\", [0.1, 0.3, 0.8])\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/sky/sky_material/sky_horizon_color\", [0.6, 0.7, 0.9])\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/ambient_light_color\", [0.2, 0.3, 0.4])\n"
        "     set_nested_property(\"WorldEnvironment\", \"environment/fog_enabled\", true)\n"
        "     ```\n\n"
        
        "   **Debugging Tips:**\n"
        "   - If operations fail, check if the node exists with `find_objects_by_name`\n"
        "   - For complex operations, break them down into individual commands\n"
        "   - After creating nodes, verify their properties with `get_object_properties`\n"
        "   - When a command fails, try similar operations with simpler parameters first\n"
        "   - Use `show_message` to display debugging information in the Godot editor\n"
    )
# Run the server
if __name__ == "__main__":
    mcp.run(transport='stdio')