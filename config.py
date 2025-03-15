import os
from dotenv import load_dotenv
import secrets
import streamlit as st
from datetime import datetime
from requests_oauthlib import OAuth2Session
import bcrypt

# Load environment variables from .env file
load_dotenv()

# Application Settings
APP_NAME = os.getenv('APP_NAME', 'JobCon')
APP_URL = os.getenv('APP_URL', 'http://localhost:8501')

# Security
SESSION_SECRET = os.getenv('SESSION_SECRET', secrets.token_urlsafe(32))
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', 'default_hash_for_development')

# Google OAuth Settings
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501/callback')
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
GOOGLE_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
]

# Database Settings
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'jobcon.db')

# Email Settings
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'JobCon <noreply@jobcon.com>')

# Payment Settings
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Map Services
MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN')

# Admin configuration
ADMIN_EMAIL = 'furkaan309@gmail.com'
ADMIN_PASSWORD = 'admin123'  # This should be stored securely
ADMIN_PASSWORD_HASH = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Session configuration
SESSION_EXPIRY = 24 * 60 * 60  # 24 hours in seconds

# Role-based access control
ROLES = ['Job Seeker', 'Job Poster', 'Administrator']

# Job categories
JOB_CATEGORIES = [
    'Plumbing',
    'Electrical',
    'Carpentry',
    'Painting',
    'HVAC',
    'Landscaping',
    'General Maintenance',
    'Cleaning',
    'Moving',
    'Other'
]

# Job types
JOB_TYPES = [
    'One-time Job',
    'Regular Work',
    'Emergency Service',
    'Project Based'
]

# Payment types
PAYMENT_TYPES = [
    'Fixed Price',
    'Hourly Rate',
    'To Be Discussed'
]

# Urgency levels
URGENCY_LEVELS = [
    'Low',
    'Medium',
    'High',
    'Emergency'
]

# Application statuses
APPLICATION_STATUSES = [
    'Pending',
    'Under Review',
    'Accepted',
    'Rejected',
    'Completed',
    'Cancelled'
]

# Review settings
MIN_RATING = 1
MAX_RATING = 5

# File upload settings
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Pagination settings
ITEMS_PER_PAGE = 10

# Search settings
SEARCH_RADIUS_KM = 50  # Default search radius in kilometers

# Notification settings
NOTIFICATION_TYPES = [
    'new_message',
    'application_update',
    'review_received',
    'job_completed'
]

# Security settings
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_REQUIRE_NUMBERS = True
MAX_LOGIN_ATTEMPTS = 5
LOGIN_COOLDOWN_MINUTES = 15

# API rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Cache settings
CACHE_TIMEOUT = 300  # 5 minutes

# Error messages
ERROR_MESSAGES = {
    'auth': {
        'invalid_credentials': 'Invalid email or password',
        'account_locked': 'Account temporarily locked. Please try again later',
        'email_exists': 'Email already registered',
        'weak_password': 'Password does not meet security requirements',
        'unauthorized': 'You are not authorized to access this resource'
    },
    'validation': {
        'required_field': 'This field is required',
        'invalid_email': 'Please enter a valid email address',
        'password_mismatch': 'Passwords do not match',
        'invalid_file': 'Invalid file type or size'
    }
}

# Success messages
SUCCESS_MESSAGES = {
    'auth': {
        'login': 'Successfully logged in',
        'logout': 'Successfully logged out',
        'signup': 'Account created successfully'
    },
    'profile': {
        'update': 'Profile updated successfully'
    },
    'job': {
        'create': 'Job posted successfully',
        'update': 'Job updated successfully',
        'delete': 'Job deleted successfully'
    }
}

def create_oauth_session():
    """Create an OAuth2Session for Google authentication"""
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not configured")
    
    return OAuth2Session(
        GOOGLE_CLIENT_ID,
        scope=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

def get_google_auth_url(role=None):
    """Generate the Google OAuth authorization URL"""
    try:
        if not GOOGLE_CLIENT_ID:
            st.error("Google authentication is not configured. Please check your .env file.")
            return None
            
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        st.session_state['oauth_state'] = state
        
        # Store role in session state
        if role:
            st.session_state['selected_role'] = role
        
        # Create OAuth session
        oauth = create_oauth_session()
        
        # Get authorization URL
        auth_url, _ = oauth.authorization_url(
            GOOGLE_AUTH_URL,
            state=state,
            access_type="offline",
            prompt="select_account"
        )
        
        return auth_url
    except Exception as e:
        st.error(f"Error generating Google auth URL: {str(e)}")
        return None 

def handle_google_callback():
    """Handle the Google OAuth callback"""
    try:
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            st.error("Google authentication is not configured. Please check your .env file.")
            return False
            
        # Verify state to prevent CSRF
        state = st.query_params.get('state')
        if state != st.session_state.get('oauth_state'):
            st.error("Invalid state parameter. Please try again.")
            return False
            
        # Get authorization code
        code = st.query_params.get('code')
        if not code:
            st.error("No authorization code received. Please try again.")
            return False
            
        # Create OAuth session
        oauth = create_oauth_session()
        
        try:
            # Construct the full authorization response URL
            full_url = f"{APP_URL}?code={code}&state={state}"
            
            # Get tokens
            token = oauth.fetch_token(
                GOOGLE_TOKEN_URL,
                client_secret=GOOGLE_CLIENT_SECRET,
                authorization_response=full_url
            )
            
            # Store token in session state
            st.session_state['google_token'] = token
            
            # Get user info
            user_info = oauth.get(GOOGLE_USERINFO_URL).json()
            
            # Create or update user
            user = {
                'name': user_info['name'],
                'email': user_info['email'],
                'picture': user_info.get('picture'),
                'google_id': user_info['sub']
            }
            
            # Get role from session state
            role = st.session_state.get('selected_role', 'Job Seeker')
            
            # Special handling for Administrator role
            if role == 'Administrator' and user['email'] != AuthManager.ADMIN_EMAIL:
                st.error("You are not authorized to sign in as an Administrator.")
                return False
            
            user['role'] = role
            
            # Login user
            success = AuthManager.google_login(user)
            if success:
                st.success(f"Successfully logged in as {role}")
            return success
            
        except Exception as e:
            print(f"Error during token exchange: {str(e)}")
            st.error(f"Error during token exchange: {str(e)}")
            return False
            
    except Exception as e:
        print(f"An error occurred during Google authentication: {str(e)}")
        st.error(f"An error occurred during Google authentication: {str(e)}")
        return False 

def show_dashboard():
    """Show the appropriate dashboard based on user role"""
    user = st.session_state.get('user')
    if not user:
        st.error("Please log in to access the dashboard")
        st.query_params['page'] = 'login'
        st.rerun()
        return
    
    # Show appropriate dashboard based on role
    if user['role'] == 'Administrator':
        show_admin_dashboard()
    elif user['role'] == 'Job Poster':
        show_job_poster_dashboard()
    else:  # Job Seeker
        show_job_seeker_dashboard() 