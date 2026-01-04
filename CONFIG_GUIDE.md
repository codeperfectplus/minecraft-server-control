# Configuration Guide

## Adding/Editing Teleport Locations

Edit `config/locations.json`:

```json
{
  "locations": [
    {
      "id": "my_location",           // Unique identifier
      "name": "My Location",          // Display name
      "icon": "home",                 // FontAwesome icon (without 'fa-')
      "coordinates": {
        "x": 100,
        "y": 64,
        "z": 200
      },
      "description": "My custom location"
    }
  ]
}
```

### Available Icons:
- `home` - House
- `city` - Buildings
- `snowflake` - Snow
- `tree` - Tree
- `mountain` - Mountain
- `dungeon` - Dungeon
- `church` - Temple
- `monument` - Monument
- `fort-awesome` - Fortress
- `landmark` - Landmark

## Adding/Editing Kits

Edit `config/kits.json`:

```json
{
  "kits": [
    {
      "id": "my_kit",               // Unique identifier
      "name": "My Kit",              // Display name
      "icon": "box",                 // FontAwesome icon
      "color": "green",              // Tailwind color: green, blue, yellow, purple, red, etc.
      "description": "My custom kit",
      "items": [
        {"item": "diamond", "amount": 64},
        {"item": "iron_ingot", "amount": 32}
      ]
    }
  ]
}
```

### Available Colors:
- `green`, `blue`, `yellow`, `purple`, `red`, `pink`, `indigo`, `orange`, `teal`

## After Editing:
1. Save the JSON file
2. Restart the Flask app
3. Locations/kits will automatically appear in the UI

## File Structure:
```
mincecraft-app/
├── config/
│   ├── locations.json    # Teleport locations
│   └── kits.json         # Item kits
├── app.py
└── ...
```
