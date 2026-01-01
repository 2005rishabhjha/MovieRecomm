"""
Check if all files are in the correct location
"""
import os

print("=" * 60)
print("MOVIERECOMM™ - Project Structure Check")
print("=" * 60)
print()

# Check current directory
print(f"Current directory: {os.getcwd()}")
print()

# Required files
required_files = [
    'app.py',
    'requirements.txt',
    'movies.csv',
]

required_folders = [
    'templates',
]

required_templates = [
    'templates/login.html',
    'templates/signup.html',
    'templates/dashboard.html',
]

print("Checking required files:")
print("-" * 60)
for file in required_files:
    exists = os.path.exists(file)
    status = "✓" if exists else "✗"
    print(f"{status} {file}")
print()

print("Checking required folders:")
print("-" * 60)
for folder in required_folders:
    exists = os.path.isdir(folder)
    status = "✓" if exists else "✗"
    print(f"{status} {folder}/")
print()

print("Checking template files:")
print("-" * 60)
for template in required_templates:
    exists = os.path.exists(template)
    status = "✓" if exists else "✗"
    print(f"{status} {template}")
print()

# List all files in templates folder
if os.path.exists('templates'):
    print("Files in templates/ folder:")
    print("-" * 60)
    for file in os.listdir('templates'):
        print(f"  - {file}")
else:
    print("⚠️  templates/ folder does not exist!")
    print("   Please create it and add the HTML files")
print()

print("=" * 60)
missing_files = [f for f in required_files if not os.path.exists(f)]
missing_templates = [t for t in required_templates if not os.path.exists(t)]

if not missing_files and not missing_templates:
    print("✓ All files are in place!")
else:
    print("✗ Missing files detected!")
    if missing_files:
        print("\nMissing files:")
        for f in missing_files:
            print(f"  - {f}")
    if missing_templates:
        print("\nMissing templates:")
        for t in missing_templates:
            print(f"  - {t}")
print("=" * 60)