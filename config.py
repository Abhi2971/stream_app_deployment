"""
Configuration Management Module
Handles environment variables and application settings
"""
import os
from typing import Optional

class Config:
    """Application configuration class"""
    
    def __init__(self):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            self.using_env = True
        except ImportError:
            self.using_env = False
    
    # MongoDB Configuration
    @property
    def MONGODB_USERNAME(self) -> str:
        return os.getenv('MONGODB_USERNAME', 'abhishelke297127')
    
    @property
    def MONGODB_PASSWORD(self) -> str:
        return os.getenv('MONGODB_PASSWORD', 'Abhi%402971')
    
    @property
    def MONGODB_CLUSTER(self) -> str:
        return os.getenv('MONGODB_CLUSTER', 'cluster0.uu8yq.mongodb.net')
    
    @property
    def MONGODB_CONNECTION_STRING(self) -> str:
        return f"mongodb+srv://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}@{self.MONGODB_CLUSTER}/?retryWrites=true&w=majority"
    
    # Database Names
    JAVA_FILE_ANALYSIS_DB = "JavaFileAnalysis"
    LOGIN_DATA_DB = "LoginData"
    QUESTION_DB = "Question"
    GRADE_DB = "Grades"
    FEEDBACK_DB = "Feedback"
    NOTIFICATION_DB = "Notifications"
    ACTIVITY_DB = "ActivityLogs"
    SETTINGS_DB = "Settings"
    
    # Application Settings
    @property
    def APP_TITLE(self) -> str:
        return os.getenv('APP_TITLE', '📚 Student Assignment Tracker')
    
    @property
    def APP_ICON(self) -> str:
        return os.getenv('APP_ICON', '📚')
    
    @property
    def SESSION_TIMEOUT(self) -> int:
        return int(os.getenv('SESSION_TIMEOUT', '3600'))
    
    # GitHub API Configuration
    @property
    def GITHUB_API_URL(self) -> str:
        return os.getenv('GITHUB_API_URL', 'https://api.github.com')
    
    # Username Validation Pattern
    USERNAME_PATTERN = r"^AF0[3-4][0-7]\d{4}$"
    
    # Page Configuration
    PAGE_CONFIG = {
        "page_title": "Assignment Tracker",
        "page_icon": "📚",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    # Color Scheme (updated for consistency)
    COLORS = {
        "primary": "#3498db",      # Blue
        "secondary": "#2ecc71",    # Green
        "success": "#27ae60",       # Dark Green
        "danger": "#e74c3c",        # Red
        "warning": "#f39c12",       # Orange
        "info": "#1abc9c",          # Teal
        "light": "#ecf0f1",         # Light Gray
        "dark": "#2c3e50",          # Dark Blue-Gray
        "background": "#f8f9fa",    # Off-white
        "card": "#ffffff",           # White
        "text": "#2c3e50",           # Dark text
        "text-light": "#7f8c8d"      # Gray text
    }
    
    # Chart Configuration
    CHART_CONFIG = {
        "displayModeBar": False,
        "responsive": True
    }

config = Config()