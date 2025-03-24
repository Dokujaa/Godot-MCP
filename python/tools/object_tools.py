# tools/object_tools.py
from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any, List, Optional
from godot_connection import get_godot_connection
import json

def register_object_tools(mcp: FastMCP):
    """Register all object inspection and manipulation tools with the MCP server."""
    
    @mcp.tool()
    def get_object_properties(ctx: Context, name: str) -> Dict[str, Any]:
        """Get all properties of a specified object (node).
        
        Args:
            ctx: The MCP context
            name: Name of the object to inspect
            
        Returns:
            Dict: Object containing the node's properties, components, and their values
        """
        try:
            response = get_godot_connection().send_command("GET_OBJECT_PROPERTIES", {
                "name": name
            })
            
            if "error" in response:
                return {"error": response["error"]}
                
            return response
        except Exception as e:
            return {"error": f"Failed to get object properties: {str(e)}"}
            
    @mcp.tool()
    def get_hierarchy(ctx: Context) -> str:
        """Get the detailed hierarchy of objects in the current scene.
        
        Args:
            ctx: The MCP context
            
        Returns:
            str: JSON string containing the complete scene hierarchy
        """
        try:
            scene_info = get_godot_connection().send_command("GET_SCENE_INFO")
            
            if "error" in scene_info:
                return f"Error: {scene_info['error']}"
            
            # Format the hierarchy for better readability
            formatted_result = {
                "scene_name": scene_info.get("name", "Unknown"),
                "scene_path": scene_info.get("path", "Unknown"),
            }
            
            # Include the full hierarchy if available
            if "hierarchy" in scene_info:
                formatted_result["hierarchy"] = scene_info["hierarchy"]
                
                # Print a more readable tree representation
                tree_view = _format_node_tree(scene_info["hierarchy"], indent="")
                return f"Scene: {formatted_result['scene_name']} ({formatted_result['scene_path']})\n\n{tree_view}"
            else:
                # Fall back to the simple root_objects list if full hierarchy isn't available
                formatted_result["root_objects"] = scene_info.get("root_objects", [])
                return json.dumps(formatted_result, indent=2)
                
        except Exception as e:
            return f"Error getting hierarchy: {str(e)}"

    def _format_node_tree(node_data, indent=""):
        """Helper function to format node hierarchy as a tree view."""
        result = f"{indent}└─ {node_data['name']} ({node_data['type']})"
        
        # Add script info if available
        if "script" in node_data:
            result += f" [Script: {node_data['script']}]"
        
        # Add transform info for 3D nodes
        if "transform" in node_data:
            pos = node_data["transform"].get("position", [0, 0, 0])
            pos_str = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})" if len(pos) >= 3 else f"({pos[0]:.1f}, {pos[1]:.1f})"
            result += f" at {pos_str}"
        
        # Process children with increased indentation
        if "children" in node_data and node_data["children"]:
            result += "\n"
            for i, child in enumerate(node_data["children"]):
                # Use different indentation for last child
                is_last = i == len(node_data["children"]) - 1
                child_indent = indent + ("    " if is_last else "│   ")
                result += _format_node_tree(child, child_indent) + "\n"
        
        return result.rstrip()


    @mcp.tool()
    def rename_node(
        ctx: Context,
        old_name: str,
        new_name: str
    ) -> str:
        """Rename a node in the scene.
        
        Args:
            ctx: The MCP context
            old_name: Current name of the node
            new_name: New name for the node
            
        Returns:
            str: Success message or error details
        """
        try:
            # Check if node with old_name exists
            old_response = get_godot_connection().send_command("FIND_OBJECTS_BY_NAME", {
                "name": old_name
            })
            
            node_exists = len(old_response.get("objects", [])) > 0
            if not node_exists:
                return f"Error: Node '{old_name}' not found"
                
            # Check if new_name is already taken
            new_response = get_godot_connection().send_command("FIND_OBJECTS_BY_NAME", {
                "name": new_name
            })
            
            name_taken = len(new_response.get("objects", [])) > 0
            if name_taken:
                return f"Error: Name '{new_name}' is already taken by another node"
                
            # Rename the node
            rename_response = get_godot_connection().send_command("RENAME_NODE", {
                "old_name": old_name,
                "new_name": new_name
            })
            
            if "error" in rename_response:
                return f"Error renaming node: {rename_response['error']}"
                
            return f"Renamed node from '{old_name}' to '{new_name}'"
        except Exception as e:
            return f"Error renaming node: {str(e)}"
            
    @mcp.tool()
    def set_property(
        ctx: Context,
        node_name: str,
        property_name: str,
        value: Any
    ) -> str:
        """Set a property value on a node.
        
        Args:
            ctx: The MCP context
            node_name: Name of the target node
            property_name: Name of the property to set
            value: New value for the property
            
        Returns:
            str: Success message or error details
        """
        try:
            # Check input parameters
            if not node_name or not isinstance(node_name, str):
                return "Error: Invalid node_name parameter"
            
            if not property_name or not isinstance(property_name, str):
                return "Error: Invalid property_name parameter"
            
            # Handle special cases
            if property_name == "script" and isinstance(value, str):
                # Ensure script path starts with res://
                if not value.startswith("res://"):
                    value = "res://" + value
                
                # Ensure script has .gd extension if no extension provided
                if "." not in value.split("/")[-1]:
                    value += ".gd"
            
            # Send the command
            response = get_godot_connection().send_command("SET_PROPERTY", {
                "node_name": node_name,
                "property_name": property_name,
                "value": value
            })
            
            return response.get("message", f"Set property '{property_name}' on node '{node_name}' to {value}")
        except Exception as e:
            return f"Error setting property: {str(e)}"
        
    @mcp.tool()
    def create_child_object(
        ctx: Context,
        parent_name: str,
        type: str = "EMPTY",
        name: str = None,
        location: List[float] = None,
        rotation: List[float] = None,
        scale: List[float] = None,
        replace_if_exists: bool = False
    ) -> str:
        """Create a new object as a child of an existing node.
        
        Args:
            ctx: The MCP context
            parent_name: Name of the parent node to attach this object to
            type: Type of object to create (e.g., "Node3D", "MeshInstance3D", "CUBE")
            name: Optional name for the new object
            location: Optional [x, y, z] position
            rotation: Optional [x, y, z] rotation in degrees
            scale: Optional [x, y, z] scale factors
            replace_if_exists: Whether to replace if an object with the same name exists
                
        Returns:
            str: Success message or error details
        """
        try:
            params = {
                "parent_name": parent_name,
                "type": type,
                "replace_if_exists": replace_if_exists
            }
            
            if name:
                params["name"] = name
            if location:
                params["location"] = location
            if rotation:
                params["rotation"] = rotation
            if scale:
                params["scale"] = scale
            
            response = get_godot_connection().send_command("CREATE_CHILD_OBJECT", params)
            
            if isinstance(response, dict) and "name" in response:
                node_type = response.get("type", type)
                return f"Created {node_type} object: {response['name']} as child of {parent_name}"
            else:
                return f"Created {type} object as child of {parent_name}"
        except Exception as e:
            return f"Error creating child object: {str(e)}"
        

    @mcp.tool()
    def set_mesh(
        ctx: Context,
        node_name: str,
        mesh_type: str,
        radius: float = None,
        height: float = None,
        size: List[float] = None
    ) -> str:
        """Set a mesh on a MeshInstance3D node.
        
        Args:
            ctx: The MCP context
            node_name: Name of the target MeshInstance3D node
            mesh_type: Type of mesh to create (CapsuleMesh, BoxMesh, SphereMesh, CylinderMesh, PlaneMesh)
            radius: Radius for CapsuleMesh, SphereMesh, or CylinderMesh
            height: Height for CapsuleMesh or CylinderMesh
            size: Size for BoxMesh [x, y, z] or PlaneMesh [x, y]
            
        Returns:
            str: Success message or error details
        """
        try:
            params = {
                "node_name": node_name,
                "mesh_type": mesh_type
            }
            
            # Add optional parameters if provided
            mesh_params = {}
            if radius is not None:
                mesh_params["radius"] = radius
            if height is not None:
                mesh_params["height"] = height
            if size is not None:
                mesh_params["size"] = size
            
            if mesh_params:
                params["mesh_params"] = mesh_params
            
            response = get_godot_connection().send_command("SET_MESH", params)
            return response.get("message", f"Set {mesh_type} on node '{node_name}'")
        except Exception as e:
            return f"Error setting mesh: {str(e)}"
        

    @mcp.tool()
    def set_collision_shape(
        ctx: Context,
        node_name: str,
        shape_type: str,
        radius: float = None,
        height: float = None,
        size: List[float] = None
    ) -> str:
        """Set a collision shape on a CollisionShape3D or CollisionShape2D node.
        
        Args:
            ctx: The MCP context
            node_name: Name or path of the target CollisionShape node
            shape_type: Type of shape to create (CapsuleShape3D, BoxShape3D, SphereShape3D, etc.)
            radius: Radius for CapsuleShape3D, SphereShape3D, etc.
            height: Height for CapsuleShape3D or CylinderShape3D
            size: Size for BoxShape3D [x, y, z] or RectangleShape2D [x, y]
            
        Returns:
            str: Success message or error details
        """
        try:
            params = {
                "node_name": node_name,
                "shape_type": shape_type
            }
            
            # Add optional parameters if provided
            shape_params = {}
            if radius is not None:
                shape_params["radius"] = radius
            if height is not None:
                shape_params["height"] = height
            if size is not None:
                shape_params["size"] = size
            
            if shape_params:
                params["shape_params"] = shape_params
            
            response = get_godot_connection().send_command("SET_COLLISION_SHAPE", params)
            return response.get("message", f"Set {shape_type} on node '{node_name}'")
        except Exception as e:
            return f"Error setting collision shape: {str(e)}"
        
    @mcp.tool()
    def set_nested_property(
        ctx: Context,
        node_name: str,
        property_name: str,
        value: Any,
        value_type: str = None
    ) -> str:
        """Set a nested property on a node (like environment/sky/sky_material).
        
        Args:
            ctx: The MCP context
            node_name: Name of the target node
            property_name: Path to the nested property using slashes (e.g., "environment/sky/sky_material")
            value: Value to set
            value_type: Optional type hint for the value
            
        Returns:
            str: Success message or error details
        """
        try:
            params = {
                "node_name": node_name,
                "property_name": property_name,
                "value": value
            }
            
            if value_type:
                params["value_type"] = value_type
            
            response = get_godot_connection().send_command("SET_NESTED_PROPERTY", params)
            return response.get("message", f"Set nested property {property_name} on {node_name}")
        except Exception as e:
            return f"Error setting nested property: {str(e)}"