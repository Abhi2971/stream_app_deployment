"""
Utility Functions Module
Common helper functions used across the application
"""
import re
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pymongo import MongoClient
from config import config

def connect_to_mongo(db_name: str = None):
    """
    Connect to MongoDB and return database instance
    
    Args:
        db_name: Name of the database to connect to
        
    Returns:
        MongoDB database instance or None if connection fails
    """
    try:
        client = MongoClient(config.MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        if db_name:
            return client[db_name]
        return client
    except Exception as e:
        st.error(f"❌ Error connecting to MongoDB: {e}")
        st.info("💡 Please check your .env file and ensure MongoDB credentials are correct")
        return None

def validate_username(username: str) -> bool:
    """
    Validate username format
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = config.USERNAME_PATTERN
    return bool(re.match(pattern, username))

def extract_owner_repo(github_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract owner and repository name from GitHub URL
    
    Args:
        github_url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo) or (None, None) if invalid
    """
    from urllib.parse import urlparse
    
    github_url = github_url.rstrip(".git")
    parsed_url = urlparse(github_url)
    path_parts = parsed_url.path.strip("/").split("/")
    
    if len(path_parts) >= 2:
        return path_parts[0], path_parts[1]
    return None, None

def calculate_completion_percentage(completed: int, total: int) -> float:
    """
    Calculate completion percentage
    
    Args:
        completed: Number of completed items
        total: Total number of items
        
    Returns:
        Percentage as float
    """
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 2)

def get_time_ago(date_str: str) -> str:
    """
    Convert datetime string to human-readable time ago format
    
    Args:
        date_str: ISO format datetime string
        
    Returns:
        Human-readable time difference
    """
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        now = datetime.now(date.tzinfo)
        diff = now - date
        
        if diff.days > 365:
            return f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
        else:
            return "just now"
    except:
        return "unknown"

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_grade_color(percentage: float) -> str:
    """
    Get color based on grade percentage
    
    Args:
        percentage: Grade percentage
        
    Returns:
        Color code
    """
    if percentage >= 90:
        return "#2ecc71"  # Green
    elif percentage >= 80:
        return "#3498db"  # Blue
    elif percentage >= 70:
        return "#f39c12"  # Orange
    else:
        return "#e74c3c"  # Red

def sanitize_collection_name(name: str) -> str:
    """
    Sanitize collection name to be MongoDB compatible
    
    Args:
        name: Collection name
        
    Returns:
        Sanitized name
    """
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    return sanitized

def get_student_statistics(db, student_name: str) -> Dict:
    """
    Get comprehensive statistics for a student
    
    Args:
        db: Database instance
        student_name: Student's name
        
    Returns:
        Dictionary with statistics
    """
    try:
        client = db.client if hasattr(db, 'client') else db
        java_analysis_db = client[config.JAVA_FILE_ANALYSIS_DB]
        question_db = client[config.QUESTION_DB]
        grade_db = client[config.GRADE_DB]
        
        stats = {
            'total_commits': 0,
            'total_files': 0,
            'completed_assignments': 0,
            'pending_assignments': 0,
            'total_assignments': 0,
            'completion_rate': 0,
            'last_commit_date': None,
            'lines_of_code': 0,
            'average_grade': 0,
            'grades_received': []
        }
        
        # Total assignments
        total_questions = question_db.questions.count_documents({})
        stats['total_assignments'] = total_questions
        
        # Student's data
        if student_name in java_analysis_db.list_collection_names():
            student_collection = java_analysis_db[student_name]
            documents = list(student_collection.find())
            
            stats['total_commits'] = len(documents)
            
            added_files = set()
            for doc in documents:
                if 'added_java_files' in doc and isinstance(doc['added_java_files'], dict):
                    added_files.update(doc['added_java_files'].keys())
                    for content in doc['added_java_files'].values():
                        stats['lines_of_code'] += len(content.split('\n'))
            
            stats['total_files'] = len(added_files)
            
            # Compare with questions
            questions = list(question_db.questions.find({}, {"class_name": 1}))
            for question in questions:
                class_name = question.get('class_name', '').replace('.java', '')
                if class_name in added_files:
                    stats['completed_assignments'] += 1
        
        stats['pending_assignments'] = stats['total_assignments'] - stats['completed_assignments']
        if stats['total_assignments'] > 0:
            stats['completion_rate'] = calculate_completion_percentage(
                stats['completed_assignments'], stats['total_assignments']
            )
        
        # Grades
        grades = list(grade_db.grades.find({"student_name": student_name}))
        if grades:
            stats['grades_received'] = grades
            total_grade = sum(g.get('grade', 0) for g in grades)
            stats['average_grade'] = round(total_grade / len(grades), 2)
        
        return stats
        
    except Exception as e:
        st.error(f"Error calculating statistics: {e}")
        return {}

