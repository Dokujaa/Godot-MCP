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