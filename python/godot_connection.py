# godot_connection.py
import socket
import json
import logging
from dataclasses import dataclass
from typing import Dict, Any
from config import config

# Configure logging using settings from config
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format=config.log_format
)
logger = logging.getLogger("GodotMCP")

@dataclass
class GodotConnection:
    """Manages the socket connection to the Godot Editor."""
    host: str = config.godot_host
    port: int = config.godot_port
    sock: socket.socket = None  # Socket for Godot communication

    def connect(self) -> bool:
        """Establish a connection to the Godot Editor."""
        if self.sock:
            return True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Godot at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Godot: {str(e)}")
            self.sock = None
            return False

    def disconnect(self):
        """Close the connection to the Godot Editor."""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Godot: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=config.buffer_size) -> bytes:
        """Receive a complete response from Godot, handling chunked data."""
        chunks = []
        sock.settimeout(config.connection_timeout)  # Use timeout from config
        try:
            while True:
                chunk = sock.recv(buffer_size)
                if not chunk:
                    if not chunks:
                        raise Exception("Connection closed before receiving data")
                    break
                chunks.append(chunk)
                
                # Process the data received so far
                data = b''.join(chunks)
                decoded_data = data.decode('utf-8')
                
                # Check if we've received a complete response
                try:
                    # Special case for ping-pong
                    if decoded_data.strip().startswith('{"status":"success","result":{"message":"pong"'):
                        logger.debug("Received ping response")
                        return data
                    
                    # Validate JSON format
                    json.loads(decoded_data)
                    
                    # If we get here, we have valid JSON
                    logger.info(f"Received complete response ({len(data)} bytes)")
                    return data
                except json.JSONDecodeError:
                    # We haven't received a complete valid JSON response yet
                    continue
                except Exception as e:
                    logger.warning(f"Error processing response chunk: {str(e)}")
                    # Continue reading more chunks as this might not be the complete response
                    continue
        except socket.timeout:
            logger.warning("Socket timeout during receive")
            raise Exception("Timeout receiving Godot response")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise


    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Godot and return its response."""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Godot")
        
        # Special handling for ping command
        if command_type == "ping":
            try:
                logger.debug("Sending ping to verify connection")
                ping_command = json.dumps({"type": "ping", "params": {}}).encode('utf-8')
                self.sock.sendall(ping_command)
                response_data = self.receive_full_response(self.sock)
                
                if not response_data:
                    logger.warning("Received empty ping response")
                    self.sock = None
                    raise ConnectionError("Empty ping response")
                    
                response = json.loads(response_data.decode('utf-8'))
                
                if not response or response.get("status") != "success":
                    logger.warning(f"Ping response was not successful: {response}")
                    self.sock = None
                    raise ConnectionError("Connection verification failed")
                    
                return {"message": "pong"}
            except Exception as e:
                logger.error(f"Ping error: {str(e)}")
                self.sock = None
                raise ConnectionError(f"Connection verification failed: {str(e)}")
        
        # Normal command handling
        command = {"type": command_type, "params": params or {}}
        try:
            logger.info(f"Sending command: {command_type} with params: {params}")
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            response_data = self.receive_full_response(self.sock)
            
            if not response_data:
                logger.warning(f"Received empty response for command: {command_type}")
                raise Exception("Empty response from Godot")
                
            response = json.loads(response_data.decode('utf-8'))
            
            if not response:
                logger.warning(f"Failed to parse response JSON for command: {command_type}")
                raise Exception("Invalid JSON response from Godot")
                
            if response.get("status") == "error":
                error_message = response.get("error") or response.get("message", "Unknown Godot error")
                logger.error(f"Godot error: {error_message}")
                raise Exception(error_message)
            
            result = response.get("result")
            if result is None:
                logger.warning(f"Response missing 'result' field for command: {command_type}")
                return {}
                
            return result
        except Exception as e:
            logger.error(f"Communication error with Godot: {str(e)}")
            self.sock = None
            raise Exception(f"Failed to communicate with Godot: {str(e)}")
    
# Global Godot connection
_godot_connection = None

def get_godot_connection() -> GodotConnection:
    """Retrieve or establish a persistent Godot connection."""
    global _godot_connection
    if _godot_connection is not None:
        try:
            # Try to ping with a short timeout to verify connection
            result = _godot_connection.send_command("ping")
            # If we get here, the connection is still valid
            logger.debug("Reusing existing Godot connection")
            return _godot_connection
        except Exception as e:
            logger.warning(f"Existing connection failed: {str(e)}")
            try:
                _godot_connection.disconnect()
            except:
                pass
            _godot_connection = None
    
    # Create a new connection
    logger.info("Creating new Godot connection")
    _godot_connection = GodotConnection()
    if not _godot_connection.connect():
        _godot_connection = None
        raise ConnectionError("Could not connect to Godot. Ensure the Godot Editor and MCP Bridge are running.")
    
    try:
        # Verify the new connection works
        _godot_connection.send_command("ping")
        logger.info("Successfully established new Godot connection")
        return _godot_connection
    except Exception as e:
        logger.error(f"Could not verify new connection: {str(e)}")
        try:
            _godot_connection.disconnect()
        except:
            pass
        _godot_connection = None
        raise ConnectionError(f"Could not establish valid Godot connection: {str(e)}")