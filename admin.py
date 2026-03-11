"""
Admin Module
Handles all admin-related functionalities with enhanced analytics and visualizations
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from config import config
from utils import (
    get_admin_statistics,
    calculate_completion_percentage,
    send_notification,
    add_activity_log,
    paginate_data,
    search_items,
    get_time_ago
)
from styles import create_metric_card, create_progress_bar, get_chart_config, create_status_badge

def admin_dashboard(db):
    """Enhanced Admin Dashboard with comprehensive analytics"""
    st.markdown("## 👨‍💼 Admin Dashboard")
    
    try:
        stats = get_admin_statistics(db)
        
        # Top metrics
        cols = st.columns(5)
        metrics = [
            ("Total Students", stats['total_students'], "primary"),
            ("Total Assignments", stats['total_assignments'], "info"),
            ("Active Students", stats['active_students'], "success"),
            ("Avg Completion", f"{stats['average_completion']}%", "warning"),
            ("Avg Grade", stats['average_grade'], "secondary")
        ]
        for col, (label, value, color) in zip(cols, metrics):
            with col:
                st.markdown(create_metric_card(label, value, color=color), unsafe_allow_html=True)
        
        # Progress bar
        st.markdown("### 📊 Overall Progress")
        st.markdown(create_progress_bar(stats['average_completion'], "Class Average Completion"), unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 Student Activity")
            java_analysis_db = db.client[config.JAVA_FILE_ANALYSIS_DB]
            students = java_analysis_db.list_collection_names()
            activity = []
            for s in students[:10]:  # Top 10
                count = java_analysis_db[s].count_documents({})
                activity.append({"Student": s[:15], "Commits": count})
            if activity:
                df = pd.DataFrame(activity).sort_values("Commits", ascending=True)
                fig = px.bar(df, x="Commits", y="Student", orientation='h', color="Commits",
                             color_continuous_scale="Blues")
                fig.update_layout(showlegend=False, height=400, margin=dict(t=0))
                st.plotly_chart(fig, width='stretch', config=get_chart_config())
        
        with col2:
            st.markdown("### 📊 Completion Distribution")
            question_db = db.client[config.QUESTION_DB]
            questions = list(question_db.questions.find({}, {"class_name": 1}))
            completion_cats = {"0-20%":0, "20-40%":0, "40-60%":0, "60-80%":0, "80-100%":0}
            for student in students:
                student_col = java_analysis_db[student]
                docs = list(student_col.find())
                added = set()
                for d in docs:
                    if 'added_java_files' in d:
                        added.update(d['added_java_files'].keys())
                completed = sum(1 for q in questions if q.get('class_name','').replace('.java','') in added)
                pct = calculate_completion_percentage(completed, len(questions)) if questions else 0
                if pct < 20: completion_cats["0-20%"] += 1
                elif pct < 40: completion_cats["20-40%"] += 1
                elif pct < 60: completion_cats["40-60%"] += 1
                elif pct < 80: completion_cats["60-80%"] += 1
                else: completion_cats["80-100%"] += 1
            df = pd.DataFrame(list(completion_cats.items()), columns=["Range", "Students"])
            fig = px.pie(df, values="Students", names="Range", color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, width='stretch', config=get_chart_config())
        
        # Recent activity
        st.markdown("### 🕒 Recent Activity")
        if stats['recent_activity']:
            df = pd.DataFrame(stats['recent_activity'])
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No recent activity.")
        
        # Quick actions
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("➕ Add Assignment", width='stretch'):
                st.session_state.current_page = "Manage Questions"
                st.rerun()
        with col2:
            if st.button("📊 Manage Grades", width='stretch'):
                st.session_state.current_page = "Manage Grades"
                st.rerun()
        with col3:
            if st.button("📋 View Feedback", width='stretch'):
                st.session_state.current_page = "View Feedback"
                st.rerun()
        with col4:
            if st.button("🔔 Send Notification", width='stretch'):
                st.session_state.show_notification_form = True
        
        if st.session_state.get("show_notification_form", False):
            with st.form("send_notification"):
                st.markdown("### Send Notification to Students")
                title = st.text_input("Title")
                message = st.text_area("Message")
                notif_type = st.selectbox("Type", ["info", "success", "warning", "error"])
                if st.form_submit_button("Send"):
                    if title and message:
                        login_db = db.client[config.LOGIN_DATA_DB]
                        students = login_db.users.find({"role": "student"})
                        for s in students:
                            send_notification(db, s['username'], title, message, notif_type)
                        st.success("Notification sent to all students.")
                        add_activity_log(db, st.session_state.username, "Broadcast notification", f"Title: {title}")
                        st.session_state.show_notification_form = False
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def manage_questions(db):
    """Enhanced question management with better UI"""
    st.markdown("## 📝 Manage Assignments")
    questions_collection = db.questions
    
    # Add new
    with st.expander("➕ Add New Assignment", expanded=False):
        with st.form("add_question"):
            col1, col2 = st.columns(2)
            with col1:
                qname = st.text_input("Assignment Name", placeholder="e.g., Array Exercise")
            with col2:
                cname = st.text_input("Class Name", placeholder="e.g., ArrayExercise.java")
            if st.form_submit_button("Add"):
                if qname and cname:
                    if not cname.endswith('.java'): cname += '.java'
                    if questions_collection.find_one({"class_name": cname}):
                        st.error("Class name already exists.")
                    else:
                        questions_collection.insert_one({
                            "question_name": qname,
                            "class_name": cname,
                            "created_at": datetime.now().isoformat()
                        })
                        add_activity_log(db, st.session_state.username, "Add assignment", f"{qname}")
                        st.success("Assignment added.")
                        st.rerun()
    
    # List with search and pagination
    questions = list(questions_collection.find())
    if not questions:
        st.info("No assignments yet.")
        return
    
    st.markdown(f"**Total Assignments:** {len(questions)}")
    search = st.text_input("🔍 Search by name or class")
    filtered = search_items(questions, search, ["question_name", "class_name"])
    
    if not filtered:
        st.info("No matching assignments found.")
        return
    
    page_size = 10
    total_pages = (len(filtered) - 1) // page_size + 1
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=min(1, total_pages), step=1)
    paginated = paginate_data(filtered, page, page_size)
    
    for q in paginated:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
        with col1:
            st.markdown(f"**{q['question_name']}**")
        with col2:
            st.code(q['class_name'])
        with col3:
            # Completion count
            java_db = db.client[config.JAVA_FILE_ANALYSIS_DB]
            students = java_db.list_collection_names()
            completed = 0
            class_base = q['class_name'].replace('.java', '')
            for s in students:
                coll = java_db[s]
                docs = coll.find({}, {"added_java_files": 1})
                for d in docs:
                    if class_base in d.get('added_java_files', {}):
                        completed += 1
                        break
            st.metric("Completed", f"{completed}/{len(students)}")
        with col4:
            if st.button("✏️", key=f"edit_{q['_id']}"):
                st.session_state[f"editing_{q['_id']}"] = True
        with col5:
            if st.button("🗑️", key=f"del_{q['_id']}"):
                questions_collection.delete_one({"_id": q["_id"]})
                add_activity_log(db, st.session_state.username, "Delete assignment", f"{q['question_name']}")
                st.rerun()
        
        if st.session_state.get(f"editing_{q['_id']}", False):
            with st.form(f"edit_form_{q['_id']}"):
                new_name = st.text_input("Assignment Name", value=q['question_name'])
                new_class = st.text_input("Class Name", value=q['class_name'])
                if st.form_submit_button("Save"):
                    questions_collection.update_one(
                        {"_id": q["_id"]},
                        {"$set": {"question_name": new_name, "class_name": new_class, "updated_at": datetime.now().isoformat()}}
                    )
                    add_activity_log(db, st.session_state.username, "Edit assignment", f"{new_name}")
                    st.session_state[f"editing_{q['_id']}"] = False
                    st.rerun()
                if st.form_submit_button("Cancel"):
                    st.session_state[f"editing_{q['_id']}"] = False
                    st.rerun()
        st.markdown("---")

def manage_students(db):
    """Enhanced student code viewer with error handling for missing fields"""
    st.markdown("## 👥 Student Code Submissions")
    java_db = db.client[config.JAVA_FILE_ANALYSIS_DB]
    students = java_db.list_collection_names()
    
    if not students:
        st.info("No student submissions yet.")
        return
    
    st.markdown(f"**Total Students with submissions:** {len(students)}")
    selected = st.selectbox("Select Student", sorted(students))
    
    if selected:
        coll = java_db[selected]
        docs = list(coll.find())
        st.metric("Total Commits", len(docs))
        
        # Aggregate files
        all_files = {}
        for d in docs:
            all_files.update(d.get('added_java_files', {}))
        
        if all_files:
            st.markdown(f"**Total Java Files:** {len(all_files)}")
            file_list = sorted(all_files.keys())
            selected_file = st.selectbox("Select File", file_list)
            if selected_file:
                content = all_files[selected_file]
                lines = len(content.split('\n'))
                st.code(content, language='java', line_numbers=True)
                st.caption(f"Lines: {lines} | Characters: {len(content)}")
                
                # Show commit history for this file (with safe field access)
                st.markdown("#### Commit History")
                history = []
                for d in docs:
                    if selected_file in d.get('added_java_files', {}):
                        history.append({
                            "Commit": d.get('commit_sha', 'N/A')[:7] if d.get('commit_sha') else 'N/A',
                            "Date": d.get('commit_date', 'Unknown'),
                            "Message": d.get('commit_message', 'No message')
                        })
                if history:
                    df = pd.DataFrame(history)
                    st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No Java files found.")

def manage_grades(db):
    """Admin grade management with code preview and assignment status list"""
    st.markdown("## 📊 Manage Grades")
    
    login_db = db.client[config.LOGIN_DATA_DB]
    students = list(login_db.users.find({"role": "student"}))
    question_db = db.client[config.QUESTION_DB]
    questions = list(question_db.questions.find())
    grade_db = db.client[config.GRADE_DB]
    java_db = db.client[config.JAVA_FILE_ANALYSIS_DB]
    
    if not students:
        st.info("No students registered.")
        return
    
    if not questions:
        st.info("No assignments created yet.")
        return
    
    # Select student and assignment
    col1, col2 = st.columns(2)
    with col1:
        student_names = [s['name'] for s in students]
        selected_student = st.selectbox("Student", student_names)
    with col2:
        assignment_names = [q['question_name'] for q in questions]
        selected_assignment = st.selectbox("Assignment", assignment_names)
    
    # Get student username and assignment details
    student = next(s for s in students if s['name'] == selected_student)
    assignment = next(q for q in questions if q['question_name'] == selected_assignment)
    
    # Strip .java for matching
    target_base = assignment['class_name'].replace('.java', '')  # e.g., "Address"
    
    # Determine if student has submitted this assignment and fetch latest code
    submitted = False
    code_content = None
    if student['name'] in java_db.list_collection_names():
        coll = java_db[student['name']]
        # Get commits sorted by commit_date descending (latest first)
        docs = list(coll.find().sort("commit_date", -1))
        for doc in docs:
            # Check both added and modified files
            for file_dict in [doc.get('added_java_files', {}), doc.get('modified_java_files', {})]:
                if target_base in file_dict:  # key is the base name without extension
                    submitted = True
                    code_content = file_dict[target_base]
                    break
            if submitted:
                break
    
    # Show submission status and code
    st.markdown("---")
    if submitted:
        st.success(f"✅ {selected_student} has submitted this assignment.")
        with st.expander("📄 View Submitted Code", expanded=True):
            if code_content:
                st.code(code_content, language='java', line_numbers=True)
            else:
                st.warning("Code content not available.")
    else:
        st.warning(f"⚠️ {selected_student} has NOT submitted this assignment yet.")
    
    # Grade form
    st.markdown("---")
    st.markdown("### ✏️ Grade Assignment")
    existing = grade_db.grades.find_one({
        "student_name": selected_student,
        "assignment_name": selected_assignment
    })
    
    with st.form("grade_form"):
        grade = st.number_input("Grade (0-100)", min_value=0, max_value=100, value=existing['grade'] if existing else 0)
        comments = st.text_area("Comments", value=existing.get('comments', '') if existing else "")
        submitted_grade = st.form_submit_button("Save Grade")
        
        if submitted_grade:
            if existing:
                grade_db.grades.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "grade": grade,
                        "comments": comments,
                        "updated_at": datetime.now().isoformat()
                    }}
                )
                msg = f"Grade updated for {selected_student} on {selected_assignment}: {grade}"
            else:
                grade_db.grades.insert_one({
                    "student_name": selected_student,
                    "assignment_name": selected_assignment,
                    "grade": grade,
                    "comments": comments,
                    "created_at": datetime.now().isoformat()
                })
                msg = f"Grade assigned for {selected_student} on {selected_assignment}: {grade}"
            st.success("Grade saved.")
            add_activity_log(db, st.session_state.username, "Grade", msg)
            send_notification(db, student['username'], "Grade Posted", f"Your grade for {selected_assignment} is {grade}", "info")
            st.rerun()
    
    # Assignment Status Table (now at the bottom)
    st.markdown("---")
    st.markdown("### 📋 Assignment Status for this Student")
    
    # Build set of completed base filenames (without .java) from all commits
    completed_bases = set()
    if student['name'] in java_db.list_collection_names():
        coll = java_db[student['name']]
        docs = list(coll.find({}, {"added_java_files": 1, "modified_java_files": 1}))
        for doc in docs:
            added = doc.get('added_java_files', {})
            modified = doc.get('modified_java_files', {})
            completed_bases.update(added.keys())
            completed_bases.update(modified.keys())
    
    status_data = []
    for q in questions:
        base = q['class_name'].replace('.java', '')
        status = "Completed" if base in completed_bases else "Pending"
        status_data.append({
            "Assignment": q['question_name'],
            "Class": q['class_name'],
            "Status": status
        })
    
    df_status = pd.DataFrame(status_data)
    
    # Apply color styling
    def color_status(val):
        return 'background-color: #d4edda' if val == 'Completed' else 'background-color: #f8d7da'
    
    styled_df = df_status.style.map(color_status, subset=['Status'])
    st.dataframe(styled_df, width='stretch', hide_index=True)
    
    # Show all grades table
    st.markdown("---")
    st.markdown("### All Grades")
    all_grades = list(grade_db.grades.find())
    if all_grades:
        df = pd.DataFrame(all_grades)
        df = df[['student_name', 'assignment_name', 'grade', 'comments', 'created_at']]
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No grades yet.")



def view_feedback(db):
    """View student feedback"""
    st.markdown("## 💬 Student Feedback")
    feedback_db = db.client[config.FEEDBACK_DB]
    feedbacks = list(feedback_db.feedback.find().sort("created_at", -1))
    
    if not feedbacks:
        st.info("No feedback yet.")
        return
    
    for fb in feedbacks:
        with st.container():
            st.markdown(f"**{fb['student_name']}** - *{fb['created_at'][:10]}*")
            st.markdown(f"**Subject:** {fb.get('subject', 'General')}")
            st.markdown(fb['message'])
            if fb.get('response'):
                st.info(f"**Response:** {fb['response']}")
            else:
                col1, col2 = st.columns([3,1])
                with col1:
                    response = st.text_area("Respond", key=f"resp_{fb['_id']}")
                with col2:
                    if st.button("Send", key=f"send_{fb['_id']}"):
                        if response:
                            feedback_db.feedback.update_one(
                                {"_id": fb["_id"]},
                                {"$set": {"response": response, "responded_at": datetime.now().isoformat()}}
                            )
                            send_notification(db, fb['student_name'], "Feedback Response", f"Response to your feedback: {response}", "info")
                            st.success("Response sent.")
                            st.rerun()
            st.markdown("---")

def activity_logs(db):
    """View system activity logs"""
    st.markdown("## 📋 Activity Logs")
    activity_db = db.client[config.ACTIVITY_DB]
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        users = ["All"] + activity_db.logs.distinct("username")
        selected_user = st.selectbox("User", users)
    with col2:
        days = st.selectbox("Last N days", [1, 7, 30, 90, 365], index=1)
    
    query = {}
    if selected_user != "All":
        query["username"] = selected_user
    if days:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        query["timestamp"] = {"$gte": cutoff}
    
    logs = list(activity_db.logs.find(query).sort("timestamp", -1).limit(500))
    
    if logs:
        df = pd.DataFrame(logs)
        df['timestamp'] = df['timestamp'].apply(lambda x: x[:19] if x else '')
        st.dataframe(df[['timestamp', 'username', 'action', 'details']], width='stretch', hide_index=True)
    else:
        st.info("No logs found.")

def system_settings(db):
    """System settings for admin"""
    st.markdown("## ⚙️ System Settings")
    settings_db = db.client[config.SETTINGS_DB]
    
    # Load or create settings
    settings = settings_db.settings.find_one({"_id": "global"})
    if not settings:
        settings = {
            "_id": "global",
            "allow_registration": True,
            "default_theme": "light",
            "session_timeout": 3600,
            "github_sync_interval": 3600,
            "email_notifications": False
        }
        settings_db.settings.insert_one(settings)
    
    with st.form("settings_form"):
        allow_reg = st.checkbox("Allow new registrations", value=settings.get('allow_registration', True))
        theme = st.selectbox("Default theme", ["light", "dark"], index=0 if settings.get('default_theme')=='light' else 1)
        timeout = st.number_input("Session timeout (seconds)", min_value=300, max_value=86400, value=settings.get('session_timeout', 3600))
        sync_int = st.number_input("GitHub sync interval (seconds)", min_value=60, value=settings.get('github_sync_interval', 3600))
        email_notif = st.checkbox("Enable email notifications", value=settings.get('email_notifications', False))
        
        if st.form_submit_button("Save Settings"):
            settings_db.settings.update_one(
                {"_id": "global"},
                {"$set": {
                    "allow_registration": allow_reg,
                    "default_theme": theme,
                    "session_timeout": timeout,
                    "github_sync_interval": sync_int,
                    "email_notifications": email_notif,
                    "updated_at": datetime.now().isoformat()
                }}
            )
            add_activity_log(db, st.session_state.username, "Settings", "Updated system settings")
            st.success("Settings saved.")
            st.rerun()
    
    # Maintenance actions
    st.markdown("---")
    st.markdown("### 🛠️ Maintenance")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clean empty collections", width='stretch'):
            from database import cleanup_empty_collections
            cleanup_empty_collections()
            st.success("Empty collections removed.")
    with col2:
        if st.button("📊 Rebuild indexes", width='stretch'):
            from database import create_indexes
            create_indexes()
            st.success("Indexes rebuilt.")