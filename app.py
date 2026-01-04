from flask import Flask, render_template, request, redirect, url_for, jsonify
from rcon_client import run_command, get_online_players
from commands import ITEMS, VILLAGE_TYPES
import json
import os

app = Flask(__name__)

# Load configurations from JSON files
def load_json_config(filename):
    config_path = os.path.join(os.path.dirname(__file__), 'config', filename)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

# Load locations and kits
LOCATIONS_CONFIG = load_json_config('locations.json')
KITS_CONFIG = load_json_config('kits.json')

@app.route("/")
def dashboard():
    players = get_online_players()
    return render_template("dashboard.html", 
                         players=players,
                         items=ITEMS,
                         village_types=VILLAGE_TYPES,
                         locations=LOCATIONS_CONFIG.get('locations', []),
                         kits=KITS_CONFIG.get('kits', []))

@app.route("/diagnostics")
def diagnostics():
    """RCON diagnostics page"""
    return render_template("diagnostics.html")

@app.route("/api/players")
def api_players():
    """API endpoint to refresh player list"""
    players = get_online_players()
    return jsonify({"players": players, "count": len(players)})

@app.route("/api/test-connection")
def test_connection():
    """Test RCON connection and return diagnostics"""
    from rcon_client import RCON_HOST, RCON_PORT, RCON_PASSWORD
    
    result = run_command("list")
    
    diagnostics = {
        "host": RCON_HOST,
        "port": RCON_PORT,
        "password_set": bool(RCON_PASSWORD and RCON_PASSWORD.strip()),
        "password_length": len(RCON_PASSWORD) if RCON_PASSWORD else 0,
        "response": result,
        "connected": not result.startswith("Error")
    }
    
    return jsonify(diagnostics)

@app.route("/command", methods=["POST"])
def execute_command():
    """Execute any Minecraft command"""
    cmd = request.form.get("command")
    player = request.form.get("player")
    
    if player and "@p" in cmd:
        cmd = cmd.replace("@p", player)
    elif player and not any(x in cmd for x in ["@p", "@a", "@s"]):
        # If command doesn't have a selector, try to add player name
        if cmd.startswith("/"):
            cmd = f"{cmd} {player}"
    
    result = run_command(cmd)
    return jsonify({"success": True, "result": result})

@app.route("/tp", methods=["POST"])
def teleport():
    print("\n=== TELEPORT REQUEST ===")
    player = request.form.get("player")
    location_id = request.form.get("location_id")
    print(f"Player: {player}")
    print(f"Location ID: {location_id}")
    
    # Find location in config
    locations = LOCATIONS_CONFIG.get('locations', [])
    location = next((loc for loc in locations if loc['id'] == location_id), None)
    
    if location:
        coords = location['coordinates']
        cmd = f"/tp {player} {coords['x']} {coords['y']} {coords['z']}"
        print(f"Executing command: {cmd}")
        result = run_command(cmd)
        print(f"RCON result: {result}")
        return jsonify({"success": True, "result": result})
    else:
        print(f"ERROR: Location not found: {location_id}")
        return jsonify({"success": False, "error": "Location not found"})

@app.route("/give", methods=["POST"])
def give_item():
    print("\n=== GIVE ITEM REQUEST ===")
    player = request.form.get("player")
    item = request.form.get("item")
    amount = request.form.get("amount", 1)
    print(f"Player: {player}")
    print(f"Item: {item}")
    print(f"Amount: {amount}")
    cmd = f"/give {player} minecraft:{item} {amount}"
    print(f"Executing command: {cmd}")
    result = run_command(cmd)
    print(f"RCON result: {result}")
    return jsonify({"success": True, "result": result})

@app.route("/locate", methods=["POST"])
def locate_village():
    player = request.form["player"]
    village_type = request.form["village_type"]
    result = run_command(f"/execute as {player} run locate structure minecraft:village_{village_type}")
    return jsonify({"success": True, "result": result})

@app.route("/quick-command", methods=["POST"])
def quick_command():
    """Execute quick gameplay commands"""
    print("\n=== QUICK COMMAND REQUEST ===")
    player = request.form.get("player")
    command_type = request.form.get("command_type")
    print(f"Player: {player}")
    print(f"Command Type: {command_type}")
    
    commands_map = {
        "gamemode_survival": f"/gamemode survival {player}",
        "gamemode_creative": f"/gamemode creative {player}",
        "gamemode_adventure": f"/gamemode adventure {player}",
        "heal": f"/effect give {player} minecraft:instant_health 1 10",
        "feed": f"/effect give {player} minecraft:saturation 1 10",
        "clear_inventory": f"/clear {player}",
        "day": "/time set day",
        "night": "/time set night",
        "clear_weather": "/weather clear",
        "rain": "/weather rain",
        "thunder": "/weather thunder",
        "give_xp": f"/xp add {player} 1000",
        "fly_enable": f"/effect give {player} minecraft:levitation 1000000 255 true",
        "fly_disable": f"/effect clear {player} minecraft:levitation",
        "speed": f"/effect give {player} minecraft:speed 600 2",
        "jump_boost": f"/effect give {player} minecraft:jump_boost 600 2",
        "night_vision": f"/effect give {player} minecraft:night_vision 600 0",
        "water_breathing": f"/effect give {player} minecraft:water_breathing 600 0",
        "fire_resistance": f"/effect give {player} minecraft:fire_resistance 600 0",
        "clear_effects": f"/effect clear {player}",
        "full_health": f"/effect give {player} minecraft:regeneration 10 255",
    }
    
    cmd = commands_map.get(command_type)
    if cmd:
        print(f"Executing command: {cmd}")
        result = run_command(cmd)
        print(f"RCON result: {result}")
        return jsonify({"success": True, "result": result})
    
    print(f"ERROR: Unknown command type: {command_type}")
    return jsonify({"success": False, "error": "Unknown command"})

@app.route("/kit/<kit_id>", methods=["POST"])
def give_kit(kit_id):
    print("\n=== GIVE KIT REQUEST ===")
    player = request.form.get("player")
    print(f"Player: {player}")
    print(f"Kit ID: {kit_id}")
    
    # Find kit in config
    kits = KITS_CONFIG.get('kits', [])
    kit = next((k for k in kits if k['id'] == kit_id), None)
    
    if kit:
        print(f"Found kit: {kit['name']}")
        results = []
        for item_data in kit['items']:
            cmd = f"/give {player} minecraft:{item_data['item']} {item_data['amount']}"
            print(f"Executing: {cmd}")
            result = run_command(cmd)
            print(f"Result: {result}")
            results.append(result)
        return jsonify({"success": True, "results": results})
    
    print(f"ERROR: Kit not found: {kit_id}")
    return jsonify({"success": False, "error": "Kit not found"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5090, debug=True)
