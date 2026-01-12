import socket
import struct
import logging
from typing import Optional
from src.services.config_service import get_rcon_config

# Set up logging
logger = logging.getLogger(__name__)

# RCON Protocol Constants
SERVERDATA_AUTH = 3
SERVERDATA_AUTH_RESPONSE = 2
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_RESPONSE_VALUE = 0


class RconClient:
    """Thread-safe RCON client that doesn't use signals."""
    
    def __init__(self, host: str, password: str, port: int = 25575, timeout: int = 10):
        self.host = host
        self.password = password
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.request_id = 0
    
    def connect(self):
        """Establish connection and authenticate."""
        try:
            # Create socket with timeout
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            
            # Authenticate
            self._send_packet(SERVERDATA_AUTH, self.password)
            response = self._receive_packet()
            
            if response[0] == -1:
                raise Exception("Authentication failed - invalid password")
            
            logger.debug(f"Connected and authenticated to {self.host}:{self.port}")
            
        except socket.timeout:
            raise Exception("Connection timeout")
        except ConnectionRefusedError:
            raise Exception("Connection refused")
        except Exception as e:
            if self.socket:
                self.socket.close()
            raise
    
    def command(self, cmd: str) -> str:
        """Send a command and return the response."""
        if not self.socket:
            raise Exception("Not connected")
        
        try:
            self._send_packet(SERVERDATA_EXECCOMMAND, cmd)
            response = self._receive_packet()
            return response[1].decode('utf-8', errors='ignore')
        except socket.timeout:
            raise Exception("Command timeout")
    
    def disconnect(self):
        """Close the connection."""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.socket = None
    
    def _send_packet(self, packet_type: int, payload: str):
        """Send an RCON packet."""
        self.request_id += 1
        payload_bytes = payload.encode('utf-8')
        
        # Packet structure: ID (4 bytes) + Type (4 bytes) + Payload + 2 null bytes
        packet = struct.pack('<ii', self.request_id, packet_type) + payload_bytes + b'\x00\x00'
        length = struct.pack('<i', len(packet))
        
        self.socket.sendall(length + packet)
    
    def _receive_packet(self):
        """Receive an RCON packet."""
        # Read length (4 bytes)
        length_data = self._recv_exact(4)
        length = struct.unpack('<i', length_data)[0]
        
        # Read packet data
        packet_data = self._recv_exact(length)
        
        # Parse packet: ID (4 bytes) + Type (4 bytes) + Payload (rest - 2 null bytes)
        request_id = struct.unpack('<i', packet_data[:4])[0]
        packet_type = struct.unpack('<i', packet_data[4:8])[0]
        payload = packet_data[8:-2]  # Remove trailing null bytes
        
        return (request_id, payload, packet_type)
    
    def _recv_exact(self, num_bytes: int) -> bytes:
        """Receive exact number of bytes from socket."""
        data = b''
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                raise Exception("Connection closed by server")
            data += chunk
        return data


def run_command(command: str, user_id: Optional[int] = None):
    """Execute a command on the Minecraft server via RCON.
    Creates a fresh connection for each command (thread-safe).
    
    Args:
        command: The RCON command to execute
        user_id: User ID to use their specific server connection
    """
    client = None
    try:
        # Get config for this user
        cfg = get_rcon_config(user_id)
        
        # Create new connection
        logger.debug(f"Connecting to RCON at {cfg['host']}:{cfg['port']}")
        client = RconClient(cfg["host"], cfg["password"], port=cfg["port"], timeout=10)
        client.connect()
        
        # Execute command
        logger.debug(f"Executing command: {command}")
        response = client.command(command)
        
        # Clean disconnect
        client.disconnect()
        logger.debug("Command executed successfully")
        
        return response
        
    except socket.timeout:
        logger.error("RCON connection timed out")
        return "Error: Connection timed out. Is the Minecraft server running?"
        
    except ConnectionRefusedError:
        logger.error("RCON connection refused")
        return "Error: Connection refused. Make sure Minecraft server is running and RCON is enabled."
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"RCON error: {error_msg}")
        
        if "Authentication failed" in error_msg or "invalid password" in error_msg.lower():
            return "Error: Authentication failed. Check RCON password in settings."
        
        if "timeout" in error_msg.lower():
            return "Error: Connection timed out. Is the Minecraft server running?"
        
        if "refused" in error_msg.lower():
            return "Error: Connection refused. Make sure Minecraft server is running and RCON is enabled."
        
        return f"Error: {error_msg}"
        
    finally:
        # Ensure connection is closed
        if client:
            try:
                client.disconnect()
            except Exception:
                pass


def reset_rcon_client(user_id: Optional[int] = None):
    """No-op function kept for backwards compatibility.
    Since we don't pool connections anymore, there's nothing to reset.
    """
    pass


def is_rcon_error(response):
    """Check if RCON response indicates an error."""
    if not response:
        return False
    error_indicators = [
        "Error:",
        "Unknown command",
        "No player was found",
        "Unable to modify",
        "Invalid",
        "Incorrect argument",
        "Expected",
        "Cannot",
        "Failed",
    ]
    return any(indicator in response for indicator in error_indicators)


def parse_rcon_response(response):
    """Parse RCON response and return structured result.
    
    Returns:
        dict with 'success', 'message', and 'data' keys
    """
    if not response or response.strip() == "":
        return {"success": True, "message": "Command executed", "data": None}
    
    if is_rcon_error(response):
        return {"success": False, "message": response, "data": None}
    
    return {"success": True, "message": response, "data": response}


def get_online_players(user_id: Optional[int] = None):
    """Get list of online players for a specific user's server"""
    try:
        response = run_command("list", user_id)
        
        # Handle errors silently
        if not response or "Error" in response:
            logger.debug("Could not get player list, returning empty")
            return []
        
        # Parse response like "There are 2 of a max of 20 players online: player1, player2"
        if "online:" in response:
            players_str = response.split("online:")[1].strip()
            if players_str:
                return [p.strip() for p in players_str.split(",")]
        
        return []
        
    except Exception as e:
        # Fail gracefully - don't block the application
        logger.debug(f"Exception getting online players: {e}")
        return []