def get_admin_statistics(db) -> Dict:
    """
    Get comprehensive statistics for admin dashboard
    
    Args:
        db: Database instance
        
    Returns:
        Dictionary with admin statistics
    """
    try:
        client = db.client if hasattr(db, 'client') else db
        java_analysis_db = client[config.JAVA_FILE_ANALYSIS_DB]
        question_db = client[config.QUESTION_DB]
        login_db = client[config.LOGIN_DATA_DB]
        grade_db = client[config.GRADE_DB]
        feedback_db = client[config.FEEDBACK_DB]
        notification_db = client[config.NOTIFICATION_DB]
        
        stats = {
            'total_students': 0,
            'total_assignments': 0,
            'total_submissions': 0,
            'average_completion': 0,
            'active_students': 0,
            'recent_activity': [],
            'total_grades': 0,
            'average_grade': 0,
            'total_feedback': 0,
            'total_notifications': 0,
            'student_list': []
        }
        
        # Students
        students = java_analysis_db.list_collection_names()
        stats['total_students'] = len(students)
        stats['student_list'] = students
        
        # Assignments
        stats['total_assignments'] = question_db.questions.count_documents({})
        
        # Submissions and completion
        total_completed = 0
        questions = list(question_db.questions.find({}, {"class_name": 1}))
        
        for student_name in students:
            student_collection = java_analysis_db[student_name]
            documents = list(student_collection.find())
            
            if documents:
                stats['active_students'] += 1
                stats['total_submissions'] += len(documents)
                
                added_files = set()
                for doc in documents:
                    if 'added_java_files' in doc and isinstance(doc['added_java_files'], dict):
                        added_files.update(doc['added_java_files'].keys())
                
                for question in questions:
                    class_name = question.get('class_name', '').replace('.java', '')
                    if class_name in added_files:
                        total_completed += 1
        
        if stats['total_students'] > 0 and stats['total_assignments'] > 0:
            stats['average_completion'] = round(
                (total_completed / (stats['total_students'] * stats['total_assignments'])) * 100, 2
            )
        
        # Grades
        stats['total_grades'] = grade_db.grades.count_documents({})
        all_grades = list(grade_db.grades.find({}, {"grade": 1}))
        if all_grades:
            stats['average_grade'] = round(sum(g['grade'] for g in all_grades) / len(all_grades), 2)
        
        # Feedback
        stats['total_feedback'] = feedback_db.feedback.count_documents({})
        
        # Notifications
        stats['total_notifications'] = notification_db.notifications.count_documents({})
        
        # Recent activity (last 5 logins)
        recent_logins = list(login_db.users.find({}, {"username": 1, "last_login": 1}).sort("last_login", -1).limit(5))
        stats['recent_activity'] = [
            {"username": u.get("username"), "time": get_time_ago(u.get("last_login", ""))}
            for u in recent_logins if u.get("last_login")
        ]
        
        return stats
        
    except Exception as e:
        st.error(f"Error calculating admin statistics: {e}")
        return {}

