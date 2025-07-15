# config.py
"""
Configuration settings for the Godot MCP Server.
This file contains all configurable parameters for the server.
"""

from dataclasses import dataclass
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for .env file in the python directory
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, just use system env vars
    pass

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
    
    # Meshy API settings
    # API key loaded from environment variable
    meshy_api_key: str = os.getenv("MESHY_API_KEY")
    meshy_base_url: str = "https://api.meshy.ai/openapi"  # Official API base URL
    meshy_timeout: int = 300  # 5 minutes for mesh generation
    meshy_download_timeout: int = 60  # 1 minute for downloading
    
    # Asset import settings
    asset_import_path: str = "res://assets/generated_meshes/"

# Create a global config instance
config = ServerConfig()