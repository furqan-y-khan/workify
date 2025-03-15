import streamlit as st

def show_sidebar():
    """Display the sidebar with role-specific navigation"""
    user = st.session_state.get('user')
    if not user:
        return
    
    with st.sidebar:
        st.write(f"Welcome, {user['name']}")
        st.markdown("---")
        
        # Role-specific navigation
        if user['role'] == 'Job Seeker':
            show_job_seeker_sidebar()
        elif user['role'] == 'Job Poster':
            show_job_poster_sidebar()
        elif user['role'] == 'Administrator':
            show_admin_sidebar()

def navigate_to(page):
    """Handle navigation to a specific page"""
    st.session_state['page'] = page
    st.query_params['page'] = page
    st.rerun()

def show_job_seeker_sidebar():
    """Display navigation for job seekers"""
    nav_items = {
        '🏠 Dashboard': {
            'page': 'dashboard',
            'module': 'pages.dashboard',
            'function': 'show_dashboard'
        },
        '🔍 Browse Jobs': {
            'page': 'browse_jobs',
            'module': 'pages.browse_jobs',
            'function': 'show_browse_jobs'
        },
        '📝 My Applications': {
            'page': 'my_applications',
            'module': 'pages.my_applications',
            'function': 'show_my_applications'
        },
        '💬 Messages': {
            'page': 'messages',
            'module': 'pages.messages',
            'function': 'show_messages'
        },
        '👤 Profile': {
            'page': 'profile',
            'module': 'pages.profile',
            'function': 'show_profile'
        }
    }
    
    for label, info in nav_items.items():
        if st.sidebar.button(label, key=f"seeker_{info['page']}", use_container_width=True):
            navigate_to(info['page'])
    
    if st.sidebar.button('🚪 Logout', key="seeker_logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

def show_job_poster_sidebar():
    """Display navigation for job posters"""
    nav_items = {
        '🏠 Dashboard': {
            'page': 'dashboard',
            'module': 'pages.dashboard',
            'function': 'show_dashboard'
        },
        '📢 Post Jobs': {
            'page': 'post_jobs',
            'module': 'pages.post_jobs',
            'function': 'show_post_jobs'
        },
        '📊 My Listings': {
            'page': 'my_listings',
            'module': 'pages.my_listings',
            'function': 'show_my_listings'
        },
        '👥 Applications': {
            'page': 'applications',
            'module': 'pages.applications',
            'function': 'show_applications'
        },
        '💬 Messages': {
            'page': 'messages',
            'module': 'pages.messages',
            'function': 'show_messages'
        },
        '👤 Profile': {
            'page': 'profile',
            'module': 'pages.profile',
            'function': 'show_profile'
        }
    }
    
    for label, info in nav_items.items():
        if st.sidebar.button(label, key=f"poster_{info['page']}", use_container_width=True):
            navigate_to(info['page'])
    
    if st.sidebar.button('🚪 Logout', key="poster_logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

def show_admin_sidebar():
    """Display navigation for administrators"""
    nav_items = {
        '📊 Dashboard': {
            'page': 'dashboard',
            'module': 'pages.dashboard',
            'function': 'show_dashboard'
        },
        '👥 User Management': {
            'page': 'users',
            'module': 'pages.users',
            'function': 'show_users'
        },
        '💼 Job Listings': {
            'page': 'jobs',
            'module': 'pages.jobs',
            'function': 'show_jobs'
        },
        '🚫 Reports': {
            'page': 'reports',
            'module': 'pages.reports',
            'function': 'show_reports'
        }
    }
    
    for label, info in nav_items.items():
        if st.sidebar.button(label, key=f"admin_{info['page']}", use_container_width=True):
            navigate_to(info['page'])
    
    if st.sidebar.button('🚪 Logout', key="admin_logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun() 