from mcrcon import MCRcon
import os
import socket
import signal
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

RCON_HOST = os.getenv("RCON_HOST", "localhost")
RCON_PORT = int(os.getenv("RCON_PORT", "25575"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD", "")

# Monkey-patch signal.signal to avoid threading issues
original_signal = signal.signal
def safe_signal(signalnum, handler):
    """Only allow signal handling in main thread"""
    if threading.current_thread() is threading.main_thread():
        return original_signal(signalnum, handler)
    return None

signal.signal = safe_signal

def run_command(command):
    """Execute a command on the Minecraft server via RCON"""
    mcr = None
    try:
        # Create connection and set socket timeout directly
        mcr = MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT)
        # Override the socket before connecting to avoid signal usage
        mcr.connect()
        response = mcr.command(command)
        return response
    except socket.timeout:
        return "Error: Connection timed out. Is the Minecraft server running?"
    except ConnectionRefusedError:
        return "Error: Connection refused. Make sure Minecraft server is running and RCON is enabled."
    except Exception as e:
        error_msg = str(e)
        if "Authentication failed" in error_msg or "Login failed" in error_msg:
            return "Error: Authentication failed. Check RCON password in .env file."
        return f"Error: {error_msg}"
    finally:
        if mcr:
            try:
                mcr.disconnect()
            except:
                pass

def get_online_players():
    """Get list of online players"""
    try:
        response = run_command("list")
        # Parse response like "There are 2 of a max of 20 players online: player1, player2"
        if "Error" in response:
            print(f"RCON Error: {response}")
            return []
        if "online:" in response:
            players_str = response.split("online:")[1].strip()
            if players_str:
                return [p.strip() for p in players_str.split(",")]
        return []
    except Exception as e:
        print(f"Exception getting players: {e}")
        return []
