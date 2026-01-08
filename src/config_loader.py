"""Configuration loading utilities."""
import json
import os


def load_json_config(filename):
    """Load JSON configuration file from the config directory."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', filename)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON config file: {config_path}")
        return {}


def get_kits():
    """Load kits configuration."""
    return load_json_config('kits.json')


def get_quick_commands():
    """Load quick commands configuration."""
    commands = load_json_config('quick_commands.json')
    print(f"Loaded {len(commands) if isinstance(commands, list) else 0} quick commands.")
    return commands
