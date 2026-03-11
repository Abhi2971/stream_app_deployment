# 🚀 Quick Start Guide

Get up and running with Student Assignment Tracker in 5 minutes!

## ⚡ Fast Setup

### Step 1: Clone and Install (2 minutes)

```bash
cd assignment-tracker

#create virtual environment
python -m venv venv
venv\Scripts\activate     
# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure MongoDB (2 minutes)

 **Add your credentials to .env**:
   ```env
   MONGODB_USERNAME=your_username
   MONGODB_PASSWORD=your_password
   MONGODB_CLUSTER=cluster0.xxxxx.mongodb.net
   ```

### Step 3: Initialize Database (30 seconds)

```bash
python database.py
```

You should see:
```
✓ Successfully connected to MongoDB!
✓ Created collection 'users' in database 'LoginData'
✓ Created collection 'questions' in database 'Question'
✓ All databases and collections are ready!
```

### Step 4: Run the Application (30 seconds)

```bash
streamlit run stream_app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## 🎉 You're All Set!

Enjoy using Student Assignment Tracker!

Made with ❤️ using Streamlit
