"""Authentication routes."""
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from src.database import get_db
from src.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user_data = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], username=user_data['username'], role=user_data['role'])
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/admin/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    """Admin user management."""
    if current_user.role != 'admin':
        flash('Access denied: Admin only')
        return redirect(url_for('main.dashboard'))
    
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            username = request.form['username']
            password = request.form['password']
            role = request.form.get('role', 'user')
            
            try:
                db.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), role)
                )
                db.commit()
                flash(f'User {username} created successfully')
            except sqlite3.IntegrityError:
                flash(f'Username {username} already exists')
        elif action == 'delete':
            user_id = request.form['user_id']
            if int(user_id) == current_user.id:
                flash('Cannot delete yourself')
            else:
                db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                db.commit()
                flash('User deleted')
            
    users = db.execute("SELECT id, username, role FROM users").fetchall()
    return render_template('manage_users.html', users=users)
