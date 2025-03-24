# config.py
"""
Configuration settings for the Godot MCP Server.
This file contains all configurable parameters for the server.
"""

from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Main configuration class for the MCP server."""
    
    # Network settings
    godot_host: str = "localhost"
    godot_port: int = 6400
    mcp_port: int = 6500
    
    # Connection settings
    connection_timeout: float = 300.0  # 5 minutes timeout
    buffer_size: int = 1024 * 1024  # 1MB buffer for localhost
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Server settings
    max_retries: int = 3
    retry_delay: float = 1.0

# Create a global config instance
config = ServerConfig()