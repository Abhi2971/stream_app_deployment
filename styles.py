"""
Custom CSS Styles for the Application
Provides modern, professional styling with a clean palette
"""

def get_custom_css():
    """Returns custom CSS for the application"""
    return """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
        box-sizing: border-box;
    }
    
    .main {
        padding: 1.5rem;
        background-color: #f8f9fa;
    }
    
    /* Header */
    .app-header {
        background-color: #ffffff;
        padding: 1.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #3498db;
    }
    
    .app-header h1 {
        color: #2c3e50;
        margin: 0;
        font-weight: 600;
        font-size: 1.8rem;
    }
    
    .app-header p {
        color: #7f8c8d;
        margin: 0.5rem 0 0 0;
    }
    
    /* Cards */
    .metric-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #ecf0f1;
        margin-bottom: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .metric-card h3 {
        color: #7f8c8d;
        margin: 0 0 0.5rem 0;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        text-align: center;
    }
    
    .status-badge.completed {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-badge.pending {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .status-badge.in-progress {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-badge.info {
        background-color: #d1ecf1;
        color: #0c5460;
    }
    
    /* Assignment Card */
    .assignment-card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 6px;
        border: 1px solid #ecf0f1;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s;
        color: #2c3e50;  /* Added */
    }
    
    .assignment-card.completed {
        border-left: 3px solid #27ae60;
    }
    
    .assignment-card.pending {
        border-left: 3px solid #e74c3c;
    }
    
    .assignment-card strong {
        color: #2c3e50;  /* Added */
    }
    .assignment-card small {
        color: #7f8c8d;  /* Added */
    }
    .assignment-card:hover {
        border-color: #3498db;
    }
    /* Progress Bar */
    .progress-container {
        background-color: #ecf0f1;
        border-radius: 6px;
        height: 8px;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        background-color: #3498db;
        border-radius: 6px;
        transition: width 0.3s ease;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #2980b9;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #2c3e50;
        color: white;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background-color: #34495e;
        color: white;
        width: 100%;
        text-align: left;
        border: none;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #3d566e;
    }
    
    /* Info Boxes */
    .info-box, .success-box, .warning-box, .error-box {
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border-left-color: #17a2b8;
    }
    
    .success-box {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    
    .error-box {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
    
    /* Tables */
    .dataframe {
        border: 1px solid #ecf0f1;
        border-radius: 6px;
        overflow: hidden;
    }
    
    .dataframe thead tr {
        background-color: #3498db;
        color: white;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #ecf0f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #b0bec5;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #90a4ae;
    }
    </style>
    """

def get_chart_config():
    """Returns plotly chart configuration"""
    return {
        'displayModeBar': False,
        'responsive': True,
        'displaylogo': False
    }

def create_metric_card(title, value, change=None, color="primary"):
    """Creates an HTML metric card"""
    change_html = ""
    if change is not None:
        change_class = "positive" if change >= 0 else "negative"
        change_symbol = "▲" if change >= 0 else "▼"
        change_html = f'<p class="change {change_class}">{change_symbol} {abs(change)}%</p>'
    
    return f"""
    <div class="metric-card">
        <h3>{title}</h3>
        <p class="value">{value}</p>
        {change_html}
    </div>
    """

def create_progress_bar(percentage, label=""):
    """Creates an HTML progress bar"""
    return f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
            <span style="font-weight: 500; color: #2c3e50;">{label}</span>
            <span style="color: #3498db; font-weight: 600;">{percentage}%</span>
        </div>
        <div class="progress-container">
            <div class="progress-bar" style="width: {percentage}%;"></div>
        </div>
    </div>
    """

def create_status_badge(status):
    """Creates a status badge HTML"""
    status_lower = status.lower()
    return f'<span class="status-badge {status_lower}">{status}</span>'