def create_chart_data_for_student(db, student_name: str) -> Dict:
    """
    Create chart data for student analytics
    
    Args:
        db: Database instance
        student_name: Student's name
        
    Returns:
        Dictionary with chart data
    """
    try:
        client = db.client if hasattr(db, 'client') else db
        java_analysis_db = client[config.JAVA_FILE_ANALYSIS_DB]
        grade_db = client[config.GRADE_DB]
        
        chart_data = {
            'commit_timeline': [],
            'file_types': {},
            'commit_frequency': {},
            'grades_over_time': [],
            'weekly_activity': [0]*7  # Mon-Sun
        }
        
        if student_name in java_analysis_db.list_collection_names():
            student_collection = java_analysis_db[student_name]
            documents = list(student_collection.find())
            
            for doc in documents:
                if 'commit_date' in doc:
                    date = datetime.fromisoformat(doc['commit_date'].replace('Z', '+00:00'))
                    chart_data['commit_timeline'].append({
                        'date': doc['commit_date'],
                        'message': doc.get('commit_message', 'No message')
                    })
                    # Weekly activity
                    weekday = date.weekday()  # 0=Mon, 6=Sun
                    chart_data['weekly_activity'][weekday] += 1
                
                if 'added_java_files' in doc:
                    for filename in doc['added_java_files'].keys():
                        ext = filename.split('.')[-1] if '.' in filename else 'unknown'
                        chart_data['file_types'][ext] = chart_data['file_types'].get(ext, 0) + 1
        
        # Grades over time
        grades = list(grade_db.grades.find({"student_name": student_name}).sort("date", 1))
        for g in grades:
            chart_data['grades_over_time'].append({
                'date': g.get('date'),
                'grade': g.get('grade'),
                'assignment': g.get('assignment_name')
            })
        
        return chart_data
        
    except Exception as e:
        st.error(f"Error creating chart data: {e}")
        return {}

def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'logged_in': False,
        'username': None,
        'role': None,
        'current_page': "Home",
        'notification_count': 0,
        'theme': 'light',
        'sidebar_state': 'expanded'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def logout():
    """Logout user and clear session"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.current_page = "Home"
    st.rerun()

def send_notification(db, username: str, title: str, message: str, notification_type: str = "info"):
    """
    Send a notification to a user
    
    Args:
        db: Database instance
        username: Recipient username
        title: Notification title
        message: Notification message
        notification_type: 'info', 'success', 'warning', 'error'
    """
    try:
        client = db.client if hasattr(db, 'client') else db
        notification_db = client[config.NOTIFICATION_DB]
        notification_db.notifications.insert_one({
            "username": username,
            "title": title,
            "message": message,
            "type": notification_type,
            "read": False,
            "created_at": datetime.now().isoformat()
        })
    except Exception as e:
        st.error(f"Failed to send notification: {e}")

def get_unread_notifications(db, username: str) -> List[Dict]:
    """Get unread notifications for a user"""
    try:
        client = db.client if hasattr(db, 'client') else db
        notification_db = client[config.NOTIFICATION_DB]
        return list(notification_db.notifications.find({"username": username, "read": False}).sort("created_at", -1))
    except:
        return []

def mark_notification_read(db, notification_id):
    """Mark a notification as read"""
    try:
        from bson.objectid import ObjectId
        client = db.client if hasattr(db, 'client') else db
        notification_db = client[config.NOTIFICATION_DB]
        notification_db.notifications.update_one({"_id": ObjectId(notification_id)}, {"$set": {"read": True}})
    except:
        pass

def add_activity_log(db, username: str, action: str, details: str = ""):
    """Log user activity"""
    try:
        client = db.client if hasattr(db, 'client') else db
        activity_db = client[config.ACTIVITY_DB]
        activity_db.logs.insert_one({
            "username": username,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    except:
        pass

def get_user_activity(db, username: str, limit: int = 20) -> List[Dict]:
    """Get recent activity for a user"""
    try:
        client = db.client if hasattr(db, 'client') else db
        activity_db = client[config.ACTIVITY_DB]
        return list(activity_db.logs.find({"username": username}).sort("timestamp", -1).limit(limit))
    except:
        return []

def paginate_data(data: List, page: int, page_size: int = 10) -> List:
    """Paginate a list of items"""
    start = (page - 1) * page_size
    end = start + page_size
    return data[start:end]

def search_items(data: List, search_term: str, fields: List[str]) -> List:
    """Search list of dicts by fields"""
    if not search_term:
        return data
    search_lower = search_term.lower()
    return [item for item in data if any(search_lower in str(item.get(f, '')).lower() for f in fields)]