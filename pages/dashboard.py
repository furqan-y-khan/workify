import streamlit as st
from utils.database import get_db
from datetime import datetime
from utils.auth_manager import AuthManager
import sqlite3

def get_current_user():
    """Get the current user from session state"""
    if 'user' not in st.session_state or not st.session_state['user']:
        st.error("Please log in to access the dashboard")
        st.session_state['page'] = 'landing'
        st.query_params['page'] = 'landing'
        st.rerun()
    return st.session_state['user']

def show_dashboard():
    """Show the appropriate dashboard based on user role"""
    user = st.session_state.get('user')
    if not user:
        st.error("Please log in to access the dashboard")
        st.session_state['page'] = 'landing'
        st.rerun()
        return
    
    # Show appropriate dashboard based on role
    if user['role'] == 'Job Seeker':
        show_job_seeker_dashboard(user)
    elif user['role'] == 'Job Poster':
        show_job_poster_dashboard(user)
    elif user['role'] == 'Administrator':
        show_admin_dashboard(user)
    else:
        st.error("Invalid user role")
        st.session_state.clear()
        st.rerun()

def show_admin_dashboard(user):
    """Show the administrator dashboard"""
    if not user or user['email'] != AuthManager.ADMIN_EMAIL:
        st.error("Unauthorized access")
        st.session_state['page'] = 'landing'
        st.query_params['page'] = 'landing'
        st.rerun()
        return

    # Add logo and brand name using simpler HTML
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="font-size: 32px; font-weight: bold; color: #4A6FDC; margin-bottom: 0;">Workify</h2>
            <p style="font-size: 14px; color: #666; margin-top: 5px;">by LastAppStanding</p>
        </div>
    """, unsafe_allow_html=True)

    st.title(f"Welcome, {user['name']} 👋")
    
    # Admin Navigation Tabs
    tabs = st.tabs([
        "📊 Overview",
        "👥 Users",
        "💼 Jobs",
        "📝 Applications",
        "⭐ Reviews",
        "⚙️ Settings"
    ])
    
    with tabs[0]:  # Overview
        show_admin_overview()
    
    with tabs[1]:  # Users
        show_user_management()
    
    with tabs[2]:  # Jobs
        show_job_management()
    
    with tabs[3]:  # Applications
        show_admin_applications()
    
    with tabs[4]:  # Reviews
        from pages.reviews import show_admin_reviews
        show_admin_reviews()
    
    with tabs[5]:  # Settings
        show_system_settings()

def show_job_poster_dashboard(user):
    """Show the job poster dashboard"""
    if not user or user['role'] != 'Job Poster':
        st.error("Unauthorized access")
        st.session_state['page'] = 'landing'
        st.query_params['page'] = 'landing'
        st.rerun()
        return
        
    # Add logo and brand name using simpler HTML
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="font-size: 32px; font-weight: bold; color: #4A6FDC; margin-bottom: 0;">Workify</h2>
            <p style="font-size: 14px; color: #666; margin-top: 5px;">by LastAppStanding</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.title(f"Welcome, {user['name']} 👋")
    
    # Add logout button at the top
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
    
    # Job Poster Navigation Tabs
    tabs = st.tabs([
        "📊 Overview",
        "📢 Post Jobs",
        "📋 My Listings",
        "👥 Applications",
        "💬 Messages",
        "⭐ Reviews",
        "💎 Subscription",
        "👤 Profile"
    ])
    
    with tabs[0]:  # Overview
        show_poster_overview(user)
    
    with tabs[1]:  # Post Jobs
        from pages.post_jobs import show_post_jobs
        show_post_jobs()
    
    with tabs[2]:  # My Listings
        show_poster_jobs(user)
    
    with tabs[3]:  # Applications
        show_applications_received(user)
    
    with tabs[4]:  # Messages
        from pages.messages import show_messages
        show_messages()
    
    with tabs[5]:  # Reviews
        from pages.reviews import show_reviews
        show_reviews()
    
    with tabs[6]:  # Subscription
        from pages.subscription import show_subscription
        show_subscription()
    
    with tabs[7]:  # Profile
        from pages.profile import show_profile
        show_profile()

def show_job_seeker_dashboard(user):
    """Show job seeker dashboard overview"""
    # Add logo and brand name using simpler HTML
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="font-size: 32px; font-weight: bold; color: #4A6FDC; margin-bottom: 0;">Workify</h2>
            <p style="font-size: 14px; color: #666; margin-top: 5px;">by LastAppStanding</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.title(f"Welcome back, {user['name']}! 👋")
    
    # Add logout button at the top
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
    
    # Job Seeker Navigation Tabs
    tabs = st.tabs([
        "📊 Overview",
        "🔍 Browse Jobs",
        "📝 My Applications",
        "💼 Portfolio",
        "💬 Messages",
        "⭐ Reviews",
        "💎 Subscription",
        "👤 Profile"
    ])
    
    with tabs[0]:  # Overview
        show_seeker_overview(user)
    
    with tabs[1]:  # Browse Jobs
        show_job_search(user)
    
    with tabs[2]:  # My Applications
        show_my_applications(user)
    
    with tabs[3]:  # Portfolio
        show_seeker_portfolio(user)
    
    with tabs[4]:  # Messages
        from pages.messages import show_messages
        show_messages()
    
    with tabs[5]:  # Reviews
        from pages.reviews import show_reviews
        show_reviews()
    
    with tabs[6]:  # Subscription
        from pages.subscription import show_subscription
        show_subscription()
    
    with tabs[7]:  # Profile
        from pages.profile import show_profile
        show_profile()

def show_seeker_overview(user):
    """Show job seeker dashboard overview"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get application stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as accepted
            FROM applications
            WHERE applicant_id = ?
        """, (user['user_id'],))
        stats = cursor.fetchone()
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Applications", stats['total'] or 0)
        with col2:
            st.metric("Pending", stats['pending'] or 0)
        with col3:
            st.metric("Accepted", stats['accepted'] or 0)
        
        # Recent Activity
        st.subheader("Recent Activity")
        cursor.execute("""
            SELECT a.*, j.title, u.name as poster_name, u.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN users u ON j.job_poster_id = u.user_id
            WHERE a.applicant_id = ?
            ORDER BY a.created_at DESC
            LIMIT 5
        """, (user['user_id'],))
        
        recent = cursor.fetchall()
        if recent:
            for app in recent:
                company = app['company_name'] or app['poster_name']
                st.write(f"Applied to **{app['title']}** at {company} - {app['created_at'][:10]}")
                st.write(f"Status: {app['status']}")
                st.markdown("---")
        else:
            st.info("No recent activity")
        
        # Add suggested jobs section
        st.markdown("---")
        st.subheader("Jobs You Might Like")
        
        # Get the user's skills and location
        cursor.execute("""
            SELECT skills, location, latitude, longitude 
            FROM users 
            WHERE user_id = ?
        """, (user['user_id'],))
        user_data = cursor.fetchone()
        
        if user_data and user_data.get('skills'):
            # Try to find jobs matching the user's skills
            skills_list = [s.strip().lower() for s in user_data['skills'].split(',')]
            skill_queries = ' OR '.join(['j.description LIKE ?' for _ in skills_list])
            params = [f'%{skill}%' for skill in skills_list]
            
            # Add user_id to params
            params.append(user['user_id'])
            
            cursor.execute(f"""
                SELECT j.*, u.name as poster_name, u.company_name
                FROM jobs j
                JOIN users u ON j.job_poster_id = u.user_id
                LEFT JOIN applications a ON j.job_id = a.job_id AND a.applicant_id = ?
                WHERE j.status = 'Open' AND a.application_id IS NULL
                AND ({skill_queries})
                LIMIT 3
            """, params)
            
            suggested_jobs = cursor.fetchall()
            
            if suggested_jobs:
                for job in suggested_jobs:
                    company = job['company_name'] or job['poster_name']
                    st.write(f"**{job['title']}** at {company}")
                    st.write(f"📍 {job['location']} | 💼 {job['job_type']}")
                    if st.button("View Details", key=f"suggested_{job['job_id']}"):
                        st.session_state['job_details_id'] = job['job_id']
                        st.session_state['prev_page'] = 'dashboard'
                        st.session_state['page'] = 'job_details'
                        st.rerun()
                    st.markdown("---")
            else:
                st.info("No matching jobs found. Try updating your skills in your profile.")
        else:
            st.info("Complete your profile with skills to see personalized job suggestions.")
            if st.button("Update Profile"):
                st.session_state['page'] = 'profile'
                st.rerun()
            
    finally:
        conn.close()

def show_seeker_portfolio(user):
    """Show job seeker's portfolio including work history and certifications"""
    st.header("Professional Portfolio")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Work History
        st.subheader("Work History")
        cursor.execute("""
            SELECT * FROM work_history
            WHERE user_id = ?
            ORDER BY start_date DESC
        """, (user['user_id'],))
        
        work_history = cursor.fetchall()
        
        if work_history:
            for work in work_history:
                with st.expander(f"{work['position']} at {work['company_name']}"):
                    st.write(f"Period: {work['start_date']} - {work['end_date'] or 'Present'}")
                    st.write(f"Trade: {work['trade_category']}")
                    if work['description']:
                        st.write(work['description'])
                    if work['is_verified']:
                        st.success("✓ Verified Experience")
        else:
            st.info("No work history added yet")
            
        # Add Work History Form
        with st.expander("Add Work Experience"):
            with st.form("add_work_history"):
                company = st.text_input("Company Name")
                position = st.text_input("Position")
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date (leave as today if current)")
                trade = st.selectbox(
                    "Trade Category",
                    ["Plumbing", "Electrical", "Carpentry", "Painting", "HVAC", 
                     "Landscaping", "Construction", "Cleaning", "Roofing", 
                     "General Maintenance", "Other"]
                )
                description = st.text_area("Description")
                
                if st.form_submit_button("Add Experience"):
                    cursor.execute("""
                        INSERT INTO work_history (
                            user_id, company_name, position, start_date,
                            end_date, description, trade_category, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user['user_id'], company, position, start_date.isoformat(),
                        end_date.isoformat(), description, trade,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    st.success("Work experience added!")
                    st.rerun()
        
        # Certifications
        st.subheader("Certifications & Licenses")
        cursor.execute("""
            SELECT * FROM certifications
            WHERE user_id = ?
            ORDER BY issue_date DESC
        """, (user['user_id'],))
        
        certs = cursor.fetchall()
        
        if certs:
            for cert in certs:
                with st.expander(f"{cert['name']} from {cert['issuing_authority']}"):
                    st.write(f"Issued: {cert['issue_date']}")
                    if cert['expiry_date']:
                        st.write(f"Expires: {cert['expiry_date']}")
                    if cert['certificate_number']:
                        st.write(f"Certificate Number: {cert['certificate_number']}")
                    if cert['verification_url']:
                        st.write(f"[Verify Certificate]({cert['verification_url']})")
                    if cert['is_verified']:
                        st.success("✓ Verified Certificate")
        else:
            st.info("No certifications added yet")
        
        # Add Certification Form
        with st.expander("Add Certification"):
            with st.form("add_certification"):
                cert_name = st.text_input("Certification Name")
                authority = st.text_input("Issuing Authority")
                issue_date = st.date_input("Issue Date")
                expiry_date = st.date_input("Expiry Date (if applicable)")
                cert_number = st.text_input("Certificate Number (optional)")
                verify_url = st.text_input("Verification URL (optional)")
                
                if st.form_submit_button("Add Certification"):
                    cursor.execute("""
                        INSERT INTO certifications (
                            user_id, name, issuing_authority, issue_date,
                            expiry_date, certificate_number, verification_url,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user['user_id'], cert_name, authority, issue_date.isoformat(),
                        expiry_date.isoformat(), cert_number, verify_url,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    st.success("Certification added!")
                    st.rerun()
        
        # Background Check Status
        st.subheader("Background Check")
        from utils.background_check import BackgroundCheckManager
        
        check_status = BackgroundCheckManager.get_background_check_status(user['user_id'])
        
        if check_status['status'] == 'completed':
            st.success("✓ Background Check Verified")
            st.write(f"Valid until: {check_status['valid_until'][:10]}")
            if check_status['report_url']:
                st.write(f"[View Report]({check_status['report_url']})")
        elif check_status['status'] == 'pending':
            st.info("Background check in progress...")
        else:
            st.warning("No background check on file")
            if st.button("Request Background Check"):
                result = BackgroundCheckManager.request_background_check(
                    user['user_id'],
                    {
                        'name': user['name'],
                        'email': user['email'],
                        'location': user['location']
                    }
                )
                if result['status'] == 'pending':
                    st.success("Background check request submitted!")
                else:
                    st.error(result['message'])
        
    finally:
        conn.close()

def show_job_search(user):
    """Show job search interface with advanced filters"""
    st.header("Job Search")
    
    # Debug mode toggle (can be removed in production)
    debug_mode = st.sidebar.checkbox("Show Debug Info", value=False)
    
    # Get user's location for distance calculation
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Modified query to handle potential missing postal_code column
        try:
            cursor.execute("""
                SELECT location, latitude, longitude, postal_code 
                FROM users 
                WHERE user_id = ?
            """, (user['user_id'],))
            user_location = cursor.fetchone()
        except sqlite3.OperationalError as e:
            if "no such column: postal_code" in str(e):
                # If postal_code column doesn't exist, get other location data
                cursor.execute("""
                    SELECT location, latitude, longitude
                    FROM users 
                    WHERE user_id = ?
                """, (user['user_id'],))
                temp_location = cursor.fetchone()
                
                # Create a dict with postal_code as None
                if temp_location:
                    user_location = {
                        'location': temp_location['location'],
                        'latitude': temp_location['latitude'],
                        'longitude': temp_location['longitude'],
                        'postal_code': None
                    }
                else:
                    user_location = None
            else:
                # Re-raise if it's a different error
                raise
    finally:
        conn.close()
    
    # Advanced Search Filters
    with st.expander("Advanced Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        # Keyword and Location filters
        with col1:
            keyword = st.text_input("Keywords", help="Search for specific skills or job titles")
            
            # Location options
            location_options = ["Use My Location", "Enter Custom Location"]
            location_choice = st.radio("Location Source", location_options)
            
            if location_choice == "Use My Location":
                if user_location and user_location['location']:
                    location = st.text_input("Your Location", 
                                            value=user_location['location'],
                                            disabled=True,
                                            help="Using your saved location")
                    st.info(f"Using your saved location: {user_location['location']}")
                else:
                    st.warning("You don't have a saved location. Please set your location in your profile or enter a custom location.")
                    location = ""
            else:
                # Manual location entry
                location = st.text_input("Enter Location", 
                                       help="Enter city, state or postal code")
                
                # Option to save this location to profile
                if location and location != user_location.get('location', ''):
                    if st.button("Save This Location to My Profile"):
                        # Update location in user profile
                        conn = get_db()
                        cursor = conn.cursor()
                        try:
                            cursor.execute("""
                                UPDATE users 
                                SET location = ?, updated_at = ?
                                WHERE user_id = ?
                            """, (location, datetime.now().isoformat(), user['user_id']))
                            conn.commit()
                            
                            # Update session state
                            st.session_state['user']['location'] = location
                            
                            st.success(f"Location updated to: {location}")
                            # Need to refresh to get coordinates
                            st.info("Refresh to use this location for distance-based search")
                        except Exception as e:
                            st.error(f"Error updating location: {str(e)}")
                        finally:
                            conn.close()
            
            # Distance filter (only if user has location with coordinates)
            distance_enabled = False
            max_distance = 50  # Default value
            if user_location and user_location.get('latitude') and user_location.get('longitude'):
                distance_enabled = True
                max_distance = st.slider("Maximum Distance (km)", 0, 500, 50)
                st.info(f"Distance search is available from your location")
            elif location_choice == "Use My Location":
                st.warning("Your profile location doesn't have coordinates. Update your profile with full location details to enable distance search.")
        
        # Job Type and Trade Category filters
        with col2:
            job_type = st.selectbox(
                "Job Type",
                ["All", "One-time Job", "Regular Work", "Emergency Service", "Project Based"]
            )
            trade_category = st.selectbox(
                "Trade Category",
                ["All", "Plumbing", "Electrical", "Carpentry", "Painting", "HVAC", 
                 "Landscaping", "Construction", "Cleaning", "Roofing", "General Maintenance", "Other"]
            )
        
        # Payment filters
        with col3:
            payment_type = st.selectbox(
                "Payment Type",
                ["All", "Fixed Price", "Hourly Rate", "To Be Discussed"]
            )
            if payment_type != "To Be Discussed":
                min_pay = st.number_input("Minimum Pay ($)", min_value=0, value=0)
            
            # Add a checkbox for remote jobs
            include_remote = st.checkbox("Include Remote Jobs", value=True)
    
    # Sorting options
    sort_col1, sort_col2 = st.columns(2)
    with sort_col1:
        sort_options = ["Newest First", "Highest Paid", "Most Workers Needed"]
        # Only add distance sorting if we have user coordinates
        if user_location and user_location.get('latitude') and user_location.get('longitude'):
            sort_options.insert(1, "Nearest Location")
        
        sort_by = st.selectbox("Sort By", sort_options)
    with sort_col2:
        show_filled = st.checkbox("Show Fully Applied Positions", value=False)
    
    # Debug: Check total jobs in database
    if debug_mode:
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            total_jobs = cursor.fetchone()['count']
            st.sidebar.write(f"Total jobs in database: {total_jobs}")
            
            cursor.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
            status_counts = cursor.fetchall()
            st.sidebar.write("Jobs by status:")
            for status in status_counts:
                st.sidebar.write(f"- {status['status']}: {status['count']}")
                
            cursor.execute("SELECT job_id, title, status, job_poster_id FROM jobs ORDER BY created_at DESC LIMIT 5")
            recent_jobs = cursor.fetchall()
            st.sidebar.write("Most recent jobs:")
            for job in recent_jobs:
                st.sidebar.write(f"- #{job['job_id']}: {job['title']} ({job['status']})")
        finally:
            conn.close()
    
    # Search button
    search = st.button("Search Jobs", use_container_width=True)
    
    # Always show some results, even without explicit search
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if postal_code column exists in jobs table
        has_postal_code = True
        try:
            cursor.execute("SELECT postal_code FROM jobs LIMIT 1")
        except sqlite3.OperationalError:
            has_postal_code = False
            
        # Check if job_latitude and job_longitude exist in the jobs table
        has_job_coords = True
        try:
            cursor.execute("SELECT job_latitude, job_longitude FROM jobs LIMIT 1")
        except sqlite3.OperationalError:
            has_job_coords = False
        
        # Get jobs user has already applied to
        cursor.execute("""
            SELECT job_id FROM applications 
            WHERE applicant_id = ?
        """, (user['user_id'],))
        applied_jobs = {row['job_id'] for row in cursor.fetchall()}
        
        # Base query - use user's latitude/longitude when job coords not available
        query = """
            SELECT j.*, u.name as poster_name, u.company_name,
                   COUNT(DISTINCT a.application_id) as application_count,
                   (SELECT COUNT(*) FROM applications WHERE job_id = j.job_id) as current_applicants,
                   u.is_premium as poster_is_premium
        """
        
        # Conditionally add columns based on what exists
        if has_job_coords:
            query += ", j.job_latitude, j.job_longitude"
        else:
            # Use user latitude/longitude instead since job latitude/longitude don't exist
            query += ", u.latitude as job_latitude, u.longitude as job_longitude"
            
        query += """
            FROM jobs j
            JOIN users u ON j.job_poster_id = u.user_id
            LEFT JOIN applications a ON j.job_id = a.job_id
            WHERE j.status = 'Open'
        """
        params = []
        
        # Apply filters (only if search button was clicked)
        if search:
            if not show_filled:
                query += " AND (SELECT COUNT(*) FROM applications WHERE job_id = j.job_id) < j.workers_needed"
            
            if keyword:
                query += " AND (j.title LIKE ? OR j.description LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            if location:
                # Use the location filter input by the user, but check for postal_code column
                if has_postal_code:
                    query += " AND (j.location LIKE ? OR j.postal_code LIKE ?)"
                    params.extend([f"%{location}%", f"%{location}%"])
                else:
                    query += " AND j.location LIKE ?"
                    params.append(f"%{location}%")
            
            if job_type != "All":
                query += " AND j.job_type = ?"
                params.append(job_type)
            
            if trade_category != "All":
                query += " AND j.trade_category = ?"
                params.append(trade_category)
            
            if payment_type != "All":
                query += " AND j.payment_type = ?"
                params.append(payment_type)
                if payment_type != "To Be Discussed" and min_pay > 0:
                    query += " AND j.payment_amount >= ?"
                    params.append(min_pay)
            
            # Only include the distance filter if we have user coordinates and distance_enabled is True
            # and the job has coordinates available
            if distance_enabled and user_location and user_location['latitude'] and user_location['longitude'] and max_distance > 0 and has_job_coords:
                # Use the Haversine formula to calculate distance
                query += """
                    AND (
                        j.job_latitude IS NOT NULL 
                        AND j.job_longitude IS NOT NULL
                        AND (6371 * acos(cos(radians(?)) * cos(radians(j.job_latitude)) * 
                        cos(radians(j.job_longitude) - radians(?)) + sin(radians(?)) * 
                        sin(radians(j.job_latitude)))) <= ?
                    )
                """
                params.extend([
                    user_location['latitude'], 
                    user_location['longitude'], 
                    user_location['latitude'], 
                    max_distance
                ])
        
        # Include remote jobs if checked
        if include_remote:
            # Check if is_remote column exists
            has_is_remote = True
            try:
                cursor.execute("SELECT is_remote FROM jobs LIMIT 1")
            except sqlite3.OperationalError:
                has_is_remote = False
            
            if has_is_remote:
                query += " OR j.is_remote = 1"
        
        query += " GROUP BY j.job_id"
        
        # Apply sorting
        if sort_by == "Highest Paid":
            query += " ORDER BY CASE WHEN j.payment_amount IS NULL THEN 0 ELSE j.payment_amount END DESC"
        elif sort_by == "Most Workers Needed":
            query += " ORDER BY j.workers_needed DESC"
        elif sort_by == "Nearest Location" and user_location and user_location['latitude'] and user_location['longitude']:
            # We'll sort by distance after fetching results
            pass
        else:  # Newest First
            query += " ORDER BY j.created_at DESC"
        
        # Debug the query
        if debug_mode:
            st.sidebar.text("Query:")
            st.sidebar.text(query)
            st.sidebar.text("Params:")
            st.sidebar.text(str(params))
        
        # Execute query with proper error handling
        try:
            cursor.execute(query, params)
            jobs = cursor.fetchall()
            
            # Calculate distances and sort if needed
            if sort_by == "Nearest Location" and user_location and user_location['latitude'] and user_location['longitude']:
                from utils.location_utils import calculate_distance
                for job in jobs:
                    if job.get('job_latitude') and job.get('job_longitude'):
                        job['distance'] = calculate_distance(
                            user_location['latitude'], user_location['longitude'],
                            job['job_latitude'], job['job_longitude']
                        )
                    else:
                        job['distance'] = float('inf')
                jobs.sort(key=lambda x: x.get('distance', float('inf')))
                
                # Filter by max distance if specified
                if max_distance and max_distance > 0:
                    jobs = [j for j in jobs if j.get('distance', float('inf')) <= max_distance]
            
            # Show result count
            st.write(f"Found {len(jobs)} matching jobs")
            
            if jobs:
                for job in jobs:
                    company = job.get('company_name') or job.get('poster_name')
                    with st.expander(f"{job['title']} at {company}"):
                        # Debug job info
                        if debug_mode:
                            st.write(f"Job ID: {job['job_id']}, Status: {job['status']}")
                            st.write(f"Posted by: {job['job_poster_id']}")
                        
                        # Location and job type
                        st.write(f"📍 {job['location']} | 💼 {job['job_type']}")
                        
                        # Distance if available
                        if sort_by == "Nearest Location" and job.get('distance', float('inf')) != float('inf'):
                            st.write(f"📏 {job['distance']:.1f} km away")
                        
                        # Payment info
                        if job.get('payment_type'):
                            payment_info = f"💰 {job['payment_type']}"
                            if job.get('payment_amount'):
                                payment_info += f" - ${job['payment_amount']}"
                            st.write(payment_info)
                        
                        # Premium badge for premium job posters
                        if job.get('poster_is_premium'):
                            st.write("✨ Premium Job Poster")
                        
                        # Workers needed and current applicants
                        workers_needed = job.get('workers_needed', 1)  # Default to 1 if not specified
                        st.write(f"👥 Workers Needed: {workers_needed} | Current Applicants: {job.get('current_applicants', 0)}")
                        
                        # Job description
                        st.write(job['description'])
                        
                        # Map - Replace HTML with folium for better integration
                        if job.get('job_latitude') and job.get('job_longitude'):
                            try:
                                import folium
                                from streamlit_folium import folium_static
                                
                                # Create a folium map
                                job_loc = (job['job_latitude'], job['job_longitude'])
                                m = folium.Map(location=job_loc, zoom_start=13)
                                
                                # Add marker for job location
                                popup_html = f"""
                                <b>{job['title']}</b><br>
                                {job['location']}<br>
                                {job['job_type']}
                                """
                                
                                folium.Marker(
                                    location=job_loc,
                                    popup=popup_html,
                                    icon=folium.Icon(color="blue", icon="briefcase"),
                                ).add_to(m)
                                
                                # Add user location if available
                                if user_location and user_location['latitude'] and user_location['longitude']:
                                    user_loc = (user_location['latitude'], user_location['longitude'])
                                    folium.Marker(
                                        location=user_loc,
                                        popup="Your Location",
                                        icon=folium.Icon(color="red", icon="home"),
                                    ).add_to(m)
                                    
                                    # Add a line connecting user and job location
                                    folium.PolyLine(
                                        locations=[user_loc, job_loc],
                                        color="#4A6FDC",
                                        weight=2,
                                        opacity=0.7,
                                        dash_array="5"
                                    ).add_to(m)
                                    
                                    # Calculate distance for display
                                    from utils.location_utils import calculate_distance
                                    distance = calculate_distance(
                                        user_location['latitude'], user_location['longitude'],
                                        job['job_latitude'], job['job_longitude']
                                    )
                                    
                                    # Add distance information to the map
                                    folium.Tooltip(f"Distance: {distance:.1f} km").add_to(m)
                                
                                # Display the map
                                folium_static(m, height=250)
                            except Exception as e:
                                st.error(f"Could not display map: {str(e)}")
                        
                        # Application status/button
                        if job['job_id'] in applied_jobs:
                            st.success("✓ Applied")
                        else:
                            current_applicants = job.get('current_applicants', 0)
                            workers_needed = job.get('workers_needed', 1)  # Default to 1 if missing
                            
                            if current_applicants >= workers_needed:
                                st.warning("This position is fully applied")
                            else:
                                apply_col1, apply_col2 = st.columns([1, 1])
                                with apply_col1:
                                    # Enhanced Apply Now button with better error handling
                                    if st.button("Apply Now", key=f"apply_job_{job['job_id']}"):
                                        # Debug info
                                        if debug_mode:
                                            st.write(f"Applying for job ID: {job['job_id']}")
                                        
                                        # Store the job ID in session state
                                        st.session_state['apply_job_id'] = job['job_id']
                                        st.session_state['prev_page'] = 'dashboard'
                                        
                                        # Try multiple navigation methods for redundancy
                                        # Method 1: Query parameters
                                        st.query_params['page'] = 'apply_job'
                                        st.query_params['job_id'] = job['job_id']
                                        
                                        # Method 2: Switch page
                                        try:
                                            st.switch_page("pages/apply_job.py")
                                        except Exception as e:
                                            if debug_mode:
                                                st.error(f"Switch page error: {str(e)}")
                                            
                                            # Method 3: Session state navigation
                                            st.session_state['page'] = 'apply_job'
                                            st.rerun()
                                with apply_col2:
                                    if st.button("View Details", key=f"details_{job['job_id']}"):
                                        st.session_state['job_details_id'] = job['job_id']
                                        st.session_state['prev_page'] = 'dashboard'
                                        st.session_state['page'] = 'job_details'
                                        st.rerun()
            else:
                st.info("No jobs found matching your criteria")
                
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {str(e)}")
            st.info("Our job search is experiencing technical difficulties. We're working on fixing it.")
            
            # Show a simplified fallback query without the problematic columns
            try:
                fallback_query = """
                    SELECT j.*, u.name as poster_name, u.company_name
                    FROM jobs j
                    JOIN users u ON j.job_poster_id = u.user_id
                    WHERE j.status = 'Open'
                    ORDER BY j.created_at DESC
                    LIMIT 20
                """
                if debug_mode:
                    st.sidebar.text("Fallback Query:")
                    st.sidebar.text(fallback_query)
                
                cursor.execute(fallback_query)
                jobs = cursor.fetchall()
                
                if jobs:
                    st.subheader("Recent Jobs")
                    for job in jobs:
                        company = job.get('company_name') or job.get('poster_name')
                        with st.expander(f"{job['title']} at {company}"):
                            st.write(f"📍 {job['location']} | 💼 {job['job_type']}")
                            st.write(job['description'])
                            if st.button("Apply Now", key=f"apply_job_{job['job_id']}"):
                                # Store job ID in session state
                                st.session_state['apply_job_id'] = job['job_id']
                                st.session_state['prev_page'] = 'dashboard'
                                
                                # Try multiple navigation methods for redundancy
                                # Method 1: Query parameters
                                st.query_params['page'] = 'apply_job'
                                st.query_params['job_id'] = job['job_id']
                                
                                # Method 2: Switch page
                                try:
                                    st.switch_page("pages/apply_job.py")
                                except Exception as e:
                                    if debug_mode:
                                        st.error(f"Switch page error: {str(e)}")
                                    
                                    # Method 3: Session state navigation
                                    st.session_state['page'] = 'apply_job'
                                    st.rerun()
            except Exception as fallback_error:
                st.error(f"Could not load any jobs: {str(fallback_error)}")
                
                # Last resort: show ALL jobs regardless of status
                try:
                    last_resort_query = """
                        SELECT j.*, u.name as poster_name, u.company_name
                        FROM jobs j
                        JOIN users u ON j.job_poster_id = u.user_id
                        ORDER BY j.created_at DESC
                        LIMIT 20
                    """
                    cursor.execute(last_resort_query)
                    jobs = cursor.fetchall()
                    
                    if jobs:
                        st.subheader("All Available Jobs")
                        for job in jobs:
                            company = job.get('company_name') or job.get('poster_name')
                            with st.expander(f"{job['title']} at {company} ({job['status']})"):
                                st.write(f"📍 {job['location']} | 💼 {job['job_type']}")
                                st.write(job['description'])
                                
                                # Only show apply button for open jobs
                                if job.get('status', '').lower() == 'open':
                                    if st.button("Apply Now", key=f"apply_lr_{job['job_id']}"):
                                        # Store job ID in session state
                                        st.session_state['apply_job_id'] = job['job_id']
                                        st.session_state['prev_page'] = 'dashboard'
                                        
                                        # Try multiple navigation methods for redundancy
                                        # Method 1: Query parameters
                                        st.query_params['page'] = 'apply_job'
                                        st.query_params['job_id'] = job['job_id']
                                        
                                        # Method 2: Switch page
                                        try:
                                            st.switch_page("pages/apply_job.py")
                                        except Exception as e:
                                            if debug_mode:
                                                st.error(f"Switch page error: {str(e)}")
                                            
                                            # Method 3: Session state navigation
                                            st.session_state['page'] = 'apply_job'
                                            st.rerun()
                except Exception as last_resort_error:
                    st.error(f"Failed to load jobs: {str(last_resort_error)}")
    finally:
        conn.close()

def show_my_applications(user):
    """Show job seeker's applications"""
    st.header("My Applications")
    
    # Debug mode toggle
    debug_mode = st.sidebar.checkbox("Show Debug Info for Applications", value=False)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if debug_mode:
            st.write(f"Fetching applications for user ID: {user['user_id']}")
        
        cursor.execute("""
            SELECT a.*, j.title, u.name as poster_name, u.company_name,
                   (SELECT COUNT(*) FROM messages m 
                    WHERE m.receiver_id = ? AND m.sender_id = j.job_poster_id 
                    AND m.is_read = 0) as unread_messages
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN users u ON j.job_poster_id = u.user_id
            WHERE a.applicant_id = ?
            ORDER BY a.created_at DESC
        """, (user['user_id'], user['user_id']))
        
        applications = cursor.fetchall()
        
        if debug_mode:
            st.write(f"Found {len(applications) if applications else 0} applications")
            
            # Show schema information
            st.write("### Database Schema Diagnostics")
            cursor.execute("PRAGMA table_info(applications)")
            st.write("Applications table columns:")
            app_columns = cursor.fetchall()
            for col in app_columns:
                st.write(f"- {col['name']} ({col['type']})")
        
        if applications:
            for app in applications:
                company = app['company_name'] or app['poster_name']
                with st.expander(f"{app['title']} at {company}"):
                    status_color = {
                        'Pending': 'blue',
                        'Accepted': 'green',
                        'Rejected': 'red'
                    }.get(app['status'], 'gray')
                    
                    # Show application ID in debug mode
                    if debug_mode:
                        st.write(f"Application ID: {app['application_id']}")
                    
                    st.markdown(f"Status: :{status_color}[{app['status']}]")
                    st.write(f"Applied: {app['created_at'][:10]}")
                    if app['updated_at']:
                        st.write(f"Last Updated: {app['updated_at'][:10]}")
                    
                    # Show application details if available
                    if app.get('cover_letter'):
                        st.write("Cover Letter:")
                        st.write(app['cover_letter'])
                    
                    # Show additional application fields if they exist and debug mode is on
                    if debug_mode:
                        for key, value in app.items():
                            if key not in ['application_id', 'job_id', 'applicant_id', 'job_poster_id', 
                                         'status', 'created_at', 'updated_at', 'title', 
                                         'poster_name', 'company_name', 'unread_messages', 'cover_letter']:
                                if value:
                                    st.write(f"{key.replace('_', ' ').title()}: {value}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Message Employer", key=f"msg_{app['application_id']}"):
                            st.session_state['message_user_id'] = app['job_poster_id']
                            st.session_state['page'] = 'messages'
                            st.rerun()
                    
                    if app['unread_messages'] > 0:
                        st.info(f"You have {app['unread_messages']} unread message{'s' if app['unread_messages'] > 1 else ''} from the employer!")
        else:
            st.info("You haven't submitted any applications yet")
            
            if st.button("Browse Jobs"):
                st.session_state['page'] = 'browse_jobs'
                st.rerun()
            
    finally:
        conn.close()

def show_admin_overview():
    """Show admin dashboard overview"""
    st.header("System Overview")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get counts
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'Job Seeker'")
        job_seekers = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'Job Poster'")
        job_posters = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE status = 'Open'")
        active_jobs = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM applications")
        total_applications = cursor.fetchone()['count']
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Job Seekers", job_seekers)
        with col2:
            st.metric("Job Posters", job_posters)
        with col3:
            st.metric("Active Jobs", active_jobs)
        with col4:
            st.metric("Total Applications", total_applications)
        
        # Recent Activity
        st.subheader("Recent Activity")
        cursor.execute("""
            SELECT 'New User' as type, u.name, u.created_at, u.role as details
            FROM users u
            WHERE u.created_at >= datetime('now', '-7 days')
            UNION ALL
            SELECT 'New Job' as type, j.title as name, j.created_at, u.company_name as details
            FROM jobs j
            JOIN users u ON j.job_poster_id = u.user_id
            WHERE j.created_at >= datetime('now', '-7 days')
            ORDER BY created_at DESC
            LIMIT 10
        """)
        activities = cursor.fetchall()
        
        if activities:
            for activity in activities:
                st.write(f"**{activity['type']}:** {activity['name']} ({activity['details']}) - {activity['created_at'][:10]}")
        else:
            st.info("No recent activity")
            
    finally:
        conn.close()

    # Add logout button
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

def show_user_management():
    """Show user management interface"""
    st.header("User Management")
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.*, 
                   COUNT(DISTINCT j.job_id) as total_jobs,
                   COUNT(DISTINCT a.application_id) as total_applications
            FROM users u
            LEFT JOIN jobs j ON u.user_id = j.job_poster_id
            LEFT JOIN applications a ON (
                u.user_id = a.applicant_id OR 
                u.user_id = j.job_poster_id
            )
            GROUP BY u.user_id
            ORDER BY u.created_at DESC
        """)
        users = cursor.fetchall()
        
        if users:
            for user in users:
                with st.expander(f"{user['name']} ({user['email']})"):
                    st.write(f"Role: {user['role']}")
                    st.write(f"Created: {user['created_at'][:10]}")
                    st.write(f"Last Updated: {user['updated_at'][:10]}")
                    
                    if user['role'] == 'Job Poster':
                        st.write(f"Company: {user['company_name'] or 'Not specified'}")
                        st.write(f"Total Jobs Posted: {user['total_jobs']}")
                    
                    st.write(f"Total Applications: {user['total_applications']}")
                    
                    if user['email'] != AuthManager.ADMIN_EMAIL:  # Don't allow blocking admin
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Block User", key=f"block_{user['user_id']}"):
                                # Delete all user's jobs and applications
                                if user['role'] == 'Job Poster':
                                    cursor.execute("""
                                        DELETE FROM applications 
                                        WHERE job_id IN (
                                            SELECT job_id FROM jobs 
                                            WHERE job_poster_id = ?
                                        )
                                    """, (user['user_id'],))
                                    cursor.execute("""
                                        DELETE FROM jobs 
                                        WHERE job_poster_id = ?
                                    """, (user['user_id'],))
                                
                                # Delete user's applications
                                cursor.execute("""
                                    DELETE FROM applications 
                                    WHERE applicant_id = ?
                                """, (user['user_id'],))
                                
                                # Delete user's messages
                                cursor.execute("""
                                    DELETE FROM messages 
                                    WHERE sender_id = ? OR receiver_id = ?
                                """, (user['user_id'], user['user_id']))
                                
                                # Delete user's reviews
                                cursor.execute("""
                                    DELETE FROM reviews 
                                    WHERE reviewer_id = ? OR reviewed_id = ?
                                """, (user['user_id'], user['user_id']))
                                
                                # Finally, delete the user
                                cursor.execute("""
                                    DELETE FROM users 
                                    WHERE user_id = ?
                                """, (user['user_id'],))
                                
                                conn.commit()
                                st.success(f"User {user['name']} has been blocked and removed")
                                st.rerun()
                        
                        with col2:
                            if st.button("Export Data", key=f"export_{user['user_id']}"):
                                data = export_user_data(user['user_id'])
                                st.json(data)  # Display the data in JSON format
                                st.download_button(
                                    "📥 Download Data",
                                    data=str(data),
                                    file_name=f"user_data_{user['user_id']}.json",
                                    mime="application/json"
                                )
        else:
            st.info("No users found")
    finally:
        conn.close()

def show_job_management():
    """Show job management interface"""
    st.header("Job Management")
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT j.*, u.company_name, u.name as poster_name
            FROM jobs j
            JOIN users u ON j.job_poster_id = u.user_id
            ORDER BY j.created_at DESC
        """)
        jobs = cursor.fetchall()
        
        if jobs:
            for job in jobs:
                company = job['company_name'] or job['poster_name']
                with st.expander(f"{job['title']} at {company}"):
                    st.write(f"Posted by: {job['poster_name']}")
                    st.write(f"Location: {job['location']}")
                    st.write(f"Type: {job['job_type']}")
                    if job.get('payment_type'):
                        payment_info = f"Payment: {job['payment_type']}"
                        if job.get('payment_amount'):
                            payment_info += f" - ${job['payment_amount']}"
                        st.write(payment_info)
                    st.write(f"Status: {job['status']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Toggle Status", key=f"toggle_job_{job['job_id']}"):
                            new_status = 'Closed' if job['status'] == 'Open' else 'Open'
                            cursor.execute(
                                "UPDATE jobs SET status = ? WHERE job_id = ?",
                                (new_status, job['job_id'])
                            )
                            conn.commit()
                            st.rerun()
                    with col2:
                        if st.button("Delete Job", key=f"delete_job_{job['job_id']}"):
                            # Delete associated applications first
                            cursor.execute(
                                "DELETE FROM applications WHERE job_id = ?",
                                (job['job_id'],)
                            )
                            # Then delete the job
                            cursor.execute(
                                "DELETE FROM jobs WHERE job_id = ?",
                                (job['job_id'],)
                            )
                            conn.commit()
                            st.success("Job deleted successfully")
                            st.rerun()
        else:
            st.info("No jobs found")
    finally:
        conn.close()

def show_system_settings():
    """Show system settings interface"""
    st.header("System Settings")
    
    # Platform Settings
    st.subheader("Platform Settings")
    with st.form("platform_settings"):
        maintenance_mode = st.checkbox("Maintenance Mode")
        registration_open = st.checkbox("Allow New Registrations", value=True)
        max_jobs_per_poster = st.number_input("Max Jobs per Poster", min_value=1, value=10)
        max_applications_per_seeker = st.number_input("Max Applications per Seeker", min_value=1, value=50)
        
        if st.form_submit_button("Save Settings"):
            st.success("Settings saved successfully")
    
    # Backup & Maintenance
    st.subheader("Backup & Maintenance")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Backup Database"):
            st.info("Database backup initiated...")
    with col2:
        if st.button("Clear Cache"):
            st.info("Cache cleared successfully")

def show_poster_overview(user):
    """Show job poster dashboard overview"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get job posting stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_jobs,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_jobs,
                SUM(CASE WHEN status = 'Filled' THEN 1 ELSE 0 END) as filled_jobs
            FROM jobs
            WHERE job_poster_id = ?
        """, (user['user_id'],))
        
        job_stats = cursor.fetchone()
        
        # Get application stats
        cursor.execute("""
            SELECT COUNT(*) as total_applications
            FROM applications
            WHERE job_id IN (SELECT job_id FROM jobs WHERE job_poster_id = ?)
        """, (user['user_id'],))
        
        app_stats = cursor.fetchone()
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Jobs", job_stats['total_jobs'] or 0)
        with col2:
            st.metric("Open Jobs", job_stats['open_jobs'] or 0)
        with col3:
            st.metric("Total Applications", app_stats['total_applications'] or 0)
        
        # Recent Activity
        st.subheader("Recent Activity")
        cursor.execute("""
            SELECT a.*, j.title, u.name as applicant_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN users u ON a.applicant_id = u.user_id
            WHERE j.job_poster_id = ?
            ORDER BY a.created_at DESC
            LIMIT 5
        """, (user['user_id'],))
        
        recent = cursor.fetchall()
        if recent:
            for app in recent:
                st.write(f"**{app['applicant_name']}** applied to **{app['title']}** - {app['created_at'][:10]}")
                st.write(f"Status: {app['status']}")
                st.markdown("---")
        else:
            st.info("No recent activity")
        
        # Add OpenStreetMap for location-based job insights
        st.markdown("---")
        st.subheader("📍 Location-Based Insights")
        
        # Check if user has location data
        cursor.execute("""
            SELECT location, latitude, longitude 
            FROM users 
            WHERE user_id = ?
        """, (user['user_id'],))
        user_location = cursor.fetchone()
        
        if user_location and user_location['latitude'] and user_location['longitude']:
            # Create a map centered on user's location
            import folium
            from streamlit_folium import folium_static
            
            st.write("Your business location:")
            user_loc = (user_location['latitude'], user_location['longitude'])
            m = folium.Map(location=user_loc, zoom_start=13)
            
            # Add user's location marker
            folium.Marker(
                location=user_loc,
                popup=user_location['location'],
                icon=folium.Icon(color="red", icon="home"),
            ).add_to(m)
            
            # Add active jobs to the map
            cursor.execute("""
                SELECT j.job_id, j.title, j.location, j.trade_category, 
                       j.payment_type, j.payment_amount,
                       COUNT(a.application_id) as application_count
                FROM jobs j
                LEFT JOIN applications a ON j.job_id = a.job_id
                WHERE j.job_poster_id = ? AND j.status = 'Open'
                GROUP BY j.job_id
            """, (user['user_id'],))
            
            active_jobs = cursor.fetchall()
            
            if active_jobs:
                # Most jobs will be at the same location as the business
                for job in active_jobs:
                    popup_html = f"""
                    <b>{job['title']}</b><br>
                    {job['trade_category']}<br>
                    {job['application_count']} applications
                    """
                    
                    # Add job to map (using same location as business for now)
                    folium.Marker(
                        location=user_loc,
                        popup=popup_html,
                        icon=folium.Icon(color="blue", icon="info-sign"),
                    ).add_to(m)
            
            # Display the map
            folium_static(m, width=700, height=400)
            
            # Display analytics
            st.write("### Local Job Market")
            
            # Show some analytics about the area (you can expand this with real data)
            st.write(f"📊 Most common trades in {user_location['location']}:")
            
            # Placeholder data (replace with real queries later)
            trade_data = {
                "Carpentry": 45, 
                "Plumbing": 32, 
                "Electrical": 28, 
                "Painting": 25, 
                "HVAC": 18
            }
            
            # Simple bar chart
            st.bar_chart(trade_data)
            
            # Add a note about location-based insights
            st.info("Location-based insights help you understand the job market in your area and optimize your job postings.")
        else:
            st.warning("Your business location is not set. Please update your profile with location information to see location-based insights.")
            
            if st.button("Update Location"):
                st.session_state['page'] = 'profile'
                st.rerun()
            
    finally:
        conn.close()

def show_poster_jobs(user):
    """Show job poster's job listings"""
    st.header("My Jobs")
    
    # Add New Job button
    if st.button("➕ Post New Job"):
        st.session_state['page'] = 'post_jobs'
        st.rerun()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT j.*, COUNT(a.application_id) as application_count
            FROM jobs j
            LEFT JOIN applications a ON j.job_id = a.job_id
            WHERE j.job_poster_id = ?
            GROUP BY j.job_id
            ORDER BY j.created_at DESC
        """, (user['user_id'],))
        jobs = cursor.fetchall()
        
        if jobs:
            for job in jobs:
                with st.expander(f"{job['title']} ({job['application_count']} applications)"):
                    st.write(f"Location: {job['location']}")
                    st.write(f"Type: {job['job_type']}")
                    if job.get('payment_type'):
                        payment_info = f"Payment: {job['payment_type']}"
                        if job.get('payment_amount'):
                            payment_info += f" - ${job['payment_amount']}"
                        st.write(payment_info)
                    st.write(f"Status: {job['status']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Edit", key=f"edit_{job['job_id']}"):
                            st.session_state['edit_job_id'] = job['job_id']
                            st.session_state['page'] = 'edit_job'
                            st.rerun()
                    with col2:
                        if st.button("Toggle Status", key=f"toggle_{job['job_id']}"):
                            new_status = 'Closed' if job['status'] == 'Open' else 'Open'
                            cursor.execute(
                                "UPDATE jobs SET status = ? WHERE job_id = ?",
                                (new_status, job['job_id'])
                            )
                            conn.commit()
                            st.rerun()
                    with col3:
                        if st.button("Delete", key=f"delete_{job['job_id']}"):
                            # Delete associated applications first
                            cursor.execute(
                                "DELETE FROM applications WHERE job_id = ?",
                                (job['job_id'],)
                            )
                            # Then delete the job
                            cursor.execute(
                                "DELETE FROM jobs WHERE job_id = ?",
                                (job['job_id'],)
                            )
                            conn.commit()
                            st.success("Job deleted successfully")
                            st.rerun()
        else:
            st.info("You haven't posted any jobs yet")
    finally:
        conn.close()

def show_applications_received(user):
    """Show applications received by job poster"""
    st.header("Applications Received")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get unread application count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            WHERE j.job_poster_id = ? 
            AND a.is_read = 0
        """, (user['user_id'],))
        unread_count = cursor.fetchone()['count']
        
        if unread_count > 0:
            st.info(f"You have {unread_count} new application{'s' if unread_count > 1 else ''}!")
        
        cursor.execute("""
            SELECT a.*, j.title as job_title, u.name as applicant_name,
                   j.workers_needed,
                   (SELECT COUNT(*) FROM applications WHERE job_id = j.job_id AND status = 'Accepted') as accepted_count,
                   u.location as applicant_location,
                   u.latitude as applicant_latitude,
                   u.longitude as applicant_longitude,
                   (
                       SELECT COUNT(*) 
                       FROM work_history wh 
                       WHERE wh.user_id = a.applicant_id 
                       AND wh.trade_category = j.trade_category
                   ) as relevant_experience,
                   (
                       SELECT GROUP_CONCAT(c.name) 
                       FROM certifications c 
                       WHERE c.user_id = a.applicant_id
                   ) as certifications,
                   u.background_check_status
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN users u ON a.applicant_id = u.user_id
            WHERE j.job_poster_id = ?
            ORDER BY a.created_at DESC
        """, (user['user_id'],))
        
        applications = cursor.fetchall()
        
        if applications:
            for app in applications:
                with st.expander(f"{app['applicant_name']} → {app['job_title']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Status: {app['status']}")
                        st.write(f"Applied: {app['created_at'][:10]}")
                        if app['updated_at']:
                            st.write(f"Last Updated: {app['updated_at'][:10]}")
                    
                    with col2:
                        st.write(f"📍 Location: {app['applicant_location']}")
                        if app['relevant_experience'] > 0:
                            st.write(f"✅ Has relevant experience")
                        if app['certifications']:
                            st.write(f"📜 Certifications: {app['certifications']}")
                        if app['background_check_status'] == 'completed':
                            st.write("✓ Background Check Verified")
                    
                    if app.get('cover_letter'):
                        st.write("Cover Letter:")
                        st.write(app['cover_letter'])
                    if app.get('tools_equipment'):
                        st.write("Tools & Equipment:")
                        st.write(app['tools_equipment'])
                    if app.get('licenses_certs'):
                        st.write("Licenses & Certifications:")
                        st.write(app['licenses_certs'])
                    
                    # Mark as read
                    if not app['is_read']:
                        cursor.execute("""
                            UPDATE applications 
                            SET is_read = 1 
                            WHERE application_id = ?
                        """, (app['application_id'],))
                        conn.commit()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if app['status'] == 'Pending' and app['accepted_count'] < app['workers_needed']:
                            if st.button("Accept", key=f"accept_{app['application_id']}"):
                                cursor.execute("""
                                    UPDATE applications 
                                    SET status = 'Accepted', updated_at = ? 
                                    WHERE application_id = ?
                                """, (datetime.now().isoformat(), app['application_id']))
                                
                                # Calculate response time
                                cursor.execute("""
                                    UPDATE applications
                                    SET response_time = 
                                        ROUND(
                                            (JULIANDAY(?) - JULIANDAY(created_at)) * 24 * 60
                                        )
                                    WHERE application_id = ?
                                """, (datetime.now().isoformat(), app['application_id']))
                                
                                conn.commit()
                                
                                # Send notification
                                cursor.execute("""
                                    INSERT INTO notifications (user_id, message, created_at)
                                    VALUES (?, ?, ?)
                                """, (app['applicant_id'], 
                                     f"Your application for {app['job_title']} has been accepted!",
                                     datetime.now().isoformat()))
                                conn.commit()
                                st.rerun()
                    with col2:
                        if app['status'] == 'Pending':
                            if st.button("Reject", key=f"reject_{app['application_id']}"):
                                cursor.execute("""
                                    UPDATE applications 
                                    SET status = 'Rejected', updated_at = ? 
                                    WHERE application_id = ?
                                """, (datetime.now().isoformat(), app['application_id']))
                                
                                # Calculate response time
                                cursor.execute("""
                                    UPDATE applications
                                    SET response_time = 
                                        ROUND(
                                            (JULIANDAY(?) - JULIANDAY(created_at)) * 24 * 60
                                        )
                                    WHERE application_id = ?
                                """, (datetime.now().isoformat(), app['application_id']))
                                
                                conn.commit()
                                
                                # Send notification
                                cursor.execute("""
                                    INSERT INTO notifications (user_id, message, created_at)
                                    VALUES (?, ?, ?)
                                """, (app['applicant_id'], 
                                     f"Your application for {app['job_title']} was not selected.",
                                     datetime.now().isoformat()))
                                conn.commit()
                                st.rerun()
                    with col3:
                        if st.button("Message", key=f"msg_{app['application_id']}"):
                            st.session_state['message_user_id'] = app['applicant_id']
                            st.session_state['page'] = 'messages'
                            st.rerun()
        else:
            st.info("No applications received yet")
            
    finally:
        conn.close()

