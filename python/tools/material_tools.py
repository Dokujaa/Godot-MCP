# tools/material_tools.py
from mcp.server.fastmcp import FastMCP, Context
from typing import List, Optional
from godot_connection import get_godot_connection

def register_material_tools(mcp: FastMCP):
    """Register all material-related tools with the MCP server."""
    
    @mcp.tool()
    def set_material(
        ctx: Context,
        object_name: str,
        material_name: Optional[str] = None,
        color: Optional[List[float]] = None,
        create_if_missing: bool = True
    ) -> str:
        """Apply or create a material for an object.
        
        Args:
            ctx: The MCP context
            object_name: Name of the target object in the scene
            material_name: Optional name for a shared material. If provided, creates/uses a shared material asset
            color: Optional RGBA color values [r, g, b] or [r, g, b, a] in range 0.0-1.0
            create_if_missing: Whether to create the material if it doesn't exist
            
        Returns:
            str: Success message or error details
        """
        try:
            params = {
                "object_name": object_name,
                "create_if_missing": create_if_missing
            }
            
            if material_name:
                params["material_name"] = material_name
                
            if color:
                # Validate color array
                if len(color) < 3 or len(color) > 4:
                    return "Error: Color must be [r, g, b] or [r, g, b, a]"
                    
                # Ensure all values are in 0.0-1.0 range
                for value in color:
                    if value < 0.0 or value > 1.0:
                        return "Error: Color values must be in range 0.0-1.0"
                        
                params["color"] = color
            
            response = get_godot_connection().send_command("SET_MATERIAL", params)
            return response.get("message", "Material applied successfully")
        except Exception as e:
            return f"Error setting material: {str(e)}"
            
    @mcp.tool()
    def list_materials(ctx: Context, folder_path: str = "res://materials") -> str:
        """List all material files in a specified folder.
        
        Args:
            ctx: The MCP context
            folder_path: Path to the folder to search (default: "res://materials")
            
        Returns:
            str: List of material files or error message
        """
        try:
            # Use asset list command with material type filter
            response = get_godot_connection().send_command("GET_ASSET_LIST", {
                "type": "material",
                "folder": folder_path
            })
            
            materials = response.get("assets", [])
            if not materials:
                return f"No materials found in {folder_path}"
                
            result = "Available materials:\n"
            for mat in materials:
                result += f"- {mat.get('name')} ({mat.get('path')})\n"
                
            return result
        except Exception as e:
            return f"Error listing materials: {str(e)}"