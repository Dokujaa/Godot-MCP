# tools/scene_tools.py
from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any, List
import json
from godot_connection import get_godot_connection
from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any
import json
from godot_connection import get_godot_connection

def register_scene_tools(mcp: FastMCP):
    """Register all scene-related tools with the MCP server."""
    
    @mcp.tool()
    def get_scene_info(ctx: Context) -> str:
        """Get information about the current scene.
        
        Returns:
            str: JSON string containing scene information
        """
        try:
            godot = get_godot_connection()
            result = godot.send_command("GET_SCENE_INFO")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting scene info: {str(e)}"

    @mcp.tool()
    def open_scene(ctx: Context, scene_path: str, save_current: bool = False) -> str:
        """Open a scene from the project.
        
        Args:
            ctx: The MCP context
            scene_path: Path to the scene file (e.g., "res://scenes/Main.tscn")
            save_current: Whether to save the current scene before opening the new one
            
        Returns:
            str: Success message or error details
        """
        try:
            # Ensure path starts with res://
            if not scene_path.startswith("res://"):
                scene_path = "res://" + scene_path
            
            # Ensure it has .tscn extension
            if not scene_path.endswith(".tscn") and not scene_path.endswith(".scn"):
                scene_path += ".tscn"
            
            response = get_godot_connection().send_command("OPEN_SCENE", {
                "scene_path": scene_path,
                "save_current": save_current
            })
            return response.get("message", "Scene opened successfully")
        except Exception as e:
            return f"Error opening scene: {str(e)}"

    @mcp.tool()
    def save_scene(ctx: Context) -> str:
        """Save the current scene.
        
        Args:
            ctx: The MCP context
            
        Returns:
            str: Success message or error details
        """
        try:
            response = get_godot_connection().send_command("SAVE_SCENE")
            return response.get("message", "Scene saved successfully")
        except Exception as e:
            return f"Error saving scene: {str(e)}"

    @mcp.tool()
    def new_scene(ctx: Context, scene_path: str, overwrite: bool = False) -> str:
        """Create a new empty scene.
        
        Args:
            ctx: The MCP context
            scene_path: Path where the new scene should be saved (e.g., "res://scenes/New.tscn")
            overwrite: Whether to overwrite if the scene already exists
            
        Returns:
            str: Success message or error details
        """
        try:
            # Ensure path starts with res://
            if not scene_path.startswith("res://"):
                scene_path = "res://" + scene_path
            
            # Ensure it has .tscn extension
            if not scene_path.endswith(".tscn"):
                scene_path += ".tscn"
            
            response = get_godot_connection().send_command("NEW_SCENE", {
                "scene_path": scene_path,
                "overwrite": overwrite
            })
            return response.get("message", "New scene created successfully")
        except Exception as e:
            return f"Error creating new scene: {str(e)}"

    @mcp.tool()
    def create_object(
        ctx: Context,
        type: str = "EMPTY",
        name: str = None,
        location: list = None,
        rotation: list = None,
        scale: list = None,
        replace_if_exists: bool = False
    ) -> str:
        """Create a new object (node) in the current scene.
        
        Args:
            ctx: The MCP context
            type: Type of object to create. Common types include:
                - 3D Nodes: "Node3D", "MeshInstance3D", "Camera3D", "DirectionalLight3D", etc.
                - 3D Primitives: "CUBE", "SPHERE", "CYLINDER", "PLANE"
                - 2D Nodes: "Node2D", "Sprite2D", "Camera2D", etc.
                - UI Nodes: "Control", "Panel", "Button", "Label", etc.
            name: Optional name for the new object
            location: Optional [x, y, z] position (for 2D nodes, only x,y are used)
            rotation: Optional [x, y, z] rotation in degrees (for 2D nodes, only x is used)
            scale: Optional [x, y, z] scale factors (for 2D nodes, only x,y are used)
            replace_if_exists: Whether to replace if an object with the same name exists
                
        Returns:
            str: Success message or error details
        """
        try:
            params = {"type": type}
            if name:
                params["name"] = name
            if location:
                params["location"] = location
            if rotation:
                params["rotation"] = rotation
            if scale:
                params["scale"] = scale
            params["replace_if_exists"] = replace_if_exists
            
            response = get_godot_connection().send_command("CREATE_OBJECT", params)
            
            if isinstance(response, dict) and "name" in response:
                node_type = response.get("type", type)
                return f"Created {node_type} object: {response['name']}"
            else:
                return f"Created {type} object"
        except Exception as e:
            return f"Error creating object: {str(e)}"
    
    @mcp.tool()
    def delete_object(ctx: Context, name: str) -> str:
        """Delete an object (node) from the current scene.
        
        Args:
            ctx: The MCP context
            name: Name of the object to delete
            
        Returns:
            str: Success message or error details
        """
        try:
            response = get_godot_connection().send_command("DELETE_OBJECT", {
                "name": name
            })
            return response.get("message", f"Object deleted: {name}")
        except Exception as e:
            return f"Error deleting object: {str(e)}"
            
    @mcp.tool()
    def find_objects_by_name(ctx: Context, name: str) -> str:
        """Find objects in the scene by name (partial matches supported).
        
        Args:
            ctx: The MCP context
            name: Name to search for
            
        Returns:
            str: JSON string with list of found objects or error details
        """
        try:
            response = get_godot_connection().send_command("FIND_OBJECTS_BY_NAME", {
                "name": name
            })
            
            objects = response.get("objects", [])
            if not objects:
                return f"No objects found with name containing '{name}'"
                
            return json.dumps(objects, indent=2)
        except Exception as e:
            return f"Error finding objects: {str(e)}"
            
    @mcp.tool()
    def set_object_transform(
        ctx: Context,
        name: str,
        location: List[float] = None,
        rotation: List[float] = None,
        scale: List[float] = None
    ) -> str:
        """Set the transform (position, rotation, scale) of an object.
        
        Args:
            ctx: The MCP context
            name: Name of the object to modify
            location: Optional [x, y, z] position
            rotation: Optional [x, y, z] rotation in degrees
            scale: Optional [x, y, z] scale factors
            
        Returns:
            str: Success message or error details
        """
        try:
            params = {"name": name}
            if location:
                params["location"] = location
            if rotation:
                params["rotation"] = rotation
            if scale:
                params["scale"] = scale
                
            response = get_godot_connection().send_command("SET_OBJECT_TRANSFORM", params)
            return response.get("message", f"Transform updated for {name}")
        except Exception as e:
            return f"Error setting transform: {str(e)}"
            
    @mcp.tool()
    def get_object_properties(ctx: Context, name: str) -> str:
        """Get all properties of an object.
        
        Args:
            ctx: The MCP context
            name: Name of the object to inspect
            
        Returns:
            str: JSON string with object properties or error details
        """
        try:
            response = get_godot_connection().send_command("GET_OBJECT_PROPERTIES", {
                "name": name
            })
            
            if "error" in response:
                return f"Error: {response['error']}"
                
            return json.dumps(response, indent=2)
        except Exception as e:
            return f"Error getting object properties: {str(e)}"