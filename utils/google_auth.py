import json
import secrets
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import streamlit as st
from datetime import datetime
from utils.database import get_db, create_or_update_user
from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    GOOGLE_SCOPES
)

# OAuth 2.0 client configuration
CLIENT_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "auth_uri": GOOGLE_AUTH_URL,
        "token_uri": GOOGLE_TOKEN_URL,
        "redirect_uris": [GOOGLE_REDIRECT_URI]
    }
}

def get_google_auth_url(role):
    """Get Google OAuth URL for the specified role"""
    try:
        # Store role in session state for callback
        st.session_state['oauth_role'] = role
        st.session_state['selected_role'] = role  # Store in both places for redundancy
        
        # Create OAuth flow instance
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=GOOGLE_SCOPES
        )
        
        # Set redirect URI
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        
        # Generate authorization URL with state parameter containing role
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=role  # Include role in state parameter
        )
        
        # Store state in session
        st.session_state['oauth_state'] = state
        
        return auth_url
        
    except Exception as e:
        st.error(f"Error generating auth URL: {str(e)}")
        return None

def handle_google_callback():
    """Handle the Google OAuth callback"""
    try:
        # Get the authorization code and state from query parameters
        code = st.query_params.get('code')
        state = st.query_params.get('state')
        
        if not code:
            st.error("No authorization code received")
            return None

        # Get role from state parameter or session state
        role = state or st.session_state.get('oauth_role') or st.session_state.get('selected_role')
        if not role:
            st.error("No role specified for registration")
            return None

        # Create OAuth flow instance
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        
        # Get credentials and create service
        credentials = flow.credentials
        service = build('oauth2', 'v2', credentials=credentials)
        
        # Get user info
        user_info = service.userinfo().get().execute()
        
        # Create or update user in database
        user = create_or_update_user(user_info, role)
        
        if user:
            # Store user info in session
            st.session_state['user'] = user
            
            # Store credentials in session
            st.session_state['credentials'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            # Clear OAuth related session data
            for key in ['oauth_role', 'oauth_state', 'selected_role']:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Clear query parameters
            st.query_params.clear()
            
            # Set page based on user role
            if user['role'] == 'Job Seeker':
                st.session_state['page'] = 'seeker_dashboard'
            elif user['role'] == 'Job Poster':
                st.session_state['page'] = 'poster_dashboard'
            elif user['role'] == 'Administrator':
                if user.get('email') == 'furkaan309@gmail.com':
                    st.session_state['page'] = 'admin_dashboard'
                else:
                    st.error("You are not authorized to access the administrator dashboard")
                    clear_session()
                    st.session_state['page'] = 'landing'
            else:
                st.session_state['page'] = 'landing'
            
            st.rerun()
            
        return user_info
        
    except Exception as e:
        st.error(f"Error in OAuth callback: {str(e)}")
        # Clear query parameters and redirect to landing
        st.query_params.clear()
        st.session_state['page'] = 'landing'
        st.rerun()
        return None

def restore_session():
    """Restore user session from stored credentials"""
    try:
        if 'credentials' in st.session_state and 'user' not in st.session_state:
            creds_dict = st.session_state['credentials']
            credentials = Credentials(
                token=creds_dict['token'],
                refresh_token=creds_dict['refresh_token'],
                token_uri=creds_dict['token_uri'],
                client_id=creds_dict['client_id'],
                client_secret=creds_dict['client_secret'],
                scopes=creds_dict['scopes']
            )
            
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            # Get user from database
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_info['id'],))
                user = cursor.fetchone()
                if user:
                    st.session_state['user'] = dict(user)
                    
                    # Set appropriate page based on user role
                    if user['role'] == 'Job Seeker':
                        st.session_state['page'] = 'seeker_dashboard'
                    elif user['role'] == 'Job Poster':
                        st.session_state['page'] = 'poster_dashboard'
                    elif user['role'] == 'Administrator' and user.get('email') == 'furkaan309@gmail.com':
                        st.session_state['page'] = 'admin_dashboard'
                    else:
                        st.session_state['page'] = 'landing'
                    
                    return True
            finally:
                conn.close()
    except Exception as e:
        st.error(f"Error restoring session: {str(e)}")
        clear_session()
    return False

def clear_session():
    """Clear all session data"""
    st.session_state.clear()
    st.query_params.clear()
