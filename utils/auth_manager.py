import streamlit as st
import sqlite3
import bcrypt
import logging
from datetime import datetime
from utils.database import get_db, create_or_update_user
from config import ADMIN_PASSWORD_HASH
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    ADMIN_EMAIL = 'furkaan309@gmail.com'
    # Store hashed password instead of plaintext
    ADMIN_PASSWORD_HASH = ADMIN_PASSWORD_HASH  # Hashed version of the password

    def __init__(self):
        """Initialize the auth manager"""
        self.client_secrets_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'client_secret.json'
        )
        
        # Load client configuration
        with open(self.client_secrets_file) as f:
            self.client_config = json.load(f)
            
        self.SCOPES = [
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email'
        ]

    @staticmethod
    def login(email, password, role=None):
        """Handle email/password login"""
        if not email or not password:
            st.error("Please fill in all fields")
            return False
            
        try:
            # Connect to database
            conn = get_db()
            cursor = conn.cursor()
            
            # Get user by email first
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                logger.warning(f"Login attempt failed: User not found - {email}")
                st.error("Invalid email or password")
                return False
            
            # Check password using secure comparison
            if not AuthManager.verify_password(password, user['password']):
                logger.warning(f"Login attempt failed: Invalid password - {email}")
                st.error("Invalid email or password")
                return False

            # Validate role if provided
            if role and user['role'] != role:
                if role == 'Administrator' and email != AuthManager.ADMIN_EMAIL:
                    logger.warning(f"Unauthorized admin access attempt: {email}")
                    st.error("You are not authorized to sign in as an Administrator")
                    return False
                logger.warning(f"Role mismatch: {email} attempted to login as {role}")
                st.error(f"Your account is not registered as a {role}")
                return False
            
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user['user_id'])
            )
            conn.commit()
            
            # Set session state
            user_data = dict(user)
            user_data.pop('password', None)  # Remove password from session data
            st.session_state['user'] = user_data
            
            # Set dashboard based on role
            dashboard_page = f"{user['role'].lower().replace(' ', '_')}_dashboard"
            st.session_state['page'] = dashboard_page
            st.query_params['page'] = dashboard_page
            
            logger.info(f"User logged in successfully: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            st.error("An error occurred during login")
            return False
            
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    @staticmethod
    def signup(name, email, password, confirm_password, role):
        """Handle email/password signup"""
        try:
            # Validate inputs
            if not all([name, email, password, confirm_password, role]):
                st.error("Please fill in all fields")
                return False
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return False
            
            if len(password) < 8:
                st.error("Password must be at least 8 characters long")
                return False

            # Validate administrator signup
            if role == 'Administrator' and email != AuthManager.ADMIN_EMAIL:
                st.error("You are not authorized to sign up as an Administrator")
                return False
                
            # Connect to database
            conn = get_db()
            cursor = conn.cursor()
            
            try:
                # Check if email exists
                cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    st.error("Email already registered")
                    return False
                
                # Create user
                cursor.execute("""
                    INSERT INTO users (
                        name, email, password, role, created_at,
                        company_name, company_description
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, 
                    email, 
                    password,
                    role, 
                    datetime.now().isoformat(),
                    name if role == 'Job Poster' else None,
                    "Tell us about your company" if role == 'Job Poster' else None
                ))
                
                conn.commit()
                
                # Get the created user
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
                
                # Set session state
                st.session_state['user'] = dict(user)
                
                # Show success message
                st.success(f"Account created successfully! Welcome {name}!")
                
                # Clear query parameters and redirect to dashboard
                st.query_params.clear()
                st.query_params['page'] = 'dashboard'
                st.rerun()
                
                return True
                
            except sqlite3.Error as e:
                print(f"Database error during signup: {str(e)}")
                st.error("Database error occurred during signup")
                return False
                
        except Exception as e:
            print(f"Signup error: {str(e)}")
            st.error("An error occurred during signup")
            return False
            
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    def get_google_auth_url(self, role):
        """Get Google OAuth URL for the specified role"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=self.client_config['web']['redirect_uris'][0]
        )
        
        # Store role in session state
        st.session_state['pending_role'] = role
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return auth_url
    
    def handle_google_callback(self, auth_response):
        """Handle Google OAuth callback and create/update user"""
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                redirect_uri=self.client_config['web']['redirect_uris'][0]
            )
            
            # Get credentials from callback
            flow.fetch_token(authorization_response=auth_response)
            credentials = flow.credentials
            
            # Get user info from Google
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            # Get role from session state
            role = st.session_state.get('pending_role', 'Job Seeker')
            
            # Create or update user in database
            user = create_or_update_user(user_info, role)
            
            # Store user in session state
            st.session_state['user'] = user
            st.session_state['credentials'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            # Clear pending role
            if 'pending_role' in st.session_state:
                del st.session_state['pending_role']
            
            return True
            
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return False
    
    def restore_session(self):
        """Restore user session from stored credentials"""
        try:
            if 'credentials' in st.session_state:
                credentials = Credentials(**st.session_state['credentials'])
                
                if credentials and not credentials.expired:
                    service = build('oauth2', 'v2', credentials=credentials)
                    user_info = service.userinfo().get().execute()
                    
                    # Get user from database
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_info['id'],))
                    user = cursor.fetchone()
                    conn.close()
                    
                    if user:
                        st.session_state['user'] = dict(user)
                        return True
            
            return False
            
        except Exception as e:
            st.error(f"Session restoration failed: {str(e)}")
            return False
    
    def logout(self):
        """Log out the current user"""
        if 'user' in st.session_state:
            del st.session_state['user']
        if 'credentials' in st.session_state:
            del st.session_state['credentials']
        if 'pending_role' in st.session_state:
            del st.session_state['pending_role']

    @staticmethod
    def is_admin(user=None):
        """Check if the current user is an administrator"""
        if not user:
            user = st.session_state.get('user')
        return user and user.get('email') == AuthManager.ADMIN_EMAIL and user.get('role') == 'Administrator'

    @staticmethod
    def require_auth(role=None):
        """Decorator to require authentication and optionally a specific role"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                user = st.session_state.get('user')
                if not user:
                    logger.warning("Unauthorized access attempt: No user in session")
                    st.query_params['page'] = 'login'
                    st.rerun()
                elif role and user.get('role') != role and not AuthManager.is_admin(user):
                    logger.warning(f"Unauthorized access attempt: {user.get('email')} tried to access {role} page")
                    st.error("You don't have permission to access this page")
                    return
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def verify_password(password, hashed_password):
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def create_user(name, email, password, role, company_name=None, company_description=None):
        """Create a new user"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            hashed_password = AuthManager.hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (name, email, password, role, company_name, company_description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, hashed_password, role, company_name, company_description, datetime.now().isoformat()))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logging.error(f"Error creating user: {str(e)}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def verify_user(email, password):
        """Verify user credentials"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user and AuthManager.verify_password(password, user['password']):
                return user
            return None
        except Exception as e:
            logging.error(f"Error verifying user: {str(e)}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """Update user information"""
        conn = get_db()
        try:
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            values = []
            for key, value in kwargs.items():
                if key == 'password':
                    value = AuthManager.hash_password(value)
                update_fields.append(f"{key} = ?")
                values.append(value)
            
            if not update_fields:
                return False
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error updating user: {str(e)}")
            return False
        finally:
            conn.close()