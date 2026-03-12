"""
Student Assignment Tracker - Main Application
Enhanced version with modern UI, visualizations, and improved user experience
"""
import streamlit as st
from pymongo import MongoClient
from urllib.parse import urlparse
import requests
import re
from datetime import datetime
from github import Github, UnknownObjectException
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Import custom modules
from config import config
from utils import (
    connect_to_mongo,
    validate_username,
    extract_owner_repo,
    initialize_session_state,
    logout,
    send_notification,
    get_unread_notifications,
    mark_notification_read,
    add_activity_log,
    get_user_activity,
    paginate_data,
    search_items
)
from admin import admin_dashboard, manage_students, manage_questions, manage_grades, view_feedback, activity_logs, system_settings
from student import student_dashboard, student_assignments, student_data, submit_feedback, view_grades, profile_settings
from styles import get_custom_css, get_chart_config

# Page configuration
st.set_page_config(**config.PAGE_CONFIG)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize session state
initialize_session_state()

def header():
    """Application header with navigation and notification badge"""
    col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
    
    with col1:
        # st.markdown(f"## {config.APP_ICON} {config.APP_TITLE.replace(config.APP_ICON, '').strip()}")
        # st.markdown("Abhi")
        st.markdown(f"<h2 style='white-space: nowrap;'>{config.APP_ICON} {config.APP_TITLE.replace(config.APP_ICON,'').strip()}</h2>",unsafe_allow_html=True)
    
    with col3:
        if st.session_state.logged_in:
            st.markdown(f"**👤 {st.session_state.username}**")
    
    with col4:
        if st.session_state.logged_in:
            # Notification bell
            db = connect_to_mongo()
            if db:
                notifications = get_unread_notifications(db, st.session_state.username)
                count = len(notifications)
                badge = f"🔔 ({count})" if count > 0 else "🔔"
                if st.button(badge, key="notif_bell"):
                    st.session_state.current_page = "Notifications"
                    st.rerun()

def toolbar():
    """Navigation toolbar based on user role with extra options"""
    if not st.session_state.logged_in:
        with st.sidebar:
            st.markdown("### 🧭 Navigation")
            if st.button("🏠 Home", width='stretch'):
                st.session_state.current_page = "Home"
                st.rerun()
            if st.button("🔑 Login", width='stretch'):
                st.session_state.current_page = "Login"
                st.rerun()
            if st.button("📝 Register", width='stretch'):
                st.session_state.current_page = "Register"
                st.rerun()
    else:
        with st.sidebar:
            st.markdown(f"### 👤 Welcome, {st.session_state.username}!")
            st.markdown(f"**Role:** {st.session_state.role.title()}")
            st.markdown("---")
            
            if st.session_state.role == "admin":
                st.markdown("### 👨‍💼 Admin Menu")
                if st.button("📊 Dashboard", width='stretch'):
                    st.session_state.current_page = "Admin Dashboard"
                    st.rerun()
                if st.button("📝 Manage Assignments", width='stretch'):
                    st.session_state.current_page = "Manage Questions"
                    st.rerun()
                if st.button("👥 Student Submissions", width='stretch'):
                    st.session_state.current_page = "Student Codes"
                    st.rerun()
                if st.button("📊 Manage Grades", width='stretch'):
                    st.session_state.current_page = "Manage Grades"
                    st.rerun()
                if st.button("💬 View Feedback", width='stretch'):
                    st.session_state.current_page = "View Feedback"
                    st.rerun()
                if st.button("📋 Activity Logs", width='stretch'):
                    st.session_state.current_page = "Activity Logs"
                    st.rerun()
                if st.button("⚙️ Settings", width='stretch'):
                    st.session_state.current_page = "System Settings"
                    st.rerun()
            else:
                st.markdown("### 📚 Student Menu")
                if st.button("📊 Dashboard", width='stretch'):
                    st.session_state.current_page = "Student Dashboard"
                    st.rerun()
                if st.button("📋 My Assignments", width='stretch'):
                    st.session_state.current_page = "My Assignments"
                    st.rerun()
                if st.button("💾 My Submissions", width='stretch'):
                    st.session_state.current_page = "My Data"
                    st.rerun()
                if st.button("📝 Submit Feedback", width='stretch'):
                    st.session_state.current_page = "Submit Feedback"
                    st.rerun()
                if st.button("📊 My Grades", width='stretch'):
                    st.session_state.current_page = "My Grades"
                    st.rerun()
                if st.button("🔔 Notifications", width='stretch'):
                    st.session_state.current_page = "Notifications"
                    st.rerun()
                if st.button("⚙️ Profile Settings", width='stretch'):
                    st.session_state.current_page = "Profile Settings"
                    st.rerun()
            
            st.markdown("---")
            if st.button("🚪 Logout", width='stretch'):
                logout()