def show_poster_analytics(user):
    """Show job poster analytics"""
    st.header("Analytics")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Job Performance
        st.subheader("Job Performance")
        cursor.execute("""
            SELECT j.title,
                   COUNT(a.application_id) as applications,
                   AVG(CASE WHEN a.status = 'Accepted' THEN 1 ELSE 0 END) as acceptance_rate
            FROM jobs j
            LEFT JOIN applications a ON j.job_id = a.job_id
            WHERE j.poster_id = ?
            GROUP BY j.job_id
            ORDER BY applications DESC
        """, (user['user_id'],))
        performance = cursor.fetchall()
        
        if performance:
            for job in performance:
                st.metric(
                    job['title'],
                    f"{job['applications']} applications",
                    f"{job['acceptance_rate']*100:.1f}% acceptance rate"
                )
        else:
            st.info("No job performance data available")
        
        # Application Trends
        st.subheader("Application Trends")
        cursor.execute("""
            SELECT DATE(a.created_at) as date,
                   COUNT(*) as count
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            WHERE j.poster_id = ?
            GROUP BY DATE(a.created_at)
            ORDER BY date DESC
            LIMIT 7
        """, (user['user_id'],))
        trends = cursor.fetchall()
        
        if trends:
            dates = [t['date'] for t in trends]
            counts = [t['count'] for t in trends]
            st.line_chart({"Applications": counts}, use_container_width=True)
        else:
            st.info("No trend data available")
            
    finally:
        conn.close()

