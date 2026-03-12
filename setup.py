"""
Setup Script for Student Assignment Tracker
Automates the initial setup process
"""
import os
import sys
from pymongo import MongoClient

def print_header():
    """Print setup header"""
    # print("=" * 10)
    # print("  📚 Student Assignment Tracker - Setup Wizard")
    # print("=" * 10)
    print()

def check_python_version():
    """Verify Python version"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✓ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install dependencies")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_env_file():
    """Create .env file from template"""
    print("\n📝 Setting up environment variables...")
    
    if os.path.exists('.env'):
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("  Skipping .env setup")
            return True
    
    try:
        with open('.env.example', 'r') as example:
            content = example.read()
        
        print("\n📋 Please provide your MongoDB credentials:")
        print("   (You can get these from MongoDB Atlas)")
        
        username = input("   MongoDB Username: ").strip()
        password = input("   MongoDB Password: ").strip()
        cluster = input("   MongoDB Cluster (e.g., cluster0.xxxxx.mongodb.net): ").strip()
        
        if not username or not password or not cluster:
            print("❌ All fields are required!")
            return False
        
        # Update content with user input
        content = content.replace('your_username_here', username)
        content = content.replace('your_password_here', password)
        content = content.replace('cluster0.uu8yq.mongodb.net', cluster)
        
        with open('.env', 'w') as env_file:
            env_file.write(content)
        
        print("✓ .env file created successfully")
        return True
    
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n🔌 Testing MongoDB connection...")
    
    try:
        # Import config after .env is created
        from config import config
        
        client = MongoClient(config.MONGODB_CONNECTION_STRING)
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")
        return True
    
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\n💡 Tips:")
        print("   - Check your credentials in .env file")
        print("   - Ensure your IP is whitelisted in MongoDB Atlas")
        print("   - Verify your cluster URL is correct")
        return False

def initialize_database():
    """Initialize database collections"""
    print("\n🗄️  Initializing database...")
    
    try:
        from database import setup_databases, create_indexes
        
        if setup_databases():
            print("✓ Database structure created")
            
            if create_indexes():
                print("✓ Indexes created")
            
            return True
        
        return False
    
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def create_admin_user():
    """Optionally create an admin user"""
    print("\n👨‍💼 Admin User Setup")
    response = input("Would you like to create an admin user? (Y/n): ")
    
    if response.lower() == 'n':
        print("  Skipping admin user creation")
        return True
    
    try:
        from config import config
        
        print("\n📋 Enter admin credentials:")
        name = input("   Name: ").strip()
        username = input("   Username: ").strip()
        password = input("   Password: ").strip()
        
        if not name or not username or not password:
            print("❌ All fields are required!")
            return False
        
        client = MongoClient(config.MONGODB_CONNECTION_STRING)
        db = client[config.LOGIN_DATA_DB]
        
        # Check if user already exists
        if db.users.find_one({"username": username}):
            print(f"⚠️  User '{username}' already exists!")
            return False
        
        db.users.insert_one({
            "name": name,
            "username": username,
            "password": password,
            "role": "admin",
            "github_link": "https://github.com/admin/repo",
            "github_token": "admin_token"
        })
        
        print(f"✓ Admin user '{username}' created successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def print_next_steps():
    """Print what to do next"""
    print("\n" + "=" * 60)
    print("  🎉 Setup Complete!")
    print("=" * 60)
    print("\n📚 Next Steps:")
    print("   1. Run the application:")
    print("      streamlit run stream_app.py")
    print()
    print("   2. Open your browser to:")
    print("      http://localhost:8501")
    print()
    print("   3. Check the documentation:")
    print("      - README.md for full guide")
    print("      - QUICKSTART.md for quick tour")
    print()
    print("💡 Tips:")
    print("   - Default admin credentials (if created above)")
    print("   - Students need to register with GitHub token")
    print("   - Check .env file for configuration")
    print()
    print("=" * 60)

def main():
    """Main setup process"""
    print_header()
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("\n⚠️  You can manually install dependencies:")
        print("   pip install -r requirements.txt")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Step 3: Setup .env file
    if not setup_env_file():
        print("\n⚠️  You can manually create .env file from .env.example")
        sys.exit(1)
    
    # Step 4: Test MongoDB connection
    if not test_mongodb_connection():
        print("\n⚠️  Fix MongoDB connection and run setup again")
        sys.exit(1)
    
    # Step 5: Initialize database
    if not initialize_database():
        print("\n⚠️  Database initialization failed")
        sys.exit(1)
    
    # Step 6: Create admin user (optional)
    create_admin_user()
    
    # Done!
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
