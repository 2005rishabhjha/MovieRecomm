"""
MOVIERECOMM™ - Complete Production Ready Application
Windows Authentication with HTML Form Login
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pyodbc
import pandas as pd
import hashlib
from datetime import timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ============================================================================
# Flask App Configuration
# ============================================================================
app = Flask(__name__)
app.secret_key = 'k9mP2$xL#vN8qR@tY5wE!hU3jF7cS1dA'  # Change this in production

app.config['SESSION_COOKIE_NAME'] = 'movierecomm_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# ============================================================================
# Database Configuration (Windows Authentication)
# ============================================================================
DB_CONFIG = {
    'server': 'LAPTOP-B0N4O9L6\\MSSQLSERVERDB',
    'database': 'MovieRecommDB',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

def get_db_connection():
    """Create database connection using Windows Authentication"""
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

# ============================================================================
# Database Initialization
# ============================================================================
def init_database():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create Users table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
            CREATE TABLE Users (
                user_id INT IDENTITY(1,1) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT GETDATE()
            )
        """)
        
        # Create UserPreferences table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='UserPreferences' AND xtype='U')
            CREATE TABLE UserPreferences (
                pref_id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT FOREIGN KEY REFERENCES Users(user_id),
                movie_title VARCHAR(500),
                rating FLOAT,
                watched_date DATETIME DEFAULT GETDATE()
            )
        """)
        
        conn.commit()
        conn.close()
        print("✓ Database tables initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization error: {e}")

# ============================================================================
# Helper Functions
# ============================================================================
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================================================
# Movie Data Loading
# ============================================================================
movies_df = None
tfidf_matrix = None
cosine_sim = None

def load_movies_data():
    """Load and prepare movie dataset from Kaggle"""
    global movies_df, tfidf_matrix, cosine_sim
    
    try:
        movies_df = pd.read_csv('movies.csv', encoding='utf-8')
        
        print(f"Loaded {len(movies_df)} movies from dataset")
        print(f"Columns: {list(movies_df.columns)}")
        
        # Ensure required columns exist
        if 'title' not in movies_df.columns:
            movies_df['title'] = movies_df.iloc[:, 0]
        
        if 'overview' not in movies_df.columns:
            movies_df['overview'] = ''
        
        if 'genres' not in movies_df.columns:
            movies_df['genres'] = ''
        
        # Clean data
        movies_df['overview'] = movies_df['overview'].fillna('')
        movies_df['genres'] = movies_df['genres'].fillna('')
        movies_df['title'] = movies_df['title'].fillna('Unknown')
        
        # Prepare features for recommendation engine
        movies_df['combined_features'] = (
            movies_df['title'].fillna('') + ' ' +
            movies_df['overview'].fillna('') + ' ' + 
            movies_df['genres'].fillna('')
        )
        
        # Create TF-IDF matrix for content-based recommendations
        tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = tfidf.fit_transform(movies_df['combined_features'])
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        print("✓ Movie recommendation engine initialized successfully!")
        
    except FileNotFoundError:
        print("✗ ERROR: movies.csv not found!")
        print("   Please download from: https://www.kaggle.com/datasets/amitksingh2103/trending-movies-over-the-years")
    except Exception as e:
        print(f"✗ Error loading movies: {e}")

# ============================================================================
# Routes - Authentication
# ============================================================================

@app.route('/')
def index():
    """Home page - redirects based on login status"""
    if 'user_id' in session:
        return render_template('dashboard.html', username=session.get('username'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with HTML form submission"""
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        print(f"\n=== LOGIN ATTEMPT ===")
        print(f"Username: {username}")
        
        if not username or not password:
            flash('Please enter both username and password')
            return render_template('login.html')
        
        try:
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
                # Set session
                session.clear()
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['email'] = user[2]
                session.permanent = True
                
                print(f"✓ Login successful: {user[1]} (ID: {user[0]})")
                print(f"  Session: {dict(session)}")
                
                return redirect(url_for('index'))
            else:
                print("✗ Invalid credentials")
                flash('Invalid username or password')
                return render_template('login.html')
                
        except Exception as e:
            print(f"✗ Login error: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Database error: Please try again')
            return render_template('login.html')
    
    # GET request - show login form
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration with HTML form submission"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        print(f"\n=== SIGNUP ATTEMPT ===")
        print(f"Username: {username}")
        print(f"Email: {email}")
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required')
            return render_template('signup.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('signup.html')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            password_hash = hash_password(password)
            cursor.execute(
                "INSERT INTO Users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            conn.commit()
            conn.close()
            
            print(f"✓ User registered successfully: {username}")
            flash('Account created successfully! Please login.')
            return redirect(url_for('login'))
            
        except pyodbc.IntegrityError:
            print("✗ User already exists")
            flash('Username or email already exists')
            return render_template('signup.html')
        except Exception as e:
            print(f"✗ Signup error: {e}")
            flash('Registration failed. Please try again.')
            return render_template('signup.html')
    
    # GET request - show signup form
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """User logout"""
    username = session.get('username', 'Unknown')
    print(f"\n=== LOGOUT: {username} ===")
    session.clear()
    flash('You have been logged out successfully')
    return redirect(url_for('login'))

# ============================================================================
# Routes - Movie API Endpoints
# ============================================================================

@app.route('/api/movies')
def get_movies():
    """Get paginated list of movies"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if movies_df is None:
        return jsonify({'error': 'Movie data not loaded'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        movies_page = movies_df.iloc[start_idx:end_idx]
        
        movies_list = []
        for _, movie in movies_page.iterrows():
            movie_dict = {
                'title': movie.get('title', 'Unknown'),
                'release_date': movie.get('release_date', 'N/A'),
                'vote_average': float(movie.get('vote_average', 0)) if pd.notna(movie.get('vote_average')) else 0,
                'vote_count': int(movie.get('vote_count', 0)) if pd.notna(movie.get('vote_count')) else 0,
                'overview': movie.get('overview', 'No overview available'),
                'genres': movie.get('genres', 'Unknown'),
                'popularity': float(movie.get('popularity', 0)) if pd.notna(movie.get('popularity')) else 0
            }
            movies_list.append(movie_dict)
        
        return jsonify({
            'movies': movies_list,
            'total': len(movies_df),
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        print(f"Error in get_movies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search_movies():
    """Search movies by title, overview, or genre"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if movies_df is None:
        return jsonify({'error': 'Movie data not loaded'}), 500
    
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({'movies': []})
    
    try:
        # Search in title, overview, and genres
        filtered = movies_df[
            movies_df['title'].str.lower().str.contains(query, na=False) |
            movies_df['overview'].str.lower().str.contains(query, na=False) |
            movies_df['genres'].str.lower().str.contains(query, na=False)
        ]
        
        movies_list = []
        for _, movie in filtered.head(20).iterrows():
            movie_dict = {
                'title': movie.get('title', 'Unknown'),
                'release_date': movie.get('release_date', 'N/A'),
                'vote_average': float(movie.get('vote_average', 0)) if pd.notna(movie.get('vote_average')) else 0,
                'vote_count': int(movie.get('vote_count', 0)) if pd.notna(movie.get('vote_count')) else 0,
                'overview': movie.get('overview', 'No overview available'),
                'genres': movie.get('genres', 'Unknown'),
                'popularity': float(movie.get('popularity', 0)) if pd.notna(movie.get('popularity')) else 0
            }
            movies_list.append(movie_dict)
        
        return jsonify({'movies': movies_list})
    except Exception as e:
        print(f"Error in search_movies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/popular')
def get_popular():
    """Get popular/trending movies"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if movies_df is None:
        return jsonify({'error': 'Movie data not loaded'}), 500
    
    try:
        # Sort by popularity or rating
        if 'popularity' in movies_df.columns:
            popular = movies_df.sort_values('popularity', ascending=False)
        elif 'vote_average' in movies_df.columns and 'vote_count' in movies_df.columns:
            movies_df['weighted_rating'] = movies_df['vote_average'] * movies_df['vote_count']
            popular = movies_df.sort_values('weighted_rating', ascending=False)
        else:
            popular = movies_df
        
        movies_list = []
        for _, movie in popular.head(20).iterrows():
            movie_dict = {
                'title': movie.get('title', 'Unknown'),
                'release_date': movie.get('release_date', 'N/A'),
                'vote_average': float(movie.get('vote_average', 0)) if pd.notna(movie.get('vote_average')) else 0,
                'vote_count': int(movie.get('vote_count', 0)) if pd.notna(movie.get('vote_count')) else 0,
                'overview': movie.get('overview', 'No overview available'),
                'genres': movie.get('genres', 'Unknown'),
                'popularity': float(movie.get('popularity', 0)) if pd.notna(movie.get('popularity')) else 0
            }
            movies_list.append(movie_dict)
        
        return jsonify({'movies': movies_list})
    except Exception as e:
        print(f"Error in get_popular: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/<movie_title>')
def get_recommendations(movie_title):
    """Get movie recommendations based on content similarity"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if movies_df is None or cosine_sim is None:
        return jsonify({'error': 'Recommendation engine not initialized'}), 500
    
    try:
        # Find the movie
        matches = movies_df[movies_df['title'].str.lower() == movie_title.lower()]
        
        if matches.empty:
            return jsonify({'error': 'Movie not found', 'recommendations': []})
        
        idx = matches.index[0]
        
        # Get similarity scores
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:11]  # Top 10 similar movies (excluding itself)
        
        movie_indices = [i[0] for i in sim_scores]
        recommended_movies = movies_df.iloc[movie_indices]
        
        recommendations = []
        for _, movie in recommended_movies.iterrows():
            movie_dict = {
                'title': movie.get('title', 'Unknown'),
                'release_date': movie.get('release_date', 'N/A'),
                'vote_average': float(movie.get('vote_average', 0)) if pd.notna(movie.get('vote_average')) else 0,
                'vote_count': int(movie.get('vote_count', 0)) if pd.notna(movie.get('vote_count')) else 0,
                'overview': movie.get('overview', 'No overview available'),
                'genres': movie.get('genres', 'Unknown'),
                'popularity': float(movie.get('popularity', 0)) if pd.notna(movie.get('popularity')) else 0
            }
            recommendations.append(movie_dict)
        
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        return jsonify({'error': str(e), 'recommendations': []}), 500

# ============================================================================
# Run Application
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("MOVIERECOMM™ - Starting Application")
    print("=" * 70)
    print()
    
    # Initialize database
    init_database()
    
    # Load movie data
    load_movies_data()
    
    print()
    print("=" * 70)
    print("✓ Server running on: http://localhost:5000")
    print("  Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    app.run(debug=True, port=5000)