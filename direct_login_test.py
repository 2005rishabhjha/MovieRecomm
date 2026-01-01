"""
Test with traditional form submission (no AJAX)
This bypasses any JavaScript issues
"""
from flask import Flask, render_template_string, request, session, redirect, url_for, flash
import pyodbc
import hashlib

app = Flask(__name__)
app.secret_key = 'direct-test-key-67890'

DB_CONFIG = {
    'server': 'LAPTOP-B0N4O9L6\\MSSQLSERVERDB',
    'database': 'MovieRecommDB',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

def get_db_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Direct Login Test</title>
    <style>
        body { 
            font-family: Arial; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 50px;
            margin: 0;
        }
        .container { 
            max-width: 400px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 { 
            color: #667eea; 
            text-align: center;
            margin-bottom: 10px;
        }
        p { text-align: center; color: #666; margin-bottom: 30px; }
        input { 
            width: 100%; 
            padding: 12px; 
            margin: 10px 0; 
            border: 2px solid #e0e0e0; 
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 14px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button { 
            width: 100%; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            border: none; 
            padding: 14px; 
            border-radius: 8px;
            cursor: pointer; 
            font-size: 16px;
            font-weight: 600;
            margin-top: 10px;
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .message { 
            padding: 12px; 
            border-radius: 8px; 
            margin-bottom: 20px;
            text-align: center;
        }
        .error { background: #fee; color: #c33; border: 1px solid #fcc; }
        .success { background: #efe; color: #3c3; border: 1px solid #cfc; }
        .info { background: #e7f3ff; color: #0066cc; border: 1px solid #b3d9ff; }
        label { 
            display: block;
            color: #333;
            font-weight: 500;
            margin-top: 15px;
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>MOVIERECOMM™</h1>
        <p>Direct Login Test (No JavaScript)</p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="message {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login">
            <label>Username:</label>
            <input type="text" name="username" required autofocus>
            
            <label>Password:</label>
            <input type="password" name="password" required>
            
            <button type="submit">Login</button>
        </form>
        
        <div class="info" style="margin-top: 20px; font-size: 12px;">
            <strong>This is a direct form submission test.</strong><br>
            No JavaScript/AJAX - pure HTML form POST.
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body { 
            font-family: Arial; 
            background: #f5f7fa; 
            padding: 0;
            margin: 0;
        }
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .container { 
            max-width: 1200px; 
            margin: 40px auto; 
            padding: 0 20px;
        }
        .welcome-box {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        h1 { color: #667eea; margin-bottom: 20px; }
        .info { 
            background: #e7f3ff; 
            padding: 20px; 
            border-radius: 10px;
            margin: 20px 0;
        }
        button { 
            background: #667eea;
            color: white; 
            border: none; 
            padding: 12px 30px; 
            border-radius: 8px;
            cursor: pointer; 
            font-size: 16px;
            margin-top: 20px;
        }
        button:hover { background: #5568d3; }
    </style>
</head>
<body>
    <div class="navbar">
        <h2 style="margin: 0;">MOVIERECOMM™ Dashboard</h2>
    </div>
    
    <div class="container">
        <div class="welcome-box">
            <h1>🎉 Welcome, {{ username }}!</h1>
            <p style="font-size: 18px; color: #666;">You have successfully logged in!</p>
            
            <div class="info">
                <p><strong>User ID:</strong> {{ user_id }}</p>
                <p><strong>Username:</strong> {{ username }}</p>
                <p><strong>Email:</strong> {{ email }}</p>
            </div>
            
            <p style="color: #3c3; font-weight: bold;">✓ Session is working correctly!</p>
            
            <form method="GET" action="/logout">
                <button type="submit">Logout</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    print(f"\n=== INDEX: Session = {dict(session)}")
    if 'user_id' in session:
        return render_template_string(
            DASHBOARD_TEMPLATE,
            username=session['username'],
            user_id=session['user_id'],
            email=session.get('email', 'N/A')
        )
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        print("Already logged in, redirecting to dashboard")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        print("\n=== LOGIN POST ===")
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password)}")
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template_string(LOGIN_TEMPLATE)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            password_hash = hash_password(password)
            
            print(f"Querying database...")
            cursor.execute(
                "SELECT user_id, username, email FROM Users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )
            user = cursor.fetchone()
            conn.close()
            
            if user:
                print(f"✓ USER FOUND: {user[1]} (ID: {user[0]})")
                
                # Set session
                session.clear()
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['email'] = user[2]
                session.permanent = True
                
                print(f"✓ Session set: {dict(session)}")
                flash('Login successful!', 'success')
                
                print("✓ Redirecting to dashboard...")
                return redirect(url_for('index'))
            else:
                print("✗ Invalid credentials")
                flash('Invalid username or password', 'error')
                return render_template_string(LOGIN_TEMPLATE)
                
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Error: {str(e)}', 'error')
            return render_template_string(LOGIN_TEMPLATE)
    
    # GET request
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    print(f"\n=== LOGOUT: Clearing session {dict(session)}")
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("=" * 70)
    print("DIRECT LOGIN TEST (No JavaScript)")
    print("Using traditional HTML form submission")
    print("=" * 70)
    print("\nOpen: http://localhost:5002\n")
    app.run(debug=True, port=5002)