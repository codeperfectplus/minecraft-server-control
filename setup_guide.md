# Minecraft Server Control Panel - Setup Guide

## Features ✨

- 🎮 **Real-time Player Management**: Auto-refreshing player list with select dropdowns
- 🎁 **Give Items**: Quick item giving with organized categories (Food, Tools, Utilities, Resources, Special)
- 📦 **Quick Kits**: Pre-configured item bundles (Starter, Tools, Explorer, Resources)
- 🗺️ **Teleportation**: Quick teleport to saved locations
- 🏘️ **Village Finder**: Locate different village types (Plains, Desert, Savanna, Taiga, Snowy)
- ⚡ **Custom Commands**: Execute any Minecraft command
- 🎨 **Modern UI**: Beautiful Tailwind CSS interface with icons
- 🔄 **Auto-refresh**: Player list updates every 10 seconds

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure RCON

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your Minecraft server RCON details:
```
RCON_HOST=localhost      # Your Minecraft server IP
RCON_PORT=25575          # RCON port (default 25575)
RCON_PASSWORD=your_password_here
```

### 3. Enable RCON on Your Minecraft Server

Edit your Minecraft server's `server.properties`:
```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_password_here
broadcast-rcon-to-ops=true
```

Restart your Minecraft server after making these changes.

### 4. Run the Application

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## Usage Guide

### Player Selection
- Click the "Refresh" button in the top-right to update the player list
- Player list auto-refreshes every 10 seconds
- Select a player from any dropdown to target them with commands

### Give Items
1. Select a player from the dropdown
2. Set the amount (1-64)
3. Click on any item button to give it to the player
4. Items are organized by category for easy access

### Quick Kits
Pre-configured item bundles:
- **Starter Kit**: Food, torches, ender pearls, compass, shield
- **Tools Kit**: Full set of diamond tools
- **Explorer Kit**: Everything needed for exploration
- **Resources Kit**: Raw materials and gems

### Teleport
- Select a player
- Click on a preset location to teleport them
- Locations include: Base, Villages, Ice Area

### Find Villages
- Select a player
- Click on a village type to locate the nearest one
- The coordinates will appear below

### Custom Commands
- Select a player (optional)
- Type any Minecraft command
- Use `@p` to reference the selected player
- Examples:
  - `/gamemode creative @p`
  - `/time set day`
  - `/weather clear`

## Customization

### Adding New Locations
Edit `commands.py` and add to the `PRESETS` dictionary:
```python
PRESETS = {
    "my_location": "X Y Z",  # Replace with your coordinates
}
```

### Adding New Items
Edit `commands.py` and add to the `ITEMS` dictionary:
```python
"Category": [
    {"name": "item_id", "display": "Display Name", "icon": "🎮"},
]
```

### Modifying Kits
Edit `app.py` in the `give_kit` function to customize kit contents.

## Troubleshooting

### "Failed to refresh players"
- Check that your Minecraft server is running
- Verify RCON is enabled in `server.properties`
- Confirm RCON password matches in `.env` file
- Check that port 25575 is not blocked by firewall

### "Error: Connection refused"
- Ensure RCON_HOST points to your server IP
- Check that RCON_PORT is correct (default 25575)
- Verify the Minecraft server is running

### Players not appearing in dropdown
- Click the "Refresh" button manually
- Check that players are actually online in Minecraft
- Verify RCON connection is working

## Security Notes

⚠️ **Important Security Considerations:**
- Never expose this application directly to the internet without authentication
- Keep your RCON password secure
- Consider using a reverse proxy with authentication (nginx, Apache)
- Use environment variables for sensitive configuration
- Run behind a VPN or firewall

## Tips

- Use the auto-refresh feature to keep player lists updated
- Quick kits save time for common item combinations
- Custom commands support all vanilla Minecraft commands
- Keep your preset locations updated in `commands.py`
- The app works great on mobile devices too!

## Support

For issues or questions:
1. Check that RCON is properly configured
2. Verify your `.env` file has correct credentials
3. Check the terminal for error messages
4. Ensure Python dependencies are installed

Enjoy managing your Minecraft server! 🎮✨
