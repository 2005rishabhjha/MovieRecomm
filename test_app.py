"""
Simple test version to diagnose the session/redirect issue
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
import pyodbc
import hashlib

app = Flask(__name__)
app.secret_key = 'test-secret-key-12345'

# Database config
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

@app.route('/')
def index():
    """Home page - shows session status"""
    print(f"\n=== INDEX ROUTE CALLED ===")
    print(f"Session contents: {dict(session)}")
    print(f"Has user_id: {'user_id' in session}")
    
    if 'user_id' in session:
        username = session.get('username', 'Unknown')
        print(f"User is logged in: {username}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard</title>
            <style>
                body {{ font-family: Arial; padding: 50px; background: #f0f0f0; }}
                .box {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; }}
                h1 {{ color: #667eea; }}
                .info {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                button {{ background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="box">
                <h1>✓ Dashboard</h1>
                <p>Welcome, <strong>{username}</strong>!</p>
                <div class="info">
                    <p>User ID: {session.get('user_id')}</p>
                    <p>Email: {session.get('email', 'N/A')}</p>
                </div>
                <p>🎉 You are successfully logged in!</p>
                <button onclick="location.href='/logout'">Logout</button>
            </div>
        </body>
        </html>
        """
    else:
        print("No user in session, redirecting to login")
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'GET':
        print("\n=== LOGIN PAGE LOADED ===")
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Test</title>
            <style>
                body { font-family: Arial; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                .box { background: white; padding: 30px; border-radius: 10px; max-width: 400px; margin: 0 auto; }
                input { width: 100%; padding: 10px; margin: 10px 0; border: 2px solid #ddd; border-radius: 5px; }
                button { width: 100%; background: #667eea; color: white; border: none; padding: 12px; border-radius: 5px; cursor: pointer; font-size: 16px; }
                button:hover { background: #5568d3; }
                .alert { padding: 10px; border-radius: 5px; margin: 10px 0; display: none; }
                .alert-error { background: #fee; color: #c33; }
                .alert-success { background: #efe; color: #3c3; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1 style="color: #667eea; text-align: center;">MOVIERECOMM™</h1>
                <p style="text-align: center; color: #666;">Test Login</p>
                
                <div id="alert" class="alert"></div>
                
                <form id="loginForm">
                    <input type="text" id="username" placeholder="Username" required>
                    <input type="password" id="password" placeholder="Password" required>
                    <button type="submit">Login</button>
                </form>
            </div>
            
            <script>
                document.getElementById('loginForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    const alert = document.getElementById('alert');
                    
                    console.log('Submitting login for:', username);
                    
                    try {
                        const response = await fetch('/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username, password })
                        });
                        
                        console.log('Response status:', response.status);
                        const data = await response.json();
                        console.log('Response data:', data);
                        
                        if (data.success) {
                            alert.textContent = 'Login successful! Redirecting...';
                            alert.className = 'alert alert-success';
                            alert.style.display = 'block';
                            
                            console.log('Redirecting to:', data.redirect);
                            
                            // Try multiple redirect methods
                            setTimeout(() => {
                                console.log('Attempting redirect...');
                                window.location.href = data.redirect;
                            }, 500);
                        } else {
                            alert.textContent = data.message;
                            alert.className = 'alert alert-error';
                            alert.style.display = 'block';
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        alert.textContent = 'Connection error: ' + error.message;
                        alert.className = 'alert alert-error';
                        alert.style.display = 'block';
                    }
                });
            </script>
        </body>
        </html>
        """
    
    # POST request - handle login
    print("\n=== LOGIN POST REQUEST ===")
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        print(f"Login attempt: {username}")
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'})
        
        # Check database
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        cursor.execute(
            "SELECT user_id, username, email FROM Users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Clear and set session
            session.clear()
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[2]
            session.permanent = True
            session.modified = True
            
            print(f"✓ Login SUCCESS!")
            print(f"  User ID: {user[0]}")
            print(f"  Username: {user[1]}")
            print(f"  Session after setting: {dict(session)}")
            
            response = make_response(jsonify({
                'success': True,
                'message': 'Login successful',
                'redirect': '/',
                'user': user[1]
            }))
            return response
        else:
            print(f"✗ Login FAILED - Invalid credentials")
            return jsonify({'success': False, 'message': 'Invalid username or password'})
            
    except Exception as e:
        print(f"✗ Login ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/logout')
def logout():
    """Logout"""
    print(f"\n=== LOGOUT ===")
    print(f"Clearing session: {dict(session)}")
    session.clear()
    return redirect(url_for('login'))

@app.route('/test-session')
def test_session():
    """Test if sessions work at all"""
    if 'counter' not in session:
        session['counter'] = 0
    session['counter'] += 1
    
    return f"""
    <h1>Session Test</h1>
    <p>Counter: {session['counter']}</p>
    <p>Session ID: {request.cookies.get('session')}</p>
    <p>Full session: {dict(session)}</p>
    <a href="/test-session">Refresh</a> | <a href="/">Home</a>
    """

if __name__ == '__main__':
    print("=" * 70)
    print("SIMPLE TEST APP - Running")
    print("=" * 70)
    app.run(debug=True, port=5001)  # Using port 5001 to avoid conflicts