def show_admin_applications():
    """Show all applications for admin"""
    st.header("All Applications")
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.*, 
                   j.title as job_title,
                   js.name as applicant_name,
                   jp.name as poster_name,
                   jp.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN users js ON a.applicant_id = js.user_id
            JOIN users jp ON j.job_poster_id = jp.user_id
            ORDER BY a.created_at DESC
        """)
        applications = cursor.fetchall()
        
        if applications:
            for app in applications:
                company = app['company_name'] or app['poster_name']
                with st.expander(f"{app['applicant_name']} → {app['job_title']} at {company}"):
                    st.write(f"Status: {app['status']}")
                    st.write(f"Applied: {app['created_at'][:10]}")
                    if app['updated_at']:
                        st.write(f"Last Updated: {app['updated_at'][:10]}")
                    if app.get('cover_letter'):
                        st.write("Cover Letter:")
                        st.write(app['cover_letter'])
                    if app.get('tools_equipment'):
                        st.write("Tools & Equipment:")
                        st.write(app['tools_equipment'])
                    if app.get('licenses_certs'):
                        st.write("Licenses & Certifications:")
                        st.write(app['licenses_certs'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Update Status", key=f"status_{app['application_id']}"):
                            new_status = 'Accepted' if app['status'] == 'Pending' else 'Pending'
                            cursor.execute("""
                                UPDATE applications 
                                SET status = ?, updated_at = ? 
                                WHERE application_id = ?
                            """, (new_status, datetime.now().isoformat(), app['application_id']))
                            conn.commit()
                            st.rerun()
                    with col2:
                        if st.button("Delete", key=f"delete_{app['application_id']}"):
                            cursor.execute("""
                                DELETE FROM applications 
                                WHERE application_id = ?
                            """, (app['application_id'],))
                            conn.commit()
                            st.success("Application deleted successfully")
                            st.rerun()
        else:
            st.info("No applications found")
            
    finally:
        conn.close()

def export_user_data(user_id):
    """Export all data related to a user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get user details
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = dict(cursor.fetchone())
        
        # Get user's jobs if they're a job poster
        cursor.execute("""
            SELECT j.*, COUNT(a.application_id) as application_count
            FROM jobs j
            LEFT JOIN applications a ON j.job_id = a.job_id
            WHERE j.job_poster_id = ?
            GROUP BY j.job_id
        """, (user_id,))
        jobs = [dict(row) for row in cursor.fetchall()]
        
        # Get user's applications if they're a job seeker
        cursor.execute("""
            SELECT a.*, j.title as job_title, u.company_name, u.name as poster_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN users u ON j.job_poster_id = u.user_id
            WHERE a.applicant_id = ?
        """, (user_id,))
        applications = [dict(row) for row in cursor.fetchall()]
        
        # Get user's reviews
        cursor.execute("""
            SELECT r.*, u.name as reviewer_name
            FROM reviews r
            JOIN users u ON r.reviewer_id = u.user_id
            WHERE r.reviewed_id = ?
        """, (user_id,))
        reviews = [dict(row) for row in cursor.fetchall()]
        
        # Compile all data
        export_data = {
            'user': user_data,
            'jobs': jobs if jobs else [],
            'applications': applications if applications else [],
            'reviews': reviews if reviews else []
        }
        
        return export_data
        
    finally:
        conn.close() 