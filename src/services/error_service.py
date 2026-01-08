"""Error logging service."""
from src.database import get_db


def log_error(command_type, command, error_message, player=None, endpoint=None):
    """Log command errors to database for debugging and monitoring."""
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO error_logs (command_type, command, error_message, player, endpoint)
            VALUES (?, ?, ?, ?, ?)
            """,
            (command_type, command, error_message, player, endpoint),
        )
        db.commit()
        print(f"[ERROR_LOG] {command_type}: {error_message}")
    except Exception as e:
        print(f"Failed to log error: {e}")


def get_error_logs(limit=50):
    """Retrieve recent error logs."""
    db = get_db()
    rows = db.execute(
        """
        SELECT id, timestamp, command_type, command, error_message, player, endpoint
        FROM error_logs
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    return [
        {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "command_type": row["command_type"],
            "command": row["command"],
            "error_message": row["error_message"],
            "player": row["player"],
            "endpoint": row["endpoint"],
        }
        for row in rows
    ]


def clear_error_logs():
    """Clear all error logs."""
    db = get_db()
    db.execute("DELETE FROM error_logs")
    db.commit()
