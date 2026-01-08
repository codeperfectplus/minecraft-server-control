"""Location management service."""
from src.database import get_db
from src.config_loader import load_json_config


def seed_locations_if_empty():
    """Seed locations from config if database is empty."""
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
    if count == 0:
        seed = load_json_config('locations.json').get('locations', [])
        for loc in seed:
            coords = loc.get('coordinates', {})
            db.execute(
                "INSERT OR REPLACE INTO locations (id, name, icon, description, x, y, z) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    loc.get('id'),
                    loc.get('name'),
                    loc.get('icon', 'map-marker-alt'),
                    loc.get('description', ''),
                    int(coords.get('x', 0)),
                    int(coords.get('y', 0)),
                    int(coords.get('z', 0)),
                ),
            )
        db.commit()


def fetch_locations():
    """Get all locations from database."""
    db = get_db()
    rows = db.execute(
        "SELECT id, name, icon, description, x, y, z FROM locations ORDER BY name"
    ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "icon": row["icon"],
            "description": row["description"],
            "coordinates": {"x": row["x"], "y": row["y"], "z": row["z"]},
        }
        for row in rows
    ]


def upsert_location(data):
    """Create or update a location."""
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO locations (id, name, icon, description, x, y, z) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data["id"],
            data["name"],
            data.get("icon", "map-marker-alt"),
            data.get("description", ""),
            int(data["x"]),
            int(data["y"]),
            int(data["z"]),
        ),
    )
    db.commit()


def delete_location(loc_id):
    """Delete a location by ID."""
    db = get_db()
    db.execute("DELETE FROM locations WHERE id = ?", (loc_id,))
    db.commit()
