"""
MOVIERECOMM™ - Dataset Verification Script
Run this to check if your Kaggle dataset is properly set up
"""

import pandas as pd
import os
import sys

def check_dataset():
    """Verify the Kaggle movies dataset"""
    print("=" * 70)
    print("MOVIERECOMM™ - Dataset Verification")
    print("Checking: Trending Movies Dataset (1990-2025)")
    print("=" * 70)
    print()
    
    # Check if file exists
    if not os.path.exists('movies.csv'):
        print("❌ ERROR: movies.csv not found in current directory!")
        print()
        print("📥 Please download the dataset:")
        print("   1. Go to: https://www.kaggle.com/datasets/amitksingh2103/trending-movies-over-the-years")
        print("   2. Click 'Download' button")
        print("   3. Extract the ZIP file")
        print("   4. Rename the CSV file to 'movies.csv'")
        print("   5. Place it in the same folder as this script")
        print()
        print(f"Current directory: {os.getcwd()}")
        return False
    
    print("✅ movies.csv found!")
    print()
    
    try:
        # Load dataset
        print("Loading dataset...")
        df = pd.read_csv('movies.csv', encoding='utf-8')
        
        # Basic info
        print("=" * 70)
        print("📊 DATASET INFORMATION")
        print("=" * 70)
        print(f"Total movies: {len(df):,}")
        print(f"Total columns: {len(df.columns)}")
        print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        print()
        
        # Column information
        print("=" * 70)
        print("📋 COLUMNS FOUND")
        print("=" * 70)
        for i, col in enumerate(df.columns, 1):
            non_null = df[col].notna().sum()
            percentage = (non_null / len(df)) * 100
            print(f"{i:2d}. {col:20s} - {non_null:,} values ({percentage:.1f}% filled)")
        print()
        
        # Check for required columns
        print("=" * 70)
        print("🔍 REQUIRED COLUMNS CHECK")
        print("=" * 70)
        
        required_cols = {
            'title': ['title', 'original_title', 'movie_title'],
            'overview': ['overview', 'description', 'plot'],
            'genres': ['genres', 'genre'],
            'release_date': ['release_date', 'year'],
            'vote_average': ['vote_average', 'rating', 'score'],
            'vote_count': ['vote_count', 'votes', 'num_votes']
        }
        
        found_columns = {}
        missing_columns = []
        
        for required, alternatives in required_cols.items():
            found = None
            for alt in alternatives:
                if alt in df.columns:
                    found = alt
                    break
            
            if found:
                found_columns[required] = found
                print(f"✅ {required:15s} → Found as '{found}'")
            else:
                missing_columns.append(required)
                print(f"⚠️  {required:15s} → Not found (searched: {', '.join(alternatives)})")
        
        print()
        
        # Show sample data
        print("=" * 70)
        print("📽️  SAMPLE MOVIES (First 5)")
        print("=" * 70)
        
        # Determine which columns to display
        display_cols = []
        if 'title' in found_columns:
            display_cols.append(found_columns['title'])
        if 'release_date' in found_columns:
            display_cols.append(found_columns['release_date'])
        if 'vote_average' in found_columns:
            display_cols.append(found_columns['vote_average'])
        if 'genres' in found_columns:
            display_cols.append(found_columns['genres'])
        
        if display_cols:
            sample = df[display_cols].head(5)
            for idx, row in sample.iterrows():
                print(f"\nMovie {idx + 1}:")
                for col in display_cols:
                    value = row[col]
                    if pd.isna(value):
                        value = "N/A"
                    elif isinstance(value, float):
                        value = f"{value:.1f}"
                    print(f"  {col:15s}: {value}")
        
        print()
        
        # Statistics
        print("=" * 70)
        print("📈 DATASET STATISTICS")
        print("=" * 70)
        
        if 'release_date' in found_columns or 'year' in found_columns:
            date_col = found_columns.get('release_date', found_columns.get('year'))
            try:
                # Try to extract years
                years = pd.to_datetime(df[date_col], errors='coerce').dt.year
                valid_years = years.dropna()
                if not valid_years.empty:
                    print(f"Year range: {int(valid_years.min())} - {int(valid_years.max())}")
                    
                    # Count by decade
                    print("\nMovies by decade:")
                    for decade in range(1990, 2030, 10):
                        count = ((valid_years >= decade) & (valid_years < decade + 10)).sum()
                        if count > 0:
                            print(f"  {decade}s: {count:,} movies")
            except:
                pass
        
        if 'vote_average' in found_columns:
            ratings = df[found_columns['vote_average']].dropna()
            if not ratings.empty:
                print(f"\nRatings:")
                print(f"  Average rating: {ratings.mean():.2f}")
                print(f"  Highest rating: {ratings.max():.2f}")
                print(f"  Lowest rating: {ratings.min():.2f}")
        
        if 'genres' in found_columns:
            genres_col = df[found_columns['genres']].dropna()
            print(f"\nGenres: {len(genres_col)} movies have genre information")
        
        print()
        
        # Final verdict
        print("=" * 70)
        print("✨ VERDICT")
        print("=" * 70)
        
        if len(missing_columns) == 0:
            print("✅ PERFECT! All required columns found!")
            print("   Your dataset is ready to use with MOVIERECOMM™")
        elif len(missing_columns) <= 2:
            print("⚠️  GOOD - Most columns found!")
            print(f"   Missing: {', '.join(missing_columns)}")
            print("   The app will work but some features may be limited")
        else:
            print("❌ WARNING - Several columns missing!")
            print(f"   Missing: {', '.join(missing_columns)}")
            print("   Make sure you downloaded the correct dataset")
        
        print()
        print("Next steps:")
        print("1. ✅ Run: python test_connection.py (test database)")
        print("2. ✅ Run: python app.py (start the application)")
        print("3. ✅ Open: http://localhost:5000")
        print()
        
        return True
        
    except pd.errors.EmptyDataError:
        print("❌ ERROR: movies.csv is empty!")
        return False
    except pd.errors.ParserError as e:
        print(f"❌ ERROR: Could not parse CSV file!")
        print(f"   {e}")
        print("   The file might be corrupted. Try re-downloading.")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_dataset()
    sys.exit(0 if success else 1)