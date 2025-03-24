# tools/editor_tools.py
from mcp.server.fastmcp import FastMCP, Context
from typing import Optional
from godot_connection import get_godot_connection

def register_editor_tools(mcp: FastMCP):
    """Register all editor control tools with the MCP server."""
    
    @mcp.tool()
    def editor_action(ctx: Context, command: str) -> str:
        """Execute an editor command like play, stop, or save.
        
        Args:
            ctx: The MCP context
            command: The command to execute (PLAY, STOP, SAVE)
            
        Returns:
            str: Success message or error details
        """
        try:
            # Validate command
            valid_commands = ["PLAY", "STOP", "SAVE"]
            if command.upper() not in valid_commands:
                return f"Error: Invalid command '{command}'. Valid commands are {', '.join(valid_commands)}"
            
            response = get_godot_connection().send_command("EDITOR_CONTROL", {
                "command": command.upper()
            })
            
            return response.get("message", f"Editor command '{command}' executed")
        except Exception as e:
            return f"Error executing editor command: {str(e)}"
            
    @mcp.tool()
    def show_message(
        ctx: Context,
        title: str,
        message: str,
        type: str = "INFO"
    ) -> str:
        """Show a message in the Godot editor.
        
        Args:
            ctx: The MCP context
            title: Title of the message
            message: Content of the message
            type: Message type (INFO, WARNING, ERROR)
            
        Returns:
            str: Success message or error details
        """
        try:
            # Validate message type
            valid_types = ["INFO", "WARNING", "ERROR"]
            if type.upper() not in valid_types:
                return f"Error: Invalid message type '{type}'. Valid types are {', '.join(valid_types)}"
            
            response = get_godot_connection().send_command("EDITOR_CONTROL", {
                "command": "SHOW_MESSAGE",
                "params": {
                    "title": title,
                    "message": message,
                    "type": type.upper()
                }
            })
            
            return response.get("message", "Message shown in editor")
        except Exception as e:
            return f"Error showing message: {str(e)}"

    @mcp.tool()
    def play_scene(ctx: Context) -> str:
        """Start playing the current scene in the editor.
        
        Args:
            ctx: The MCP context
            
        Returns:
            str: Success message or error details
        """
        return editor_action(ctx, "PLAY")
        
    @mcp.tool()
    def stop_scene(ctx: Context) -> str:
        """Stop playing the current scene in the editor.
        
        Args:
            ctx: The MCP context
            
        Returns:
            str: Success message or error details
        """
        return editor_action(ctx, "STOP")
        
    @mcp.tool()
    def save_all(ctx: Context) -> str:
        """Save all open resources in the editor.
        
        Args:
            ctx: The MCP context
            
        Returns:
            str: Success message or error details
        """
        return editor_action(ctx, "SAVE")