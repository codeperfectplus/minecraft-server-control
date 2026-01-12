"""Chat routes and API."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_from_directory
from flask_login import login_required, current_user
from src.database import get_db
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
@login_required
def index():
    """Main chat interface."""
    return render_template('chat/index.html')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'src', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@chat_bp.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# --- API Endpoints ---

@chat_bp.route('/api/chat/users')
@login_required
def get_users():
    """Get list of discoverable users."""
    db = get_db()
    
    # Simple strategy: Discover = All users NOT current user
    # DMs list will be handled separately or filtered frontend
    
    users = db.execute(
        """
        SELECT u.id, u.username, u.first_name, u.last_name, u.gamer_tag, u.profile_image,
               (SELECT COUNT(*) FROM messages m 
                WHERE m.sender_id = u.id 
                AND m.recipient_id = ? 
                AND m.read = 0) as unread
        FROM users u 
        WHERE u.id != ?
        """,
        (current_user.id, current_user.id)
    ).fetchall()
    
    return jsonify({
        'users': [dict(u) for u in users]
    })

@chat_bp.route('/api/chat/dms')
@login_required
def get_dms():
    """Get users with active DM history."""
    db = get_db()
    users = db.execute(
        """
        SELECT DISTINCT u.id, u.username, u.first_name, u.last_name, u.gamer_tag, u.profile_image,
               (SELECT COUNT(*) FROM messages m 
                WHERE m.sender_id = u.id 
                AND m.recipient_id = ? 
                AND m.read = 0) as unread
        FROM users u
        JOIN messages m ON (m.sender_id = u.id AND m.recipient_id = ?) 
                        OR (m.sender_id = ? AND m.recipient_id = u.id)
        WHERE u.id != ?
        """,
        (current_user.id, current_user.id, current_user.id, current_user.id)
    ).fetchall()
    
    return jsonify({
        'dms': [dict(u) for u in users]
    })

@chat_bp.route('/api/chat/groups')
@login_required
def get_groups():
    """Get groups the current user is a member of."""
    db = get_db()
    groups = db.execute(
        """
        SELECT g.id, g.name, g.created_by, g.image_url,
               (SELECT COUNT(*) FROM messages m 
                WHERE m.group_id = g.id 
                AND m.timestamp > gm.last_read_at) as unread
        FROM chat_groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ?
        """,
        (current_user.id,)
    ).fetchall()
    
    
    return jsonify({
        'groups': [dict(g) for g in groups]
    })


@chat_bp.route('/api/chat/groups/<int:group_id>/members')
@login_required
def get_group_members(group_id):
    """Get members of a group."""
    db = get_db()
    
    # Check if current user is member
    member = db.execute(
        "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, current_user.id)
    ).fetchone()
    if not member:
        return jsonify({'error': 'Not a member of this group'}), 403
        
    members = db.execute(
        """
        SELECT u.id, u.username, u.first_name, u.last_name, u.gamer_tag 
        FROM group_members gm
        JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = ?
        """,
        (group_id,)
    ).fetchall()
    
    return jsonify({
        'members': [dict(m) for m in members]
    })

@chat_bp.route('/api/chat/messages', methods=['GET'])
@login_required
def get_messages():
    """Get messages for a specific conversation."""
    target_id = request.args.get('target_id') # user_id or group_id
    is_group = request.args.get('is_group') == 'true'
    
    if not target_id:
        return jsonify({'error': 'Missing target_id'}), 400
        
    db = get_db()
    messages = []
    
    if is_group:
        # Check membership
        member = db.execute(
            "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
            (target_id, current_user.id)
        ).fetchone()
        if not member:
            return jsonify({'error': 'Not a member of this group'}), 403
            
        messages = db.execute(
            """
            SELECT m.id, m.sender_id, u.username, u.gamer_tag, m.content, m.timestamp, m.type
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.group_id = ?
            ORDER BY m.timestamp ASC
            """,
            (target_id,)
        ).fetchall()
    else:
        # 1-on-1 chat
        messages = db.execute(
            """
            SELECT m.id, m.sender_id, u.username, u.gamer_tag, m.content, m.timestamp, m.type
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.recipient_id = ?)
            OR (m.sender_id = ? AND m.recipient_id = ?)
            ORDER BY m.timestamp ASC
            """,
            (current_user.id, target_id, target_id, current_user.id)
        ).fetchall()
        
    # Mark messages as read
    if is_group:
        db.execute(
            "UPDATE group_members SET last_read_at = CURRENT_TIMESTAMP WHERE group_id = ? AND user_id = ?",
            (target_id, current_user.id)
        )
    else:
        db.execute(
            "UPDATE messages SET read = 1 WHERE sender_id = ? AND recipient_id = ?",
            (target_id, current_user.id)
        )
    db.commit()
    
    return jsonify({
        'messages': [dict(m) for m in messages],
        'current_user_id': current_user.id
    })

@chat_bp.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    """Send a message."""
    data = request.json
    content = data.get('content')
    target_id = data.get('target_id')
    is_group = data.get('is_group')
    
    if not content or not target_id:
        return jsonify({'error': 'Missing content or target'}), 400
        
    db = get_db()
    
    if is_group:
         # Check membership
        member = db.execute(
            "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
            (target_id, current_user.id)
        ).fetchone()
        if not member:
            return jsonify({'error': 'Not a member of this group'}), 403
            
        db.execute(
            "INSERT INTO messages (sender_id, group_id, content) VALUES (?, ?, ?)",
            (current_user.id, target_id, content)
        )
    else:
        db.execute(
            "INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)",
            (current_user.id, target_id, content)
        )
        
    db.commit()
    return jsonify({'status': 'sent'})

@chat_bp.route('/api/chat/groups/create', methods=['POST'])
@login_required
def create_group():
    """Create a new group with optional initial members."""
    data = request.json
    name = data.get('name')
    members = data.get('members', []) # List of user IDs
    
    if not name:
        return jsonify({'error': 'Name required'}), 400
        
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO chat_groups (name, created_by) VALUES (?, ?)",
            (name, current_user.id)
        )
        group_id = cursor.lastrowid
        
        # Add creator
        cursor.execute(
            "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, current_user.id)
        )
        
        # Add selected members
        for user_id in members:
            try:
                # Prevent adding self again if selected
                if int(user_id) != current_user.id:
                    cursor.execute(
                        "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
                        (group_id, user_id)
                    )
            except (ValueError, TypeError):
                continue
                
        # Add system message
        cursor.execute(
            "INSERT INTO messages (sender_id, group_id, content, type) VALUES (?, ?, ?, ?)",
            (current_user.id, group_id, 'created the group', 'system')
        )
                
        db.commit()
        return jsonify({'status': 'created', 'group_id': group_id})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/api/chat/groups/join', methods=['POST'])
@login_required
def join_group():
    """Join or add member to group."""
    data = request.json
    group_id = data.get('group_id')
    user_id = data.get('user_id') # if adding someone else
    
    if not group_id:
        return jsonify({'error': 'Missing group_id'}), 400
        
    target_user_id = user_id if user_id else current_user.id
    
    db = get_db()
    
    # Simple check: assuming public groups or invite logic (simplifying to: anyone can add anyone for now per "Chat groups" req)
    try:
        db.execute(
            "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, target_user_id)
        )
        # Add system message
        db.execute(
            "INSERT INTO messages (sender_id, group_id, content, type) VALUES (?, ?, ?, ?)",
            (current_user.id, group_id, f'added {target_user_id}' if target_user_id != current_user.id else 'joined the group', 'system') 
        )
        
        # If adding someone else, we need their username for the message, let's fix that
        # Actually better to just use generic message or fetch username. 
        # Simpler: "added a member" or just use current_user.id as sender and handle text in frontend?
        # Let's fetch the added user's name for clarity if it's an add
        if target_user_id != current_user.id:
            added_user = db.execute("SELECT username, gamer_tag FROM users WHERE id = ?", (target_user_id,)).fetchone()
            if added_user:
                 name_display = added_user['username']
                 if added_user['gamer_tag']:
                     name_display += f" ({added_user['gamer_tag']})"
                     
                 db.execute(
                    "INSERT INTO messages (sender_id, group_id, content, type) VALUES (?, ?, ?, ?)",
                    (current_user.id, group_id, f"added {name_display}", 'system')
                )
        else:
             # Self join logic (if needed in future, currently not exposed as "Join" button for public groups, only add)
             # But good to have
             current_user_data = db.execute("SELECT gamer_tag FROM users WHERE id = ?", (current_user.id,)).fetchone()
             gt = current_user_data['gamer_tag']
             msg = "joined the group"
             if gt:
                 msg = f"joined the group ({gt})" # A bit redundant if username is shown, but fulfills req
             
             db.execute(
                "INSERT INTO messages (sender_id, group_id, content, type) VALUES (?, ?, ?, ?)",
                (current_user.id, group_id, "joined the group", 'system')
            )

        db.commit()
        return jsonify({'status': 'joined'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already a member'}), 400

@chat_bp.route('/api/chat/groups/leave', methods=['POST'])
@login_required
def leave_group():
    """Leave a group."""
    data = request.json
    group_id = data.get('group_id')
    
    if not group_id:
        return jsonify({'error': 'Missing group_id'}), 400
        
    db = get_db()
    
    # Check if member
    member = db.execute(
        "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, current_user.id)
    ).fetchone()
    
    if not member:
        return jsonify({'error': 'Not a member of this group'}), 400
        
    try:
        db.execute(
            "DELETE FROM group_members WHERE group_id = ? AND user_id = ?",
            (group_id, current_user.id)
        )
        # Add system message
        db.execute(
            "INSERT INTO messages (sender_id, group_id, content, type) VALUES (?, ?, ?, ?)",
            (current_user.id, group_id, 'left the group', 'system')
        )

        db.commit()
        return jsonify({'status': 'left'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/api/chat/unread-count')
@login_required
def get_unread_count():
    """Get total unread message count."""
    db = get_db()
    
    # Unread DMs
    dm_count = db.execute(
        "SELECT COUNT(*) FROM messages WHERE recipient_id = ? AND read = 0",
        (current_user.id,)
    ).fetchone()[0]
    
    # Unread Group Messages
    group_count = db.execute(
        """
        SELECT COUNT(*) 
        FROM messages m
        JOIN group_members gm ON m.group_id = gm.group_id
        WHERE gm.user_id = ? 
        AND m.timestamp > gm.last_read_at
        """,
        (current_user.id,)
    ).fetchone()[0]
    
    return jsonify({'count': dm_count + group_count})

@chat_bp.route('/api/chat/upload-image', methods=['POST'])
@login_required
def upload_image():
    """Upload an image for profile or group."""
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['image']
    upload_type = request.form.get('type') # 'profile' or 'group'
    target_id = request.form.get('id') # group_id (if type is group)
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        url = url_for('chat.uploaded_file', filename=filename)
        
        db = get_db()
        if upload_type == 'profile':
            db.execute("UPDATE users SET profile_image = ? WHERE id = ?", (url, current_user.id))
        elif upload_type == 'group' and target_id:
             # Check if admin/creator? For now allow any member
             member = db.execute("SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?", (target_id, current_user.id)).fetchone()
             if member:
                db.execute("UPDATE chat_groups SET image_url = ? WHERE id = ?", (url, target_id))
             else:
                 return jsonify({'error': 'Not authorized'}), 403
        
        db.commit()
        return jsonify({'url': url})
        
    return jsonify({'error': 'Upload failed'}), 500
