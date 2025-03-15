import streamlit as st
from utils.database import get_db
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
from utils.location_utils import calculate_distance

def check_application_limits(user_id):
    """Check if user has reached their application limits"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check subscription status
        cursor.execute("""
            SELECT plan_id, status 
            FROM subscriptions 
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        subscription = cursor.fetchone()
        
        # Get number of applications in the last 30 days
        cursor.execute("""
            SELECT COUNT(*) as app_count 
            FROM applications 
            WHERE applicant_id = ? 
            AND created_at >= ?
        """, (user_id, (datetime.now() - timedelta(days=30)).isoformat()))
        
        app_count = cursor.fetchone()['app_count']
        
        # Free users can apply to 1 job per month
        if not subscription and app_count >= 1:
            return False, "You have reached the maximum number of free job applications (1 per month). Please upgrade to Pro to apply for more jobs."
        
        return True, None
        
    finally:
        conn.close()

def show_browse_jobs():
    st.title("Browse Local Jobs")
    
    # Check if user is logged in
    if 'user' not in st.session_state:
        st.error("Please log in to browse jobs")
        return
    
    # Get user location for distance calculation
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT latitude, longitude, postal_code 
        FROM users 
        WHERE user_id = ?
    """, (st.session_state['user']['user_id'],))
    user_location = cursor.fetchone()
    
    # View mode selector (List or Map)
    view_mode = st.radio("View Mode", ["List View", "Map View"], horizontal=True)
    
    # Search and filter section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search jobs", placeholder="e.g. Electrician, Plumber...")
    
    with col2:
        location = st.text_input("Location", placeholder="Enter your area...")
    
    with col3:
        job_type = st.selectbox(
            "Job Type",
            ["All Types", "Full-time", "Part-time", "Contract", "One-time", "Hourly"]
        )
    
    # Additional filters
    col1, col2 = st.columns(2)
    with col1:
        distance = st.slider("Distance (km)", 0, 50, 10)
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Most Recent", "Distance", "Pay Rate (High to Low)", "Pay Rate (Low to High)"]
        )
    
    # Build query
    query = """
        SELECT j.*, u.company_name, u.rating, u.latitude as poster_lat, u.longitude as poster_lng,
               COUNT(DISTINCT r.review_id) as review_count
        FROM jobs j
        JOIN users u ON j.poster_id = u.user_id
        LEFT JOIN reviews r ON u.user_id = r.reviewed_user_id
        WHERE j.is_active = 1
    """
    params = []
    
    if search_term:
        query += " AND (j.title LIKE ? OR j.description LIKE ? OR j.skills_required LIKE ?)"
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern] * 3)
    
    if location:
        query += " AND j.location LIKE ?"
        params.append(f"%{location}%")
    
    if job_type != "All Types":
        query += " AND j.job_type = ?"
        params.append(job_type)
    
    # Distance filtering for location-enabled jobs when user has location
    if user_location and user_location['latitude'] and user_location['longitude'] and distance > 0:
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
            distance
        ])
    
    query += " GROUP BY j.job_id"
    
    if sort_by == "Most Recent":
        query += " ORDER BY j.created_at DESC"
    elif sort_by == "Pay Rate (High to Low)":
        query += " ORDER BY j.pay_rate DESC"
    elif sort_by == "Pay Rate (Low to High)":
        query += " ORDER BY j.pay_rate ASC"
    elif sort_by == "Distance" and user_location and user_location['latitude'] and user_location['longitude']:
        # We'll sort in Python after fetching results since SQLite doesn't handle this well
        pass
    
    # Execute query
    cursor.execute(query, params)
    jobs = cursor.fetchall()
    
    # Sort by distance if needed
    if sort_by == "Distance" and user_location and user_location['latitude'] and user_location['longitude']:
        def calculate_job_distance(job):
            if job.get('job_latitude') and job.get('job_longitude'):
                return calculate_distance(
                    user_location['latitude'], user_location['longitude'],
                    job['job_latitude'], job['job_longitude']
                )
            return float('inf')  # Jobs without coordinates go to the end
        
        jobs = sorted(jobs, key=calculate_job_distance)
    
    if not jobs:
        st.info("No jobs found matching your criteria.")
        conn.close()
        return
    
    # Display jobs based on view mode
    if view_mode == "Map View":
        # Create map centered on user's location or default to first job
        if user_location and user_location['latitude'] and user_location['longitude']:
            map_center = [user_location['latitude'], user_location['longitude']]
        elif jobs and jobs[0].get('job_latitude') and jobs[0].get('job_longitude'):
            map_center = [jobs[0]['job_latitude'], jobs[0]['job_longitude']]
        else:
            map_center = [40.7128, -74.0060]  # Default to NYC
        
        m = folium.Map(location=map_center, zoom_start=11)
        
        # Add user marker if location is available
        if user_location and user_location['latitude'] and user_location['longitude']:
            folium.Marker(
                location=[user_location['latitude'], user_location['longitude']],
                popup="Your Location",
                icon=folium.Icon(color="red", icon="home"),
            ).add_to(m)
            
            # Add circle for distance filter
            if distance > 0:
                folium.Circle(
                    location=[user_location['latitude'], user_location['longitude']],
                    radius=distance * 1000,  # Convert km to meters
                    color='#3186cc',
                    fill=True,
                    fill_color='#3186cc',
                    fill_opacity=0.2
                ).add_to(m)
        
        # Add job markers
        for job in jobs:
            if job.get('job_latitude') and job.get('job_longitude'):
                # Calculate distance if user location is available
                distance_info = ""
                if user_location and user_location['latitude'] and user_location['longitude']:
                    job_distance = calculate_distance(
                        user_location['latitude'], user_location['longitude'],
                        job['job_latitude'], job['job_longitude']
                    )
                    distance_info = f"<br>📍 {job_distance:.1f} km from you"
                
                # Create popup content
                popup_html = f"""
                <div style="width:200px">
                    <b>{job['title']}</b><br>
                    🏢 {job['company_name']}<br>
                    📍 {job['location']}<br>
                    💼 {job['job_type']}<br>
                    {"💰 $" + str(job['pay_rate']) + "/hr" if job['pay_rate'] else ""}
                    {distance_info}
                    <br><br>
                    <a href="javascript:void(0);" onclick="parent.postMessage({{'job_id': {job['job_id']}}}, '*')">Apply Now</a>
                </div>
                """
                
                # Add marker to map
                folium.Marker(
                    location=[job['job_latitude'], job['job_longitude']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=job['title'],
                    icon=folium.Icon(color="blue", icon="briefcase"),
                ).add_to(m)
        
        # Display map
        st.write("### Map View of Available Jobs")
        folium_static(m, width=800, height=500)
        
        # Handle map clicks (this requires JavaScript communication)
        st.markdown("""
        <script>
        window.addEventListener('message', function(e) {
            if (e.data.job_id) {
                // Communicate with Streamlit using query parameters
                window.location.href = window.location.href.split('?')[0] + '?job_id=' + e.data.job_id;
            }
        });
        </script>
        """, unsafe_allow_html=True)
        
        # Display a simplified list below the map
        st.write("### Available Jobs")
        for job in jobs:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(job['title'])
                    st.write(f"🏢 {job['company_name']} | 📍 {job['location']} | 💼 {job['job_type']}")
                    if job['pay_rate']:
                        st.write(f"💰 ${job['pay_rate']}/hr")
                
                with col2:
                    can_apply, limit_message = check_application_limits(st.session_state['user']['user_id'])
                    if not can_apply:
                        st.error(limit_message)
                        if st.button("Upgrade to Pro", key=f"upgrade_{job['job_id']}"):
                            st.session_state['page'] = 'pricing'
                            st.rerun()
                    else:
                        if st.button("Apply Now", key=f"apply_{job['job_id']}"):
                            st.session_state['apply_job_id'] = job['job_id']
                            st.session_state['page'] = 'apply_job'
                            st.session_state['prev_page'] = 'browse_jobs'
                            # Add debug output
                            st.info(f"Redirecting to apply for job {job['job_id']}...")
                            st.rerun()
                
                st.markdown("---")
    else:
        # List View - original code
        for job in jobs:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(job['title'])
                    st.write(f"🏢 {job['company_name']}")
                    st.write(f"📍 {job['location']}")
                    st.write(f"💼 {job['job_type']}")
                    if job['pay_rate']:
                        st.write(f"💰 ${job['pay_rate']}/hr")
                    
                    # Add distance information if user location is available
                    if user_location and user_location['latitude'] and user_location['longitude'] and job.get('job_latitude') and job.get('job_longitude'):
                        distance = calculate_distance(
                            user_location['latitude'], user_location['longitude'],
                            job['job_latitude'], job['job_longitude']
                        )
                        st.write(f"📍 {distance:.1f} km from your location")
                    
                    with st.expander("View Details"):
                        st.write(job['description'])
                        st.write("**Skills Required:**")
                        st.write(job['skills_required'])
                        st.write("**Experience Level:**")
                        st.write(job['experience_level'])
                        
                        # Show provider rating
                        if job['rating']:
                            st.write(f"⭐ Rating: {job['rating']:.1f} ({job['review_count']} reviews)")
                        
                        # Show job location map if coordinates are available
                        if job.get('job_latitude') and job.get('job_longitude'):
                            st.write("### Job Location")
                            job_map = folium.Map(location=[job['job_latitude'], job['job_longitude']], zoom_start=13)
                            
                            # Add job marker
                            folium.Marker(
                                location=[job['job_latitude'], job['job_longitude']],
                                popup=job['title'],
                                icon=folium.Icon(color="blue", icon="briefcase"),
                            ).add_to(job_map)
                            
                            # Add user location if available
                            if user_location and user_location['latitude'] and user_location['longitude']:
                                folium.Marker(
                                    location=[user_location['latitude'], user_location['longitude']],
                                    popup="Your Location",
                                    icon=folium.Icon(color="red", icon="home"),
                                ).add_to(job_map)
                                
                                # Add a line connecting user and job location
                                folium.PolyLine(
                                    locations=[
                                        [user_location['latitude'], user_location['longitude']],
                                        [job['job_latitude'], job['job_longitude']]
                                    ],
                                    color="#4A6FDC",
                                    weight=2,
                                    opacity=0.7,
                                    dash_array="5"
                                ).add_to(job_map)
                            
                            folium_static(job_map, height=200)
                
                with col2:
                    can_apply, limit_message = check_application_limits(st.session_state['user']['user_id'])
                    if not can_apply:
                        st.error(limit_message)
                        if st.button("Upgrade to Pro", key=f"upgrade_{job['job_id']}"):
                            st.session_state['page'] = 'pricing'
                            st.rerun()
                    else:
                        if st.button("Apply Now", key=f"apply_{job['job_id']}"):
                            st.session_state['apply_job_id'] = job['job_id']
                            st.session_state['page'] = 'apply_job'
                            st.session_state['prev_page'] = 'browse_jobs'
                            # Add debug output
                            st.info(f"Redirecting to apply for job {job['job_id']}...")
                            st.rerun()
                    
                    # Save job button
                    if st.button("Save Job", key=f"save_{job['job_id']}"):
                        save_job(st.session_state['user']['user_id'], job['job_id'])
                        st.success("Job saved!")
                
                st.markdown("---")
    
    conn.close()

def save_job(user_id, job_id):
    """Save a job for later"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO saved_jobs (user_id, job_id, saved_at)
            VALUES (?, ?, ?)
        """, (user_id, job_id, datetime.now().isoformat()))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving job: {str(e)}")
    finally:
        conn.close() 