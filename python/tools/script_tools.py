# tools/script_tools.py
from mcp.server.fastmcp import FastMCP, Context
from typing import List
from godot_connection import get_godot_connection

def register_script_tools(mcp: FastMCP):
    """Register all script-related tools with the MCP server."""
    
    @mcp.tool()
    def view_script(ctx: Context, script_path: str, require_exists: bool = True) -> str:
        """View the contents of a Godot script file.
        
        Args:
            ctx: The MCP context
            script_path: Path to the script file (e.g., "res://scripts/player.gd")
            require_exists: Whether to raise an error if the file doesn't exist
            
        Returns:
            str: The contents of the script file or error message
        """
        try:
            # Ensure path starts with res://
            if not script_path.startswith("res://"):
                script_path = "res://" + script_path
                
            # Ensure it has .gd extension if no extension is provided
            if "." not in script_path.split("/")[-1]:
                script_path += ".gd"
            
            response = get_godot_connection().send_command("VIEW_SCRIPT", {
                "script_path": script_path,
                "require_exists": require_exists
            })
            
            if response.get("exists", True):
                return response.get("content", "Script contents not available")
            else:
                return response.get("message", "Script not found")
        except Exception as e:
            return f"Error viewing script: {str(e)}"

    @mcp.tool()
    def create_script(
        ctx: Context,
        script_name: str,
        script_type: str = "Node",
        namespace: str = None,
        script_folder: str = "res://scripts",
        overwrite: bool = False,
        content: str = None
    ) -> str:
        """Create a new Godot script file.
        
        Args:
            ctx: The MCP context
            script_name: Name of the script (with or without .gd extension)
            script_type: Base class to extend (e.g., "Node", "Node3D", "Control")
            namespace: Optional class_name for the script
            script_folder: Folder path within the project to create the script
            overwrite: Whether to overwrite if script already exists
            content: Optional custom content for the script
            
        Returns:
            str: Success message or error details
        """
        try:
            # Ensure script_name has .gd extension
            if not script_name.endswith(".gd"):
                script_name += ".gd"
                
            # Ensure script_folder starts with res://
            if not script_folder.startswith("res://"):
                script_folder = "res://" + script_folder
            
            params = {
                "script_name": script_name,
                "script_type": script_type,
                "script_folder": script_folder,
                "overwrite": overwrite
            }
            
            if namespace:
                params["namespace"] = namespace
                
            if content:
                params["content"] = content
                
            response = get_godot_connection().send_command("CREATE_SCRIPT", params)
            return response.get("message", "Script created successfully")
        except Exception as e:
            return f"Error creating script: {str(e)}"

    @mcp.tool()
    def update_script(
        ctx: Context,
        script_path: str,
        content: str,
        create_if_missing: bool = False,
        create_folder_if_missing: bool = False
    ) -> str:
        """Update the contents of an existing Godot script.
        
        Args:
            ctx: The MCP context
            script_path: Path to the script file (e.g., "res://scripts/player.gd")
            content: New content for the script
            create_if_missing: Whether to create the script if it doesn't exist
            create_folder_if_missing: Whether to create the parent directory if needed
            
        Returns:
            str: Success message or error details
        """
        try:
            # Ensure path starts with res://
            if not script_path.startswith("res://"):
                script_path = "res://" + script_path
                
            # Ensure it has .gd extension if no extension is provided
            if "." not in script_path.split("/")[-1]:
                script_path += ".gd"
            
            response = get_godot_connection().send_command("UPDATE_SCRIPT", {
                "script_path": script_path,
                "content": content,
                "create_if_missing": create_if_missing,
                "create_folder_if_missing": create_folder_if_missing
            })
            
            return response.get("message", "Script updated successfully")
        except Exception as e:
            return f"Error updating script: {str(e)}"

    @mcp.tool()
    def list_scripts(ctx: Context, folder_path: str = "res://") -> str:
        """List all script files in a specified folder.
        
        Args:
            ctx: The MCP context
            folder_path: Path to the folder to search (default: "res://")
            
        Returns:
            str: List of script files or error message
        """
        try:
            # Ensure path starts with res://
            if not folder_path.startswith("res://"):
                folder_path = "res://" + folder_path
            
            response = get_godot_connection().send_command("LIST_SCRIPTS", {
                "folder_path": folder_path
            })
            
            scripts = response.get("scripts", [])
            if not scripts:
                return "No scripts found in the specified folder"
                
            return "\n".join(scripts)
        except Exception as e:
            return f"Error listing scripts: {str(e)}"