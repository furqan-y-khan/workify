import streamlit as st
from utils.database import get_db
from datetime import datetime, timedelta

def check_job_posting_limits(user_id):
    """Check if user has reached their job posting limits"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check subscription status
        cursor.execute("""
            SELECT plan_id, status, valid_until 
            FROM subscriptions 
            WHERE user_id = ? AND status = 'active'
            AND valid_until > ?
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, datetime.now().isoformat()))
        subscription = cursor.fetchone()
        
        # Get number of jobs posted in the last 30 days
        cursor.execute("""
            SELECT COUNT(*) as job_count 
            FROM jobs 
            WHERE job_poster_id = ? 
            AND created_at >= ?
        """, (user_id, (datetime.now() - timedelta(days=30)).isoformat()))
        
        job_count = cursor.fetchone()['job_count']
        
        # Free users can post up to 3 jobs per month
        if not subscription and job_count >= 3:
            return False, "You have reached the maximum number of free job postings (3 per month). Please upgrade to Pro to post more jobs."
        
        return True, None
        
    finally:
        conn.close()

def show_post_jobs():
    """Show the job posting form"""
    st.title("Post a Job")
    
    user = st.session_state.get('user')
    if not user:
        st.error("Please log in to post jobs")
        return
    
    # Check posting limits
    can_post, limit_message = check_job_posting_limits(user['user_id'])
    if not can_post:
        st.error(limit_message)
        
        # Show upgrade button
        if st.button("Upgrade to Pro"):
            st.session_state['page'] = 'subscription'
            st.rerun()
        return
    
    with st.form("post_job_form"):
        # Basic Job Information
        title = st.text_input("Job Title", placeholder="e.g., Plumbing Work Needed, Electrical Repairs")
        
        # Job Type
        job_type = st.selectbox(
            "Job Type",
            ["One-time Job", "Regular Work", "Emergency Service", "Project Based"]
        )
        
        # Trade Category
        trade_category = st.selectbox(
            "Trade Category",
            [
                "Plumbing",
                "Electrical",
                "Carpentry",
                "Painting",
                "HVAC",
                "Landscaping",
                "Construction",
                "Cleaning",
                "Roofing",
                "General Maintenance",
                "Other"
            ]
        )
        
        # Number of Workers Needed
        workers_needed = st.number_input("Number of Workers Needed", min_value=1, value=1)
        
        # Location
        location = st.text_input("Location", placeholder="Enter the job location")
        
        # Payment Details
        col1, col2 = st.columns(2)
        with col1:
            payment_type = st.selectbox(
                "Payment Type",
                ["Fixed Price", "Hourly Rate", "To Be Discussed"]
            )
        with col2:
            payment_amount = None
            if payment_type in ["Fixed Price", "Hourly Rate"]:
                payment_amount = st.number_input(
                    "Amount ($)", 
                    min_value=0, 
                    value=100 if payment_type == "Fixed Price" else 25
                )
        
        # Timing
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            urgency = st.selectbox(
                "Urgency",
                ["Not Urgent", "Within a Week", "Within 48 Hours", "Emergency (24h)"]
            )
        
        # Detailed Description
        description = st.text_area(
            "Job Description",
            placeholder="Describe the job in detail. Include:\n" +
                      "- Specific tasks needed\n" +
                      "- Required materials (if any)\n" +
                      "- Special requirements\n" +
                      "- Any additional information"
        )
        
        # Requirements
        requirements = st.text_area(
            "Requirements",
            placeholder="List any specific requirements:\n" +
                      "- Required experience\n" +
                      "- Tools/equipment needed\n" +
                      "- Certifications/licenses\n" +
                      "- Insurance requirements"
        )
        
        # Tools Needed
        tools_needed = st.text_area(
            "Tools & Equipment Needed",
            placeholder="List any tools or equipment that will be needed for this job"
        )
        
        # Submit Button
        submitted = st.form_submit_button("Post Job")
        
        if submitted:
            if not title or not description or not location:
                st.error("Please fill in all required fields")
                return
            
            conn = get_db()
            cursor = conn.cursor()
            
            try:
                # Get current user
                user = st.session_state.get('user')
                if not user:
                    st.error("Please log in to post jobs")
                    return
                
                now = datetime.now().isoformat()
                
                # Insert job into database
                cursor.execute("""
                    INSERT INTO jobs (
                        job_poster_id, title, description, location,
                        job_type, trade_category, payment_type, payment_amount,
                        urgency, start_date, requirements, tools_needed,
                        status, created_at, updated_at, workers_needed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user['user_id'], title, description, location,
                    job_type, trade_category, payment_type, payment_amount,
                    urgency, start_date.isoformat(), requirements, tools_needed,
                    'Open', now, now, workers_needed
                ))
                
                conn.commit()
                st.success("Job posted successfully!")
                
                # Store the job_id in session state
                cursor.execute("SELECT last_insert_rowid()")
                job_id = cursor.fetchone()[0]
                st.session_state['last_posted_job_id'] = job_id
                
                # Redirect to dashboard
                st.session_state['page'] = 'poster_dashboard'
                st.switch_page("pages/dashboard.py")
                
            except Exception as e:
                error_msg = str(e)
                if error_msg and error_msg != "0":
                    st.error(f"Error posting job: {error_msg}")
                else:
                    st.error("An error occurred while posting the job. Please try again.")
            finally:
                conn.close() 