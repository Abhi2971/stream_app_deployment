"""
Student Module
Handles all student-related functionalities with enhanced UI and visualizations
"""
import os
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from config import config
from utils import (
    extract_owner_repo,
    get_student_statistics,
    calculate_completion_percentage,
    create_chart_data_for_student,
    send_notification,
    add_activity_log,
    get_unread_notifications,
    paginate_data,
    search_items
)
from styles import create_metric_card, create_progress_bar, create_status_badge, get_chart_config

def extract_base_name(key):
    """Extract base filename without .java from a stored key (may include path)"""
    base = os.path.basename(key)
    if base.endswith('.java'):
        base = base[:-5]
    return base

def student_dashboard(db):
    """Enhanced Student Dashboard with visualizations and statistics"""
    st.markdown("## 📊 Student Dashboard")
    
    try:
        login_db = db.client[config.LOGIN_DATA_DB]
        user = login_db.users.find_one({"username": st.session_state.username})
        if not user:
            st.error("User data not found")
            return
        
        student_name = user.get('name', 'Unknown')
        stats = get_student_statistics(db, student_name)
        chart_data = create_chart_data_for_student(db, student_name)
        
        # Fetch all questions
        questions = list(db.questions.find())
        total_assignments = len(questions)
        
        # Get student's completed assignments (base names)
        java_db = db.client[config.JAVA_FILE_ANALYSIS_DB]
        completed_bases = set()
        if student_name in java_db.list_collection_names():
            coll = java_db[student_name]
            docs = list(coll.find({}, {"added_java_files": 1, "modified_java_files": 1}))
            for doc in docs:
                added = doc.get('added_java_files', {})
                modified = doc.get('modified_java_files', {})
                for key in added.keys():
                    completed_bases.add(extract_base_name(key))
                for key in modified.keys():
                    completed_bases.add(extract_base_name(key))
        
        completed_count = 0
        for q in questions:
            base = q['class_name'].replace('.java', '')
            if base in completed_bases:
                completed_count += 1
        pending_count = total_assignments - completed_count
        completion_rate = calculate_completion_percentage(completed_count, total_assignments)
        
        # Metrics (use computed values, but keep other stats from get_student_statistics)
        cols = st.columns(4)
        metrics = [
            ("Total Assignments", total_assignments, "primary"),
            ("Completed", completed_count, "success"),
            ("Pending", pending_count, "danger"),
            ("Completion Rate", f"{completion_rate}%", "info")
        ]
        for col, (label, value, color) in zip(cols, metrics):
            with col:
                st.markdown(create_metric_card(label, value, color=color), unsafe_allow_html=True)
        
        # Progress
        st.markdown("### 📈 Overall Progress")
        st.markdown(create_progress_bar(completion_rate, "Assignment Completion"), unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Status")
            fig = go.Figure(data=[go.Pie(
                labels=['Completed', 'Pending'],
                values=[completed_count, pending_count],
                marker=dict(colors=['#2ecc71', '#e74c3c']),
                hole=0.4
            )])
            fig.update_layout(showlegend=True, height=300, margin=dict(t=0))
            st.plotly_chart(fig, width='stretch', config=get_chart_config())
        
        with col2:
            st.markdown("### 📝 Activity")
            act_data = pd.DataFrame({
                'Metric': ['Commits', 'Java Files', 'Lines of Code'],
                'Count': [stats['total_commits'], stats['total_files'], stats['lines_of_code']]
            })
            fig = px.bar(act_data, x='Metric', y='Count', color='Metric',
                         color_discrete_sequence=['#3498db', '#2ecc71', '#f39c12'])
            fig.update_layout(showlegend=False, height=300, margin=dict(t=0))
            st.plotly_chart(fig, width='stretch', config=get_chart_config())
        
        # Weekly activity heatmap
        if chart_data['weekly_activity']:
            st.markdown("### 📅 Weekly Activity")
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            df_week = pd.DataFrame({'Day': days, 'Commits': chart_data['weekly_activity']})
            fig = px.bar(df_week, x='Day', y='Commits', color='Commits',
                         color_continuous_scale='Blues')
            st.plotly_chart(fig, width='stretch', config=get_chart_config())
        
        # Recent assignments
        st.markdown("### 📚 Recent Assignments")
        recent_questions = questions[:5]  # first 5
        if recent_questions:
            for q in recent_questions:
                base = q['class_name'].replace('.java', '')
                is_completed = base in completed_bases
                status = "Completed" if is_completed else "Pending"
                badge = create_status_badge(status)
                st.markdown(f"""
                <div class="assignment-card {'completed' if is_completed else 'pending'}">
                    <strong>{q.get('question_name')}</strong><br>
                    <small>Class: {q.get('class_name')}</small>
                    <div style="float:right">{badge}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No assignments yet.")
        
        # Recent grades
        if stats.get('grades_received'):
            st.markdown("### 🏆 Recent Grades")
            df_grades = pd.DataFrame(stats['grades_received'][-5:])
            st.dataframe(df_grades[['assignment_name', 'grade', 'comments', 'created_at']], width='stretch', hide_index=True)
    
    except Exception as e:
        st.error(f"Error: {e}")

def student_assignments(db, username):
    """Display student's assignments with filtering"""
    st.markdown("## 📋 My Assignments")
    
    try:
        login_db = db.client[config.LOGIN_DATA_DB]
        user = login_db.users.find_one({"username": username})
        if not user:
            st.error("User not found")
            return
        
        name = user.get('name', 'Unknown')
        questions = list(db.questions.find())
        
        # Get completed assignments (base names)
        java_db = db.client[config.JAVA_FILE_ANALYSIS_DB]
        completed_bases = set()
        if name in java_db.list_collection_names():
            coll = java_db[name]
            docs = list(coll.find({}, {"added_java_files": 1, "modified_java_files": 1}))
            for doc in docs:
                added = doc.get('added_java_files', {})
                modified = doc.get('modified_java_files', {})
                for key in added.keys():
                    completed_bases.add(extract_base_name(key))
                for key in modified.keys():
                    completed_bases.add(extract_base_name(key))
        
        completed_count = sum(1 for q in questions if extract_base_name(q['class_name']) in completed_bases)
        pending_count = len(questions) - completed_count
        
        # Summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(questions))
        col2.metric("Completed", completed_count, delta=f"{calculate_completion_percentage(completed_count, len(questions))}%")
        col3.metric("Pending", pending_count)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            filter_status = st.selectbox("Filter", ["All", "Completed", "Pending"])
        with col2:
            search = st.text_input("Search by name")
        
        # Display
        for q in questions:
            base = q['class_name'].replace('.java', '')
            is_completed = base in completed_bases
            if filter_status == "Completed" and not is_completed:
                continue
            if filter_status == "Pending" and is_completed:
                continue
            if search and search.lower() not in q['question_name'].lower():
                continue
            
            status = "Completed" if is_completed else "Pending"
            badge = create_status_badge(status)
            st.markdown(f"""
            <div class="assignment-card {'completed' if is_completed else 'pending'}">
                <strong>{q['question_name']}</strong><br>
                <small>Class: {q['class_name']}</small>
                <div style="float:right">{badge}</div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error: {e}")

def student_data(db, username):
    """Display student's profile and code submissions"""
    st.markdown("## 👤 My Profile & Submissions")
    
    try:
        login_db = db.client[config.LOGIN_DATA_DB]
        user = login_db.users.find_one({"username": username})
        if not user:
            st.error("User not found")
            return
        
        name = user.get('name', 'Unknown')
        github_link = user.get('github_link', 'N/A')
        
        # Profile
        st.markdown("### 📝 Profile Information")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {name}")
            st.markdown(f"**Username:** {username}")
        with col2:
            st.markdown(f"**GitHub:** [{github_link}]({github_link})")
        
        # Submissions
        java_db = db.client[config.JAVA_FILE_ANALYSIS_DB]
        if name not in java_db.list_collection_names():
            st.info("No submissions yet.")
            return
        
        coll = java_db[name]
        docs = list(coll.find())
        
        # Aggregate files (keys may include paths, we'll keep them for display)
        added = {}
        modified = {}
        for d in docs:
            added.update(d.get('added_java_files', {}))
            modified.update(d.get('modified_java_files', {}))
        
        tab1, tab2 = st.tabs(["📁 Added Files", "✏️ Modified Files"])
        with tab1:
            if added:
                st.markdown(f"**Total Added Files:** {len(added)}")
                selected = st.selectbox("Select file", list(added.keys()), key="added")
                if selected:
                    content = added[selected]
                    lines = len(content.split('\n'))
                    st.code(content, language='java', line_numbers=True)
                    st.caption(f"Lines: {lines}")
            else:
                st.info("No added files.")
        
        with tab2:
            if modified:
                st.markdown(f"**Total Modified Files:** {len(modified)}")
                selected = st.selectbox("Select file", list(modified.keys()), key="modified")
                if selected:
                    content = modified[selected]
                    lines = len(content.split('\n'))
                    st.code(content, language='java', line_numbers=True)
                    st.caption(f"Lines: {lines}")
            else:
                st.info("No modified files.")
    
    except Exception as e:
        st.error(f"Error: {e}")

def submit_feedback(db, username):
    """Submit feedback to admin"""
    st.markdown("## 📝 Submit Feedback")
    
    login_db = db.client[config.LOGIN_DATA_DB]
    user = login_db.users.find_one({"username": username})
    if not user:
        st.error("User not found")
        return
    
    with st.form("feedback_form"):
        subject = st.text_input("Subject", placeholder="e.g., Question about assignment")
        message = st.text_area("Message", placeholder="Write your feedback here...")
        if st.form_submit_button("Submit Feedback"):
            if subject and message:
                feedback_db = db.client[config.FEEDBACK_DB]
                feedback_db.feedback.insert_one({
                    "student_name": user['name'],
                    "username": username,
                    "subject": subject,
                    "message": message,
                    "created_at": datetime.now().isoformat(),
                    "response": None
                })
                add_activity_log(db, username, "Feedback", f"Submitted: {subject}")
                send_notification(db, "admin", "New Feedback", f"{username}: {subject}", "info")
                st.success("Feedback submitted.")
                st.rerun()
            else:
                st.error("Please fill all fields.")

def view_grades(db, username):
    """View personal grades"""
    st.markdown("## 📊 My Grades")
    
    login_db = db.client[config.LOGIN_DATA_DB]
    user = login_db.users.find_one({"username": username})
    if not user:
        st.error("User not found")
        return
    
    grade_db = db.client[config.GRADE_DB]
    grades = list(grade_db.grades.find({"student_name": user['name']}).sort("created_at", -1))
    
    if not grades:
        st.info("No grades yet.")
        return
    
    df = pd.DataFrame(grades)
    df = df[['assignment_name', 'grade', 'comments', 'created_at']]
    st.dataframe(df, width='stretch', hide_index=True)
    
    # Chart
    st.markdown("### 📈 Grade Trend")
    fig = px.line(df, x='created_at', y='grade', title='Grades over time', markers=True)
    st.plotly_chart(fig, width='stretch', config=get_chart_config())

def profile_settings(db, username):
    """Update profile settings"""
    st.markdown("## ⚙️ Profile Settings")
    
    login_db = db.client[config.LOGIN_DATA_DB]
    user = login_db.users.find_one({"username": username})
    if not user:
        st.error("User not found")
        return
    
    with st.form("profile_form"):
        name = st.text_input("Name", value=user.get('name', ''))
        github_link = st.text_input("GitHub Repository", value=user.get('github_link', ''))
        github_token = st.text_input("GitHub Token", type="password", value=user.get('github_token', ''))
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        
        if st.form_submit_button("Update Profile"):
            updates = {}
            if name != user['name']:
                updates['name'] = name
            if github_link != user['github_link']:
                # Validate repo
                owner, repo = extract_owner_repo(github_link)
                if not owner or not repo:
                    st.error("Invalid GitHub URL")
                    return
                updates['github_link'] = github_link
            if github_token:
                updates['github_token'] = github_token
            if new_password:
                updates['password'] = new_password
            
            if updates:
                login_db.users.update_one({"username": username}, {"$set": updates})
                add_activity_log(db, username, "Profile", "Updated profile")
                st.success("Profile updated.")
                st.rerun()