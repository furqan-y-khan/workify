import streamlit as st
import os
from datetime import datetime
from utils.database import get_db, init_db
from pages.dashboard import show_dashboard
from pages.landing import show_landing
from pages.profile import show_profile
from pages.messages import show_messages
from pages.reviews import show_reviews
from pages.applications import show_applications
from pages.subscription import show_subscription
from pages.apply_job import show_apply_job
from utils.google_auth import handle_google_callback, restore_session
from pages.dashboard import (
    show_job_seeker_dashboard,
    show_job_poster_dashboard,
    show_admin_dashboard
)

# Initialize database
init_db()

# Import necessary modules for page navigation
try:
    from pages.apply_job import apply_job, show_apply_job
except ImportError:
    from pages import apply_job

def main():
    """Main application entry point"""
    # Hide sidebar completely before Streamlit renders
    st.set_page_config(
        page_title="Workify",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items=None
    )
    
    # Custom CSS to make the interface prettier
    st.markdown("""
    <style>
        /* Base Styles */
        :root {
            --primary-color: #4A6FDC;
            --primary-light: #E0E7FF;
            --text-color: #333333;
            --text-light: #666666;
            --background-light: #f0f2f6;
            --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-color);
        }
        
        /* Card Styles */
        div.stExpander {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: var(--shadow);
        }
        
        div.stExpander > details {
            background-color: white;
            padding: 0.5rem 1rem;
            border-radius: 10px;
        }
        
        div.stExpander > details > summary {
            font-weight: 600;
            cursor: pointer;
            padding: 0.5rem 0;
        }
        
        /* Input Fields */
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            padding: 0.5rem 1rem;
        }
        
        .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px var(--primary-light);
        }
        
        /* Buttons */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(74, 111, 220, 0.2);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            font-weight: 500;
            background-color: #f8f9fa;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: white;
            border-top: 2px solid var(--primary-color);
        }
        
        /* Status colors */
        .blue { color: #4A6FDC; }
        .green { color: #09AB3B; }
        .red { color: #D30000; }
        .gray { color: #666666; }
        
        /* App header/title */
        h1, h2, h3 {
            color: var(--text-color);
        }
        
        /* Fix for mobile responsiveness */
        @media (max-width: 640px) {
            .row-widget.stButton {
                width: 100%;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Try to restore session first if not logged in
    if 'user' not in st.session_state:
        restore_session()
    
    # Initialize session state if it doesn't exist
    if 'page' not in st.session_state:
        # Default to landing page if no user is logged in
        st.session_state['page'] = 'landing'
    
    # Get current page from query params if available
    query_params = st.query_params
    query_page = query_params.get('page')
    
    # Use query parameter to set page if it exists and is valid
    valid_pages = [
        'landing', 'seeker_dashboard', 'poster_dashboard', 'admin_dashboard',
        'profile', 'messages', 'reviews', 'applications', 'subscription', 'apply_job',
        'dashboard', 'browse_jobs'
    ]
    
    if query_page and query_page in valid_pages:
        # Handle special case for dashboard - direct to appropriate role-specific dashboard
        if query_page == 'dashboard' and 'user' in st.session_state:
            user_role = st.session_state['user'].get('role')
            if user_role == 'Job Seeker':
                st.session_state['page'] = 'seeker_dashboard'
            elif user_role == 'Job Poster':
                st.session_state['page'] = 'poster_dashboard'
            elif user_role == 'Administrator':
                st.session_state['page'] = 'admin_dashboard'
            else:
                st.session_state['page'] = 'landing'
        else:
            st.session_state['page'] = query_page
    
    # Get current page from session state
    current_page = st.session_state.get('page', 'landing')
    
    # Update URL when page changes
    if current_page != query_page:
        st.query_params['page'] = current_page
    
    # Make sure user is logged in for protected pages
    protected_pages = [
        'seeker_dashboard', 'poster_dashboard', 'admin_dashboard',
        'profile', 'messages', 'reviews', 'applications', 'subscription', 'apply_job',
        'browse_jobs'
    ]
    
    if current_page in protected_pages and 'user' not in st.session_state:
        st.warning("Please log in to continue")
        st.session_state['page'] = 'landing'
        st.query_params['page'] = 'landing'
        current_page = 'landing'
    
    # Route to appropriate page
    try:
        if current_page == 'landing':
            show_landing()
        elif current_page == 'seeker_dashboard':
            if 'user' in st.session_state and st.session_state['user']['role'] == 'Job Seeker':
                show_job_seeker_dashboard(st.session_state['user'])
            else:
                st.warning("You don't have access to this page")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'poster_dashboard':
            if 'user' in st.session_state and st.session_state['user']['role'] == 'Job Poster':
                show_job_poster_dashboard(st.session_state['user'])
            else:
                st.warning("You don't have access to this page")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'admin_dashboard':
            if 'user' in st.session_state and st.session_state['user']['role'] == 'Administrator':
                show_admin_dashboard(st.session_state['user'])
            else:
                st.warning("You don't have access to this page")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'profile':
            if 'user' in st.session_state:
                show_profile()
            else:
                st.warning("Please log in to view your profile")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'messages':
            if 'user' in st.session_state:
                show_messages()
            else:
                st.warning("Please log in to view your messages")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'reviews':
            if 'user' in st.session_state:
                show_reviews()
            else:
                st.warning("Please log in to view reviews")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'applications':
            if 'user' in st.session_state:
                show_applications()
            else:
                st.warning("Please log in to view your applications")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'subscription':
            if 'user' in st.session_state:
                show_subscription()
            else:
                st.warning("Please log in to manage your subscription")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'apply_job':
            if 'user' in st.session_state:
                # Check if we have a job_id to apply for
                if 'apply_job_id' not in st.session_state:
                    st.error("No job selected to apply for")
                    
                    # Check if there's a previous page to return to
                    if 'prev_page' in st.session_state:
                        prev_page = st.session_state['prev_page']
                        # Map 'dashboard' to the appropriate dashboard based on role
                        if prev_page == 'dashboard' and 'user' in st.session_state:
                            if st.session_state['user']['role'] == 'Job Seeker':
                                prev_page = 'seeker_dashboard'
                            elif st.session_state['user']['role'] == 'Job Poster':
                                prev_page = 'poster_dashboard'
                        
                        st.session_state['page'] = prev_page
                    else:
                        # Default to seeker dashboard if no previous page
                        st.session_state['page'] = 'seeker_dashboard'
                    
                    st.rerun()
                else:
                    # Debug info about application
                    debug_mode = st.sidebar.checkbox("Debug Mode", value=False)
                    if debug_mode:
                        st.sidebar.write(f"Apply Job ID: {st.session_state['apply_job_id']}")
                        st.sidebar.write(f"User ID: {st.session_state['user']['user_id']}")
                        if 'prev_page' in st.session_state:
                            st.sidebar.write(f"Previous Page: {st.session_state['prev_page']}")
                    
                    # For pages that need a job_id parameter
                    job_id = st.session_state.get('apply_job_id', None)
                    if debug_mode:
                        st.sidebar.write(f"Job ID for apply page: {job_id}")
                    
                    # Handle the case when no job ID is provided
                    if job_id is None:
                        st.warning("No job selected. Please select a job first.")
                        st.session_state['page'] = 'dashboard'
                        st.rerun()
                    
                    try:
                        # Try to call show_apply_job which is the compatibility function
                        if 'show_apply_job' in globals() or 'apply_job' in locals():
                            show_apply_job()
                        # Fallback to importing and calling directly
                        else:
                            try:
                                from pages.apply_job import apply_job, show_apply_job
                                show_apply_job()
                            except ImportError:
                                st.error("Could not load the application page. Please try again.")
                                st.session_state['page'] = 'dashboard'
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error loading application page: {str(e)}")
                        if debug_mode:
                            st.write(f"Error details: {str(e)}")
                        st.session_state['page'] = 'dashboard'
                        st.rerun()
            else:
                st.warning("Please log in to apply for jobs")
                st.session_state['page'] = 'landing'
                st.rerun()
        elif current_page == 'browse_jobs':
            # Redirect to seeker dashboard since the browse jobs functionality is there
            if 'user' in st.session_state and st.session_state['user']['role'] == 'Job Seeker':
                # Just set the tab directly to Browse Jobs in the dashboard
                st.session_state['page'] = 'seeker_dashboard'
                st.rerun()
            else:
                st.warning("You don't have access to this page")
                st.session_state['page'] = 'landing'
                st.rerun()
        else:
            st.warning(f"Invalid page: {current_page}")
            st.session_state['page'] = 'landing'
            st.query_params['page'] = 'landing'
            show_landing()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        # Provide a way for users to recover
        if st.button("Return to Home"):
            st.session_state['page'] = 'landing'
            st.query_params['page'] = 'landing'
            st.rerun()

if __name__ == "__main__":
    main()

