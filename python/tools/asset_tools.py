# tools/asset_tools.py
from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, List
from godot_connection import get_godot_connection
import json

def register_asset_tools(mcp: FastMCP):
    """Register all asset management tools with the MCP server."""
    
    @mcp.tool()
    def get_asset_list(
        ctx: Context,
        type: Optional[str] = None,
        search_pattern: str = "*",
        folder: str = "res://"
    ) -> str:
        """List assets in the project.
        
        Args:
            ctx: The MCP context
            type: Optional asset type to filter by (e.g., "scene", "script", "texture")
            search_pattern: Pattern to match in asset names
            folder: Folder path to search in
            
        Returns:
            str: JSON string with list of found assets or error details
        """
        try:
            # Ensure folder starts with res://
            if not folder.startswith("res://"):
                folder = "res://" + folder
            
            params = {
                "search_pattern": search_pattern,
                "folder": folder
            }
            
            if type:
                params["type"] = type
                
            response = get_godot_connection().send_command("GET_ASSET_LIST", params)
            assets = response.get("assets", [])
            
            if not assets:
                if type:
                    return f"No {type} assets found in {folder} matching '{search_pattern}'"
                else:
                    return f"No assets found in {folder} matching '{search_pattern}'"
                    
            return json.dumps(assets, indent=2)
        except Exception as e:
            return f"Error listing assets: {str(e)}"
            
    @mcp.tool()
    def import_asset(
        ctx: Context,
        source_path: str,
        target_path: str,
        overwrite: bool = False
    ) -> str:
        """Import an external asset into the project.
        
        Args:
            ctx: The MCP context
            source_path: Path to the source file on disk
            target_path: Path where the asset should be imported in the project
            overwrite: Whether to overwrite if an asset already exists at target path
            
        Returns:
            str: Success message or error details
        """
        try:
            # Ensure target_path starts with res://
            if not target_path.startswith("res://"):
                target_path = "res://" + target_path
            
            response = get_godot_connection().send_command("IMPORT_ASSET", {
                "source_path": source_path,
                "target_path": target_path,
                "overwrite": overwrite
            })
            
            return response.get("message", "Asset imported successfully")
        except Exception as e:
            return f"Error importing asset: {str(e)}"
            
    @mcp.tool()
    def create_prefab(
        ctx: Context,
        object_name: str,
        prefab_path: str,
        overwrite: bool = False
    ) -> str:
        """Create a packed scene (prefab) from an object in the scene.
        
        Args:
            ctx: The MCP context
            object_name: Name of the object to create a packed scene from
            prefab_path: Path where the packed scene should be saved
            overwrite: Whether to overwrite if a file already exists at the path
            
        Returns:
            str: Success message or error details
        """
        try:
            # Ensure prefab_path starts with res://
            if not prefab_path.startswith("res://"):
                prefab_path = "res://" + prefab_path
                
            # Ensure it has .tscn extension
            if not prefab_path.endswith(".tscn"):
                prefab_path += ".tscn"
            
            response = get_godot_connection().send_command("CREATE_PREFAB", {
                "object_name": object_name,
                "prefab_path": prefab_path,
                "overwrite": overwrite
            })
            
            if response.get("success", False):
                return f"Packed scene created successfully at {response.get('path', prefab_path)}"
            else:
                return f"Error creating packed scene: {response.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error creating packed scene: {str(e)}"
            
    @mcp.tool()
    def instantiate_prefab(
        ctx: Context,
        prefab_path: str,
        position_x: float = 0.0,
        position_y: float = 0.0,
        position_z: float = 0.0,
        rotation_x: float = 0.0,
        rotation_y: float = 0.0,
        rotation_z: float = 0.0
    ) -> str:
        """Instantiate a packed scene (prefab) into the current scene.
        
        Args:
            ctx: The MCP context
            prefab_path: Path to the packed scene file
            position_x: X position in 3D space
            position_y: Y position in 3D space
            position_z: Z position in 3D space
            rotation_x: X rotation in degrees
            rotation_y: Y rotation in degrees
            rotation_z: Z rotation in degrees
            
        Returns:
            str: Success message or error details
        """
        try:
            # Ensure prefab_path starts with res://
            if not prefab_path.startswith("res://"):
                prefab_path = "res://" + prefab_path
                
            # Ensure it has .tscn extension
            if not prefab_path.endswith(".tscn") and not prefab_path.endswith(".scn"):
                prefab_path += ".tscn"
            
            response = get_godot_connection().send_command("INSTANTIATE_PREFAB", {
                "prefab_path": prefab_path,
                "position_x": position_x,
                "position_y": position_y,
                "position_z": position_z,
                "rotation_x": rotation_x,
                "rotation_y": rotation_y,
                "rotation_z": rotation_z
            })
            
            if response.get("success", False):
                return f"Packed scene instantiated as {response.get('instance_name', 'unknown')}"
            else:
                return f"Error instantiating packed scene: {response.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error instantiating packed scene: {str(e)}"
    
    @mcp.tool()
    def import_3d_model(
        ctx: Context,
        model_path: str,
        name: str = None,
        position_x: float = 0.0,
        position_y: float = 0.0,
        position_z: float = 0.0,
        rotation_x: float = 0.0,
        rotation_y: float = 0.0,
        rotation_z: float = 0.0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        scale_z: float = 1.0
    ) -> str:
        """Import a 3D model file (GLB, FBX, OBJ) into the current scene as a MeshInstance3D.
        
        This is different from instantiate_prefab which is for .tscn packed scenes.
        Use this for 3D model files like those generated by Meshy API.
        
        Args:
            ctx: The MCP context
            model_path: Path to the 3D model file (e.g., res://assets/generated_meshes/House.glb)
            name: Optional name for the imported model node
            position_x: X position in 3D space
            position_y: Y position in 3D space
            position_z: Z position in 3D space
            rotation_x: X rotation in degrees
            rotation_y: Y rotation in degrees
            rotation_z: Z rotation in degrees
            scale_x: X scale factor
            scale_y: Y scale factor
            scale_z: Z scale factor
            
        Returns:
            str: Success message with node details or error
        """
        try:
            # Ensure model_path starts with res://
            if not model_path.startswith("res://"):
                model_path = "res://" + model_path
            
            # Determine the name from the file if not provided
            if not name:
                # Extract filename without extension
                filename = model_path.split('/')[-1]
                name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            
            # Check file extension
            extension = model_path.split('.')[-1].lower() if '.' in model_path else ""
            
            if extension == "glb" or extension == "gltf":
                # Use the specialized GLB import handler
                glb_response = get_godot_connection().send_command("IMPORT_GLB_SCENE", {
                    "glb_path": model_path,
                    "name": name,
                    "position": [position_x, position_y, position_z],
                    "rotation": [rotation_x, rotation_y, rotation_z],
                    "scale": [scale_x, scale_y, scale_z]
                })
                
                if glb_response.get("success", False):
                    instance_name = glb_response.get("instance_name", name)
                    return f"Successfully imported GLB model: {instance_name} at position ({position_x}, {position_y}, {position_z})"
                elif "error" in glb_response:
                    # If GLB import fails, try regular mesh approach
                    print(f"GLB import failed: {glb_response['error']}, trying mesh approach...")
                else:
                    # Continue to mesh approach
                    pass
            
            # Create a MeshInstance3D node
            create_response = get_godot_connection().send_command("CREATE_OBJECT", {
                "type": "MeshInstance3D",
                "name": name,
                "location": [position_x, position_y, position_z],
                "rotation": [rotation_x, rotation_y, rotation_z],
                "scale": [scale_x, scale_y, scale_z]
            })
            
            if "error" in create_response:
                return f"Failed to create MeshInstance3D: {create_response['error']}"
            
            # Try to set the mesh resource
            set_mesh_response = get_godot_connection().send_command("SET_PROPERTY", {
                "node_name": name,
                "property_name": "mesh",
                "value": model_path
            })
            
            if "error" in set_mesh_response:
                # If setting mesh fails, the node is still created
                return f"Created MeshInstance3D '{name}' but couldn't load mesh. You may need to manually assign the mesh from: {model_path}"
            
            return f"Successfully imported 3D model '{name}' from {model_path} at position ({position_x}, {position_y}, {position_z})"
            
        except Exception as e:
            return f"Error importing 3D model: {str(e)}"
    
    @mcp.tool()
    def list_generated_meshes(ctx: Context) -> str:
        """List all generated mesh files in the res://assets/generated_meshes/ folder.
        
        This is a convenience tool specifically for listing Meshy-generated models.
        
        Args:
            ctx: The MCP context
            
        Returns:
            str: List of generated mesh files or error message
        """
        try:
            response = get_godot_connection().send_command("GET_ASSET_LIST", {
                "search_pattern": ".glb",
                "folder": "res://assets/generated_meshes/"
            })
            
            assets = response.get("assets", [])
            
            if not assets:
                return "No generated meshes found. Generate some meshes using generate_mesh_from_text first!"
            
            # Format the output nicely
            result = "**Generated Meshes Available:**\n\n"
            glb_files = [asset for asset in assets if asset['name'].endswith('.glb')]
            
            for asset in glb_files:
                name = asset['name'].replace('.glb', '')
                result += f"• **{name}** - `{asset['path']}`\n"
            
            result += f"\n**Total:** {len(glb_files)} mesh(es)\n"
            result += "\nUse `import_3d_model` to add any of these to your scene!"
            
            return result
            
        except Exception as e:
            return f"Error listing generated meshes: {str(e)}"