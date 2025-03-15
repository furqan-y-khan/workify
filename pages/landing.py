import streamlit as st
from utils.database import get_db
from utils.location_services import show_location_picker, calculate_distance
import folium
from streamlit_folium import folium_static
from utils.google_auth import get_google_auth_url
import webbrowser
from streamlit.components.v1 import html

def show_landing():
    """Show the landing page with role selection"""
    # Handle OAuth callback first
    if 'code' in st.query_params:
        from utils.google_auth import handle_google_callback
        user_info = handle_google_callback()
        if user_info and 'user' in st.session_state:
            # Route to appropriate dashboard based on role
            role = st.session_state['user']['role']
            if role == 'Job Seeker':
                st.session_state['page'] = 'seeker_dashboard'
                st.rerun()
            elif role == 'Job Poster':
                st.session_state['page'] = 'poster_dashboard'
                st.rerun()
            elif role == 'Administrator':
                if st.session_state['user'].get('email') == 'furkaan309@gmail.com':
                    st.session_state['page'] = 'admin_dashboard'
                    st.rerun()
                else:
                    st.error("You are not authorized to access the administrator dashboard")
                    st.session_state.clear()
                    st.rerun()
            return  # Exit function after setting redirect
    
    # Check if user is already logged in
    if 'user' in st.session_state:
        role = st.session_state['user']['role']
        if role == 'Job Seeker':
            st.session_state['page'] = 'seeker_dashboard'
            st.rerun()
        elif role == 'Job Poster':
            st.session_state['page'] = 'poster_dashboard'
            st.rerun()
        elif role == 'Administrator' and st.session_state['user'].get('email') == 'furkaan309@gmail.com':
            st.session_state['page'] = 'admin_dashboard'
            st.rerun()
        return  # Exit function if user is logged in
    
    # Custom CSS for landing page
    st.markdown("""
        <style>
            .main-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            .header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .header h1 {
                font-size: 3.5rem;
                margin-bottom: 1rem;
                color: #4A6FDC;
                display: none;
            }
            .header p {
                font-size: 1.2rem;
                color: #5f6368;
                margin: 1.5rem auto;
                max-width: 800px;
            }
            .logo-container {
                text-align: center;
                margin-bottom: 1rem;
            }
            .role-card {
                background: white;
                border-radius: 8px;
                padding: 2rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            .role-card:hover {
                transform: translateY(-5px);
            }
            .role-card h3 {
                color: #4A6FDC;
                margin-bottom: 1rem;
            }
            .role-card p {
                color: #5f6368;
                margin-bottom: 1.5rem;
            }
            .google-btn {
                display: inline-block;
                background-color: #4A6FDC;
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 4px;
                text-align: center;
                width: 100%;
                margin-top: auto;
                transition: background-color 0.2s;
            }
            .google-btn:hover {
                background-color: #5C33B8;
            }
            .brand-name {
                font-size: 1rem;
                color: #666;
                margin-top: 0.5rem;
                font-style: italic;
            }
            .admin-link {
                position: fixed;
                bottom: 20px;
                right: 20px;
                font-size: 14px;
                color: #5f6368;
                text-decoration: none;
                padding: 8px 16px;
                border-radius: 20px;
                background: rgba(255,255,255,0.9);
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .admin-link:hover {
                background: white;
                color: #4A6FDC;
            }
            .features-section {
                margin-top: 4rem;
                text-align: center;
            }
            .feature-card {
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin: 1rem 0;
            }
            .how-it-works {
                padding: 3rem 0;
                text-align: center;
            }
            .how-it-works h2 {
                margin-bottom: 2rem;
                color: #4A6FDC;
            }
            .step-container {
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                gap: 2rem;
            }
            .step-card {
                flex: 1;
                min-width: 250px;
                padding: 2rem;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .step-icon {
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
            .recent-jobs {
                margin-top: 4rem;
                padding: 2rem;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .job-card {
                padding: 1rem;
                border-bottom: 1px solid #eee;
            }
            .job-card:last-child {
                border-bottom: none;
            }
            .stApp {
                margin-top: 0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Main container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header section with logo
    st.markdown("""
        <div class="header">
            <div class="logo-container">
                <div style="text-align: center; max-width: 240px; margin: 0 auto;">
                    <h2 style="font-size: 32px; font-weight: bold; color: #4A6FDC; margin-bottom: 0;">Workify</h2>
                    <p style="font-size: 14px; color: #666; margin-top: 5px;">by LastAppStanding</p>
                </div>
            </div>
            <p>Connect with local service providers or find work opportunities in your area</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Role selection cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="role-card">
            <h3>🔍 Job Seeker</h3>
            <p>Looking for your next opportunity? Browse local jobs and connect with employers. Get started with:</p>
            <ul>
                <li>Browse local job opportunities</li>
                <li>Easy application process</li>
                <li>Track your applications</li>
                <li>Professional profile builder</li>
            </ul>
        """, unsafe_allow_html=True)
        auth_url = get_google_auth_url("Job Seeker")
        if auth_url:
            st.markdown(f'<a href="{auth_url}" class="google-btn" target="_self">Continue with Google</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="role-card">
            <h3>📢 Job Poster</h3>
            <p>Need skilled professionals? Post jobs and find qualified local talent. Get started with:</p>
            <ul>
                <li>Post job opportunities</li>
                <li>Review applications</li>
                <li>Message candidates</li>
                <li>Manage your listings</li>
            </ul>
        """, unsafe_allow_html=True)
        auth_url = get_google_auth_url("Job Poster")
        if auth_url:
            st.markdown(f'<a href="{auth_url}" class="google-btn" target="_self">Continue with Google</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # How it Works section
    st.markdown("""
        <div class="how-it-works">
            <h2>How It Works</h2>
            <div class="step-container">
                <div class="step-card">
                    <div class="step-icon">📍</div>
                    <h3>Find</h3>
                    <p>Discover skilled professionals in your area</p>
                </div>
                <div class="step-card">
                    <div class="step-icon">📝</div>
                    <h3>Connect</h3>
                    <p>Apply for jobs or hire professionals</p>
                </div>
                <div class="step-card">
                    <div class="step-icon">⭐</div>
                    <h3>Review</h3>
                    <p>Share your experience and build trust</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Recent Jobs section
    st.markdown('<div class="recent-jobs">', unsafe_allow_html=True)
    st.subheader("Recent Job Postings")
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT j.title, j.location, j.job_type, j.trade_category,
                   u.company_name, u.name as poster_name
            FROM jobs j
            JOIN users u ON j.job_poster_id = u.user_id
            WHERE j.status = 'Open'
            ORDER BY j.created_at DESC
            LIMIT 5
        """)
        
        jobs = cursor.fetchall()
        
        if jobs:
            for job in jobs:
                company = job['company_name'] or job['poster_name']
                st.markdown(f"""
                    <div class="job-card">
                        <h4>{job['title']}</h4>
                        <p>🏢 {company}</p>
                        <p>📍 {job['location']} | 💼 {job['job_type']} | 🔧 {job['trade_category']}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No jobs posted yet")
            
    except Exception as e:
        st.error(f"Error loading recent jobs: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0; color: #666;">
            <p>© 2024 Workify by LastAppStanding. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Admin link
    admin_auth_url = get_google_auth_url("Administrator")
    if admin_auth_url:
        st.markdown(f'<a href="{admin_auth_url}" class="admin-link">Administrator Login</a>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True) 