# tools/editor_tools.py
from mcp.server.fastmcp import FastMCP, Context, Image
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

    @mcp.tool()
    def capture_screenshot(ctx: Context, path: Optional[str] = None) -> Image:
        """Capture a screenshot of the Godot editor viewport.

        Args:
            ctx: The MCP context
            path: Optional file path to save the PNG (default: user://screenshot.png)

        Returns:
            Image: The captured screenshot as an image
        """
        try:
            params = {}
            if path is not None:
                params["path"] = path
            response = get_godot_connection().send_command("CAPTURE_SCREENSHOT", params)
            if "error" in response:
                raise RuntimeError(response["error"])
            return Image(path=response["path"])
        except Exception as e:
            raise RuntimeError(f"Error capturing screenshot: {str(e)}")

    @mcp.tool()
    def send_game_input(ctx: Context, command: str) -> str:
        """Send input commands to the running Godot game.

        Commands:
            move <direction> <steps> - Move player (left/right/up/down, default 1 step)
            interact - Press the interact button

        Examples:
            "move left 5" - move left 5 tiles
            "move up 3" - move up 3 tiles
            "interact" - interact with facing entity

        Args:
            ctx: The MCP context
            command: The input command string

        Returns:
            str: Success message or error details
        """
        try:
            parts = command.strip().split()
            if not parts:
                return "Error: Empty command"
            if parts[0] == "interact":
                if len(parts) != 1:
                    return "Error: 'interact' takes no arguments"
            elif parts[0] == "move":
                valid_directions = {"left", "right", "up", "down"}
                if len(parts) < 2 or parts[1] not in valid_directions:
                    return f"Error: 'move' requires a direction: {', '.join(sorted(valid_directions))}"
                if len(parts) == 3:
                    if not parts[2].isdigit() or int(parts[2]) <= 0:
                        return "Error: steps must be a positive integer"
                elif len(parts) > 3:
                    return "Error: 'move' takes at most 2 arguments: direction and steps"
            else:
                return f"Error: Unknown command '{parts[0]}'. Valid commands: move, interact"

            response = get_godot_connection().send_command("SEND_INPUT", {"command": command})
            if "error" in response:
                return f"Error: {response['error']}"
            return response.get("message", "Input sent")
        except Exception as e:
            return f"Error sending game input: {str(e)}"