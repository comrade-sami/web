from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps

app = Flask(__name__)

# Database setup


def get_db():
    conn = sqlite3.connect('todo.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    with get_db() as db:

        db.execute('DROP TABLE IF EXISTS users')
        db.execute('DROP TABLE IF EXISTS tasks')
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                done BOOLEAN DEFAULT 0,
                user TEXT NOT NULL,
                FOREIGN KEY (user) REFERENCES users(username)
            )
        ''')


init_db()

# Authentication


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return jsonify({"error": "Missing credentials"}), 401

        with get_db() as db:
            user = db.execute(
                'SELECT password_hash FROM users WHERE username = ?',
                (auth.username,)
            ).fetchone()

            if not user or not check_password_hash(user['password_hash'], auth.password):
                return jsonify({"error": "Invalid credentials"}), 401

        return f(*args, **kwargs)
    return decorated

# Validation functions


def validate_password(password):
    if len(password) < 8:
        return {"error": "Password must be at least 8 characters"}, 400
    return None


def validate_description(description):
    if description and len(description) > 16:
        return {"error": "Description cannot exceed 16 characters"}, 400
    return None

# Helper function


def get_current_user():
    return request.authorization.username

# API Endpoints


@app.route('/register', methods=['POST'])
def register():
    # Ensure request has JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Check required fields
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password required"}), 400

    # Validate password
    if error := validate_password(data['password']):
        return jsonify(error[0]), error[1]

    # Register user
    with get_db() as db:
        try:
            db.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (data['username'], generate_password_hash(data['password']))
            )
            db.commit()
            return jsonify({
                "message": "User registered successfully",
                "username": data['username']
            }), 201
        except sqlite3.IntegrityError:
            return jsonify({"error": "Username already exists"}), 400


@app.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    user = get_current_user()
    with get_db() as db:
        tasks = db.execute(
            'SELECT * FROM tasks WHERE user = ?',
            (user,)
        ).fetchall()
        return jsonify({"tasks": [dict(task) for task in tasks]})


@app.route('/tasks', methods=['POST'])
@login_required
def create_task():
    user = get_current_user()
    data = request.json

    if not data or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400

    # Validate description length
    if 'description' in data:
        if error := validate_description(data['description']):
            return jsonify(error[0]), error[1]

    with get_db() as db:
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO tasks (title, description, done, user) VALUES (?, ?, ?, ?)',
            (data['title'], data.get('description'),
             data.get('done', False), user)
        )
        task_id = cursor.lastrowid
        db.commit()

        new_task = db.execute(
            'SELECT * FROM tasks WHERE id = ?',
            (task_id,)
        ).fetchone()

        return jsonify({"task": dict(new_task)}), 201


@app.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    user = get_current_user()
    with get_db() as db:
        task = db.execute(
            'SELECT * FROM tasks WHERE id = ? AND user = ?',
            (task_id, user)
        ).fetchone()

        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"task": dict(task)})


@app.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    user = get_current_user()
    data = request.json

    with get_db() as db:
        # Verify task exists
        if not db.execute(
            'SELECT 1 FROM tasks WHERE id = ? AND user = ?',
            (task_id, user)
        ).fetchone():
            return jsonify({"error": "Task not found"}), 404

        # Validate description if being updated
        if 'description' in data:
            if error := validate_description(data['description']):
                return jsonify(error[0]), error[1]

        # Build update query
        updates = []
        params = []

        if 'title' in data:
            updates.append("title = ?")
            params.append(data['title'])
        if 'description' in data:
            updates.append("description = ?")
            params.append(data['description'])
        if 'done' in data:
            updates.append("done = ?")
            params.append(data['done'])

        if not updates:
            return jsonify({"error": "No fields to update"}), 400

        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"

        db.execute(query, params)
        db.commit()

        updated_task = db.execute(
            'SELECT * FROM tasks WHERE id = ?',
            (task_id,)
        ).fetchone()

        return jsonify({"task": dict(updated_task)})


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    user = get_current_user()
    with get_db() as db:
        result = db.execute(
            'DELETE FROM tasks WHERE id = ? AND user = ?',
            (task_id, user)
        )
        db.commit()

        if result.rowcount == 0:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"message": "Task deleted"})


if __name__ == '__main__':
    app.run(debug=True)