def is_github_repo_public(github_token, owner, repo):
    """Check if the GitHub repository is public and accessible"""
    try:
        g = Github(github_token)
        repository = g.get_repo(f"{owner}/{repo}")
        
        if repository.private:
            st.error("❌ GitHub repository is private.")
            return False
        
        repository.get_contents("")
        return True
    except UnknownObjectException:
        st.error("❌ Token does not have access to this repository.")
        return False
    except Exception as e:
        st.error("❌ Error accessing GitHub repository. Ensure the repository exists and the token is correct.")
        return False

def check_repo_visibility(owner, repo, headers):
    """Check if repository is public"""
    repo_url = f"{config.GITHUB_API_URL}/repos/{owner}/{repo}"
    response = requests.get(repo_url, headers=headers)
    
    if response.status_code == 200:
        repo_data = response.json()
        if repo_data.get("private"):
            st.warning("⚠️ The repository is private.")
            return False
        return True
    return False

def fetch_commits_and_files(owner, repo, db, headers, name):
    """Fetch commits and files from GitHub repository"""
    commits_url = f"{config.GITHUB_API_URL}/repos/{owner}/{repo}/commits"
    response = requests.get(commits_url, headers=headers)
    
    if response.status_code != 200:
        st.error(f"❌ Failed to fetch commits: {response.json().get('message', 'Unknown error')}")
        return
    
    commits = response.json()
    collection = db[name]
    
    for commit in commits:
        commit_sha = commit["sha"]
        commit_message = commit["commit"]["message"]
        commit_date = commit["commit"]["author"]["date"]
        
        if collection.find_one({"commit_sha": commit_sha}):
            continue
        
        commit_url = f"{config.GITHUB_API_URL}/repos/{owner}/{repo}/commits/{commit_sha}"
        commit_response = requests.get(commit_url, headers=headers)
        
        if commit_response.status_code != 200:
            continue
        
        commit_data = commit_response.json()
        files = commit_data.get("files", [])
        
        added_java_files = {}
        modified_java_files = {}
        deleted_java_files = []
        renamed_java_files = {}
        
        for file in files:
            filename = file["filename"]
            status = file["status"]
            
            if filename.endswith(".java"):
                if status == "added":
                    file_url = file.get("raw_url")
                    if file_url:
                        file_response = requests.get(file_url, headers=headers)
                        if file_response.status_code == 200:
                            added_java_files[filename] = file_response.text
                
                elif status == "modified":
                    file_url = file.get("raw_url")
                    if file_url:
                        file_response = requests.get(file_url, headers=headers)
                        if file_response.status_code == 200:
                            modified_java_files[filename] = file_response.text
                
                elif status == "removed":
                    deleted_java_files.append(filename)
                
                elif status == "renamed":
                    previous_filename = file.get("previous_filename")
                    renamed_java_files[previous_filename] = filename
        
        commit_document = {
            "commit_sha": commit_sha,
            "commit_message": commit_message,
            "commit_date": commit_date,
            "added_java_files": added_java_files,
            "modified_java_files": modified_java_files,
            "deleted_java_files": deleted_java_files,
            "renamed_java_files": renamed_java_files
        }
        
        collection.insert_one(commit_document)
        add_activity_log(db, name, "GitHub sync", f"Fetched commit {commit_sha[:7]}")

