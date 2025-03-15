import streamlit as st
import time
from datetime import datetime
from utils.database import get_db
from utils.notification_manager import NotificationManager

def apply_job():
    """Show job application form for job seekers"""
    user = st.session_state.get('user')
    
    if not user:
        st.error("Please log in to apply for jobs")
        time.sleep(1.5)
        st.switch_page("pages/landing.py")
        return
    
    if user['role'] != 'Job Seeker':
        st.error("Only Job Seekers can apply for jobs")
        time.sleep(1.5)
        st.switch_page("pages/dashboard.py")
        return
    
    # Get job ID from query parameters or session state
    job_id = st.query_params.get('job_id')
    
    # Fall back to session state if query param is not available
    if not job_id:
        job_id = st.session_state.get('apply_job_id')
    
    # Enable debug mode for troubleshooting
    debug_mode = st.session_state.get('debug_mode', False)
    if st.sidebar.checkbox("Debug Mode", value=debug_mode):
        st.session_state['debug_mode'] = True
        debug_mode = True
        st.sidebar.write(f"Job ID: {job_id}")
        st.sidebar.write(f"Session state: {st.session_state}")
    else:
        st.session_state['debug_mode'] = False
    
    if not job_id:
        st.error("No job selected. Please browse jobs first.")
        time.sleep(1.5)
        st.switch_page("pages/dashboard.py")
        return
    
    # Check if user already applied for this job
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM applications
            WHERE applicant_id = ? AND job_id = ?
        """, (user['user_id'], job_id))
        
        existing_application = cursor.fetchone()
        
        if existing_application:
            st.warning("You have already applied for this job.")
            
            # Show application status
            st.info(f"Your application status: {existing_application['status']}")
            
            # Add a button to return to dashboard
            if st.button("Return to Dashboard"):
                st.switch_page("pages/dashboard.py")
            
            return
    
        # Get job details
        try:
            cursor.execute("""
                SELECT j.*, u.name as poster_name, u.company_name, u.user_id as poster_id
                FROM jobs j
                JOIN users u ON j.job_poster_id = u.user_id
                WHERE j.job_id = ?
            """, (job_id,))
        except Exception as e:
            if debug_mode:
                st.sidebar.error(f"Error with first query: {str(e)}")
            
            # Fallback to simpler query if first one fails
            cursor.execute("""
                SELECT * FROM jobs WHERE job_id = ?
            """, (job_id,))
            
            if debug_mode:
                st.sidebar.warning("Using simplified fallback query due to schema differences")
        
        job = cursor.fetchone()
        
        if not job:
            st.error("Job not found or no longer available")
            time.sleep(1.5)
            try:
                st.switch_page("pages/dashboard.py")
            except:
                st.session_state['page'] = 'dashboard'
                st.rerun()
            return
        
        # Display job details
        company_name = job.get('company_name') or job.get('poster_name', 'Unknown Company')
        st.title(f"Apply for: {job['title']}")
        st.subheader(f"at {company_name}")
        
        # Job details
        details_col1, details_col2 = st.columns(2)
        with details_col1:
            st.markdown(f"**Location:** {job['location']}")
            st.markdown(f"**Job Type:** {job['job_type']}")
        
        with details_col2:
            if job['pay_rate']:
                st.markdown(f"**Pay Rate:** ${job['pay_rate']}/hr")
            
            workers_needed = job.get('workers_needed', 1)
            if workers_needed > 1:
                st.markdown(f"**Positions Available:** {workers_needed}")
        
        # Job description
        st.markdown("### Job Description")
        st.markdown(job['description'])
        
        # Requirements
        if job.get('requirements'):
            st.markdown("### Requirements")
            st.markdown(job['requirements'])
        
        # Additional questions
        questions = []
        try:
            cursor.execute("""
                SELECT * FROM job_questions
                WHERE job_id = ?
                ORDER BY question_order
            """, (job_id,))
            
            questions = cursor.fetchall()
        except Exception as e:
            if debug_mode:
                st.sidebar.error(f"Error fetching job questions: {str(e)}")
        
        # Application form
        st.markdown("### Your Application")
        
        with st.form("application_form"):
            # Basic fields
            cover_letter = st.text_area("Cover Letter/Introduction", 
                                       placeholder="Introduce yourself and explain why you're a good fit for this position...")
            
            experience = st.text_area("Relevant Experience", 
                                     placeholder="Describe your experience relevant to this position...")
            
            expected_pay = st.number_input("Expected Pay Rate ($/hr)", 
                                          min_value=float(job.get('pay_rate', 0)), 
                                          value=float(job.get('pay_rate', 15.0)),
                                          step=1.0)
            
            availability = st.text_area("Availability", 
                                       placeholder="When are you available to work?")
            
            # Custom questions
            custom_answers = {}
            for q in questions:
                if q['question_type'] == 'text':
                    custom_answers[q['question_id']] = st.text_area(q['question_text'], key=f"q_{q['question_id']}")
                elif q['question_type'] == 'choice':
                    options = q.get('options', '').split(',')
                    custom_answers[q['question_id']] = st.selectbox(q['question_text'], options, key=f"q_{q['question_id']}")
                elif q['question_type'] == 'number':
                    custom_answers[q['question_id']] = st.number_input(q['question_text'], key=f"q_{q['question_id']}")
            
            submitted = st.form_submit_button("Submit Application")
        
        if submitted:
            # Insert application into database
            try:
                cursor.execute("""
                    INSERT INTO applications 
                    (job_id, applicant_id, status, created_at, updated_at, cover_letter, experience, expected_pay, availability)
                    VALUES (?, ?, 'Pending', ?, ?, ?, ?, ?, ?)
                """, (
                    job_id, 
                    user['user_id'], 
                    datetime.now().isoformat(), 
                    datetime.now().isoformat(),
                    cover_letter,
                    experience,
                    expected_pay,
                    availability
                ))
                
                application_id = cursor.lastrowid
                
                # Insert custom answers
                for question_id, answer in custom_answers.items():
                    cursor.execute("""
                        INSERT INTO application_fields 
                        (application_id, field_name, field_value)
                        VALUES (?, ?, ?)
                    """, (
                        application_id,
                        f"Question {question_id}",
                        str(answer)
                    ))
                
                conn.commit()
                
                # Notify job poster
                try:
                    NotificationManager.notify_new_application(application_id)
                except Exception as e:
                    if debug_mode:
                        st.sidebar.error(f"Error sending notification: {str(e)}")
                
                st.success("Application submitted successfully!")
                
                # Give the user time to see the success message
                time.sleep(2)
                
                # Redirect back to dashboard
                try:
                    st.switch_page("pages/applications.py")
                except Exception as e:
                    if debug_mode:
                        st.sidebar.error(f"Error navigating: {str(e)}")
                    st.session_state['page'] = 'applications'
                    st.rerun()
                
            except Exception as e:
                st.error(f"Error submitting application: {str(e)}")
                if debug_mode:
                    st.sidebar.error(f"Detailed error: {str(e)}")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        if debug_mode:
            st.sidebar.error(f"Detailed error: {str(e)}")
    
    finally:
        conn.close()

def show_apply_job():
    """Compatibility function to call the main apply_job function"""
    apply_job()

# If this script is run directly
if __name__ == "__main__":
    apply_job()
