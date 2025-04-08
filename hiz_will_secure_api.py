
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import hashlib
import os

app = Flask(_name_, static_folder='static')

@app.route("/")
def home():
    return "Welcome to Hizwill Medical Charting!"
DB_PATH = 'hiz_will_system.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'hiz_will_login_secure.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory(app.static_folder, 'hiz_will_dashboard_loggedin.html')

@app.route('/admin')
def admin():
    return send_from_directory(app.static_folder, 'hiz_will_admin_dashboard.html')

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, role, created_at FROM users').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    password_hash = hash_password(password)

    conn = get_db_connection()
    user = conn.execute('SELECT id, username, role FROM users WHERE username = ? AND password_hash = ?',
                        (username, password_hash)).fetchone()
    conn.close()

    if user:
        return jsonify(dict(user)), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'medtech')
    password_hash = hash_password(password)

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                     (username, password_hash, role))
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 400
    finally:
        conn.close()

@app.route('/api/residents', methods=['GET'])
def get_residents():
    conn = get_db_connection()
    residents = conn.execute('SELECT * FROM residents WHERE active = 1').fetchall()
    conn.close()
    return jsonify([dict(resident) for resident in residents])

@app.route('/api/chart', methods=['POST'])
def add_chart_entry():
    data = request.json
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO medication_charts (user_id, resident_id, date_time, medication, dosage, vitals, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['user_id'], data['resident_id'], data['date_time'], data['medication'], data['dosage'], data['vitals'], data['notes']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Chart entry added'}), 201

@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    data = request.json
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO attendance (user_id, clock_in, clock_out)
        VALUES (?, ?, ?)
    ''', (data['user_id'], data['clock_in'], data['clock_out']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Attendance recorded'}), 201

if __name__ == '__main__':
    app.run(debug=True)
