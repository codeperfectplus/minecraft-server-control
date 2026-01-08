"""User model for authentication."""
from flask_login import UserMixin
from src.database import get_db


class User(UserMixin):
    """User model for Flask-Login."""
    
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role
    
    @staticmethod
    def get(user_id):
        """Get user by ID."""
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?", (int(user_id),)).fetchone()
        if not user:
            return None
        return User(id=user['id'], username=user['username'], role=user['role'])