def login():
    """User login page with enhanced UI"""

    st.markdown("""
    <div class="app-header">
        <h1>🔑 Login to Your Account</h1>
        <p>Access your personalized dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    client = MongoClient(config.MONGODB_CONNECTION_STRING)
    login_db = client[config.LOGIN_DATA_DB]

    with st.form("login_form"):

        username = st.text_input(
            "👤 Username",
            placeholder="Enter your username"
        )

        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Enter your password"
        )

        col1, col2 = st.columns(2)

        with col1:
            login_submit = st.form_submit_button("🚀 Login", width="stretch")

        with col2:
            goto_register = st.form_submit_button("📝 Need an account?", width="stretch")

    # Handle navigation
    if goto_register:
        st.session_state.current_page = "Register"
        st.rerun()

    # Handle login
    if login_submit:

        if not username or not password:
            st.error("⚠️ Please fill in all fields")
            return

        user = login_db.users.find_one({
            "username": username,
            "password": password
        })

        if user:

            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]

            # Update last login
            login_db.users.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.now().isoformat()}}
            )

            st.success(f"✅ Welcome {user['name']}!")

            add_activity_log(
                login_db,
                username,
                "Login",
                "User logged in"
            )

            # Admin dashboard
            if user["role"] == "admin":
                st.session_state.current_page = "Admin Dashboard"

            else:

                github_link = user["github_link"]
                github_token = user["github_token"]
                name = user["name"]

                owner, repo = extract_owner_repo(github_link)

                if owner and repo:

                    HEADERS = {
                        "Authorization": f"token {github_token}"
                    }

                    with st.spinner("🔄 Fetching your latest GitHub data..."):

                        if check_repo_visibility(owner, repo, HEADERS):

                            db = client[config.JAVA_FILE_ANALYSIS_DB]

                            fetch_commits_and_files(
                                owner,
                                repo,
                                db,
                                HEADERS,
                                name
                            )

                            st.success("✅ Data synced successfully!")

                st.session_state.current_page = "Student Dashboard"

            st.rerun()

        else:
            st.error("❌ Invalid username or password")


def register_user():
    """User registration page with enhanced UI"""

    st.markdown("""
    <div class="app-header">
        <h1>📝 Create Your Account</h1>
        <p>Join the student assignment tracking system</p>
    </div>
    """, unsafe_allow_html=True)

    client = MongoClient(config.MONGODB_CONNECTION_STRING)
    login_db = client[config.LOGIN_DATA_DB]

    with st.form("registration_form"):

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "👤 Full Name",
                placeholder="Enter your full name"
            )

            username = st.text_input(
                "🆔 Username",
                placeholder="e.g., AF0442897"
            )

        with col2:
            github_link = st.text_input(
                "🔗 GitHub Repository",
                placeholder="https://github.com/username/repo"
            )

            github_token = st.text_input(
                "🔑 GitHub Token",
                type="password",
                placeholder="Your GitHub personal access token"
            )

        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Create a strong password"
        )

        register_submit = st.form_submit_button(
            "✅ Register",
            width="stretch"
        )

    # Form submission logic
    if register_submit:

        errors = []

        if not name.strip():
            errors.append("Name is required")

        if not validate_username(username):
            errors.append("Invalid username format (e.g., AF0300000)")

        if not github_link:
            errors.append("GitHub link is required")

        if not github_token:
            errors.append("GitHub token is required")

        if not password:
            errors.append("Password is required")

        if errors:
            for error in errors:
                st.error(f"⚠️ {error}")
            return

        owner, repo = extract_owner_repo(github_link)

        if not owner or not repo:
            st.error("❌ Invalid GitHub URL")
            return

        if not is_github_repo_public(github_token, owner, repo):
            return

        existing_user = login_db.users.find_one({"username": username})
        existing_repo = login_db.users.find_one({"github_link": github_link})

        if existing_user and existing_repo:
            st.error("❌ Both username and GitHub link already exist")
            return

        if existing_user:
            st.error("❌ Username already exists")
            return

        if existing_repo:
            st.error("❌ GitHub link already registered")
            return

        try:

            login_db.users.insert_one({
                "name": name,
                "username": username,
                "github_link": github_link,
                "github_token": github_token,
                "password": password,
                "role": "student",
                "created_at": datetime.now().isoformat(),
                "last_login": None
            })

            st.success("✅ Registration successful! Please login.")
            st.balloons()

        except Exception as e:
            st.error(f"❌ Registration failed: {e}")

def homepage():
    """Enhanced homepage"""
    st.markdown("""
    <div class="app-header">
        <h3>📚 Welcome to Student Assignment Tracker</h3>
        <p>Track, manage, and analyze student assignments with GitHub integration</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-box">
                <h3>🎓 For Students</h3>
                <p>Track your assignments, view progress, submit feedback, and receive grades.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Get Started", width='stretch'):
                st.session_state.current_page = "Register"
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="info-box">
                <h3>👨‍💼 For Administrators</h3>
                <p>Manage assignments, monitor progress, grade submissions, and analyze data.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔑 Login", width='stretch'):
                st.session_state.current_page = "Login"
                st.rerun()
    else:
        st.markdown(f"""
        <div class="success-box">
            <h3>👋 Hello, {st.session_state.username}!</h3>
            <p>You are logged in as <strong>{st.session_state.role}</strong>. Use the sidebar to navigate.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("## ✨ Key Features")
    cols = st.columns(3)
    features = [
        ("📊 Real-time Analytics", "Track progress with interactive charts"),
        ("🔗 GitHub Integration", "Automatic synchronization with your repos"),
        ("📈 Progress Tracking", "Monitor completion and grades"),
        ("💬 Feedback System", "Submit and receive feedback"),
        ("📋 Grade Management", "View and manage grades"),
        ("🔔 Notifications", "Stay updated with alerts")
    ]
    for i, (title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"**{title}**  \n{desc}")

def notifications_page():
    """Display user notifications"""
    st.markdown("## 🔔 Notifications")
    db = connect_to_mongo()
    if not db:
        return
    
    notif_db = db.client[config.NOTIFICATION_DB]
    notifications = list(notif_db.notifications.find(
        {"username": st.session_state.username}
    ).sort("created_at", -1))
    
    if not notifications:
        st.info("No notifications.")
        return
    
    for n in notifications:
        with st.container():
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(n.get("type", "info"), "📌")
                st.markdown(f"{icon} **{n['title']}**  \n{n['message']}  \n<small>{n['created_at']}</small>", unsafe_allow_html=True)
            with col2:
                if not n.get("read", False):
                    if st.button("✓", key=f"read_{n['_id']}"):
                        mark_notification_read(db, n['_id'])
                        st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_{n['_id']}"):
                    notif_db.notifications.delete_one({"_id": n["_id"]})
                    st.rerun()
            st.markdown("---")

def main():
    """Main application entry point"""
    db = connect_to_mongo(config.QUESTION_DB)
    
    if db is None:
        st.error("❌ Failed to connect to database. Please check your connection.")
        return
    
    # Render header and navigation
    header()
    toolbar()
    
    # Route to appropriate page
    page = st.session_state.current_page
    
    if page == "Home":
        homepage()
    elif page == "Login":
        login()
    elif page == "Register":
        register_user()
    elif page == "Notifications":
        notifications_page()
    elif st.session_state.logged_in:
        if st.session_state.role == "admin":
            if page == "Admin Dashboard":
                admin_dashboard(db)
            elif page == "Manage Questions":
                manage_questions(db)
            elif page == "Student Codes":
                manage_students(db)
            elif page == "Manage Grades":
                manage_grades(db)
            elif page == "View Feedback":
                view_feedback(db)
            elif page == "Activity Logs":
                activity_logs(db)
            elif page == "System Settings":
                system_settings(db)
        else:
            if page == "Student Dashboard":
                student_dashboard(db)
            elif page == "My Assignments":
                student_assignments(db, st.session_state.username)
            elif page == "My Data":
                student_data(db, st.session_state.username)
            elif page == "Submit Feedback":
                submit_feedback(db, st.session_state.username)
            elif page == "My Grades":
                view_grades(db, st.session_state.username)
            elif page == "Notifications":
                notifications_page()
            elif page == "Profile Settings":
                profile_settings(db, st.session_state.username)
    else:
        st.error("❌ Access denied. Please login first.")

if __name__ == "__main__":
    main()