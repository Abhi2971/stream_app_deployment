"""
Database Setup and Management Module
Handles MongoDB database and collection creation
"""
from pymongo import MongoClient
from config import config
import streamlit as st

def setup_databases():
    """
    Initialize MongoDB databases and collections
    Creates required databases and collections if they don't exist
    """
    try:
        client = MongoClient(config.MONGODB_CONNECTION_STRING)
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")
        
        databases_and_collections = {
            config.JAVA_FILE_ANALYSIS_DB: [],
            config.LOGIN_DATA_DB: ["users"],
            config.QUESTION_DB: ["questions"],
            config.GRADE_DB: ["grades"],
            config.FEEDBACK_DB: ["feedback"],
            config.NOTIFICATION_DB: ["notifications"],
            config.ACTIVITY_DB: ["logs"],
            config.SETTINGS_DB: ["settings"]
        }
        
        for db_name, collections in databases_and_collections.items():
            db = client[db_name]
            existing_collections = db.list_collection_names()
            
            for collection_name in collections:
                if collection_name not in existing_collections:
                    db.create_collection(collection_name)
                    print(f"✓ Created collection '{collection_name}' in database '{db_name}'")
                else:
                    print(f"  Collection '{collection_name}' already exists in '{db_name}'")
        
        print("\n✓ All databases and collections are ready!")
        return True
        
    except Exception as e:
        print(f"✗ Error setting up databases: {e}")
        return False

def create_indexes():
    """
    Create indexes for better query performance
    """
    try:
        client = MongoClient(config.MONGODB_CONNECTION_STRING)
        
        # Users
        login_db = client[config.LOGIN_DATA_DB]
        login_db.users.create_index("username", unique=True)
        login_db.users.create_index("github_link", unique=True)
        
        # Questions
        question_db = client[config.QUESTION_DB]
        question_db.questions.create_index("class_name", unique=True)
        
        # Grades
        grade_db = client[config.GRADE_DB]
        grade_db.grades.create_index([("student_name", 1), ("assignment_name", 1)], unique=True)
        
        # Feedback
        feedback_db = client[config.FEEDBACK_DB]
        feedback_db.feedback.create_index([("student_name", 1), ("created_at", -1)])
        
        # Notifications
        notification_db = client[config.NOTIFICATION_DB]
        notification_db.notifications.create_index([("username", 1), ("read", 1), ("created_at", -1)])
        
        # Activity logs
        activity_db = client[config.ACTIVITY_DB]
        activity_db.logs.create_index([("username", 1), ("timestamp", -1)])
        
        print("✓ Created indexes for all collections")
        return True
        
    except Exception as e:
        print(f"✗ Error creating indexes: {e}")
        return False

def verify_connection():
    """Verify MongoDB connection"""
    try:
        client = MongoClient(config.MONGODB_CONNECTION_STRING)
        client.admin.command('ping')
        return True
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return False

def get_database_stats():
    """Get statistics about all databases"""
    try:
        client = MongoClient(config.MONGODB_CONNECTION_STRING)
        stats = {}
        
        dbs = [
            config.JAVA_FILE_ANALYSIS_DB,
            config.LOGIN_DATA_DB,
            config.QUESTION_DB,
            config.GRADE_DB,
            config.FEEDBACK_DB,
            config.NOTIFICATION_DB,
            config.ACTIVITY_DB,
            config.SETTINGS_DB
        ]
        
        for db_name in dbs:
            db = client[db_name]
            collections = db.list_collection_names()
            
            stats[db_name] = {
                'collections': len(collections),
                'collection_names': collections
            }
            
            for coll_name in collections:
                try:
                    count = db[coll_name].count_documents({})
                    stats[db_name][f'{coll_name}_count'] = count
                except:
                    stats[db_name][f'{coll_name}_count'] = 0
        
        return stats
        
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return {}

def cleanup_empty_collections():
    """Remove empty collections (maintenance function)"""
    try:
        client = MongoClient(config.MONGODB_CONNECTION_STRING)
        
        for db_name in [config.JAVA_FILE_ANALYSIS_DB]:
            db = client[db_name]
            collections = db.list_collection_names()
            
            for coll_name in collections:
                if db[coll_name].count_documents({}) == 0:
                    db[coll_name].drop()
                    print(f"Dropped empty collection: {coll_name}")
        
        return True
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Database Setup Script")
    print("=" * 50)
    print()
    
    if setup_databases():
        print()
        create_indexes()
        print()
        
        print("=" * 50)
        print("Database Statistics")
        print("=" * 50)
        stats = get_database_stats()
        for db_name, db_stats in stats.items():
            print(f"\n{db_name}:")
            for key, value in db_stats.items():
                print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)