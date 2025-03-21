import streamlit as st
from utils.database import get_db
from datetime import datetime
from utils.notification_manager import NotificationManager

def show_applications():
    """Show the applications page for both job seekers and job posters"""
    user = st.session_state.get('user')
    if not user:
        st.error("Please log in to view applications")
        return
    
    # Debug mode to see application details
    debug_mode = st.session_state.get('debug_applications', False)
    if st.sidebar.checkbox("Debug Mode", value=debug_mode):
        st.session_state['debug_applications'] = True
    else:
        st.session_state['debug_applications'] = False
    
    # Set up tabs for applications
    if user['role'] == 'Job Seeker':
        show_seeker_applications(user)
    else:
        show_poster_applications(user)

def show_seeker_applications(user):
    """Show applications for a job seeker"""
    st.title("My Applications")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Query to get all applications by this seeker
    try:
        cursor.execute("""
            SELECT 
                a.*,
                j.title as job_title,
                j.company_name,
                j.job_poster_id,
                u.name as poster_name,
                u.company_name as poster_company_name,
                (SELECT COUNT(*) FROM messages 
                 WHERE receiver_id = ? 
                 AND sender_id = j.job_poster_id 
                 AND is_read = 0) as unread_messages
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN users u ON j.job_poster_id = u.user_id
            WHERE a.applicant_id = ?
            ORDER BY 
                CASE a.status
                    WHEN 'Pending' THEN 1
                    WHEN 'Accepted' THEN 2
                    WHEN 'Completed' THEN 3
                    WHEN 'Withdrawn' THEN 4
                    WHEN 'Rejected' THEN 5
                    ELSE 6
                END,
                a.updated_at DESC
        """, (user['user_id'], user['user_id']))
        
        applications = cursor.fetchall()
        
        if st.session_state.get('debug_applications'):
            st.write("Debug: Applications fetched:", len(applications))
            st.json(applications)
        
        if not applications:
            st.info("You haven't applied to any jobs yet.")
            
            # Add Browse Jobs button to navigate to job search
            if st.button("Browse Jobs", use_container_width=True):
                st.session_state['prev_page'] = 'applications'
                st.switch_page("pages/dashboard.py")
            return
        
        # Add Browse Jobs button at the top
        if st.button("Browse Jobs", use_container_width=True):
            st.session_state['prev_page'] = 'applications'
            st.switch_page("pages/dashboard.py")
        
        # Display applications
        selected_application_id = st.session_state.get('selected_application_id')
        
        # Filter options
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Pending", "Accepted", "Rejected", "Completed", "Withdrawn"],
            index=0
        )
        
        filtered_applications = applications
        if status_filter != "All":
            filtered_applications = [a for a in applications if a['status'] == status_filter]
        
        # Create a card for each application
        for app in filtered_applications:
            company_name = app['poster_company_name'] or app['poster_name']
            
            # Determine badge color based on status
            status_colors = {
                'Pending': 'blue',
                'Accepted': 'green',
                'Rejected': 'red',
                'Completed': 'purple',
                'Withdrawn': 'gray'
            }
            status_color = status_colors.get(app['status'], 'gray')
            
            # Create the application card
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {app['job_title']}")
                    st.markdown(f"**Company:** {company_name}")
                    st.markdown(f"**Applied:** {app['created_at'][:10]}")
                    st.markdown(f"**Status:** :{status_color}[{app['status']}]")
                
                with col2:
                    # Add buttons for actions
                    if app['status'] == 'Pending':
                        if st.button("Withdraw", key=f"withdraw_{app['application_id']}"):
                            update_application_status(app['application_id'], 'Withdrawn')
                            st.rerun()
                    
                    if app['status'] == 'Accepted':
                        if st.button("Mark Completed", key=f"complete_{app['application_id']}"):
                            update_application_status(app['application_id'], 'Completed')
                            st.rerun()
                        
                        # Show message button with unread count
                        message_label = "Message Employer"
                        if app['unread_messages'] > 0:
                            message_label = f"Message Employer ({app['unread_messages']} unread)"
                        
                        if st.button(message_label, key=f"message_{app['application_id']}"):
                            # Set up session state for messages page
                            st.session_state['message_user_id'] = app['job_poster_id']
                            st.session_state['current_job_context'] = app['job_title']
                            st.session_state['prev_page'] = 'applications'
                            st.switch_page("pages/messages.py")
                
                # Application details
                if st.button("View Details", key=f"details_{app['application_id']}"):
                    if selected_application_id == app['application_id']:
                        st.session_state['selected_application_id'] = None  # Toggle off
                    else:
                        st.session_state['selected_application_id'] = app['application_id']  # Toggle on
                    st.rerun()
                
                # Show application details if selected
                if selected_application_id == app['application_id']:
                    try:
                        cursor.execute("""
                            SELECT * FROM application_fields
                            WHERE application_id = ?
                        """, (app['application_id'],))
                        
                        fields = cursor.fetchall()
                        
                        if fields:
                            st.subheader("Application Details")
                            for field in fields:
                                st.markdown(f"**{field['field_name']}:** {field['field_value']}")
                        else:
                            st.info("No detailed information available for this application.")
                    except Exception as e:
                        st.error(f"Could not load application details: {str(e)}")
                
                st.divider()
    
    except Exception as e:
        st.error(f"An error occurred while loading applications: {str(e)}")
    
    finally:
        conn.close()

def show_poster_applications(user):
    """Show applications received by a job poster"""
    st.title("Applications Received")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get the job poster's posted jobs
        cursor.execute("""
            SELECT job_id, title FROM jobs WHERE job_poster_id = ?
        """, (user['user_id'],))
        
        jobs = cursor.fetchall()
        
        if not jobs:
            st.info("You haven't posted any jobs yet.")
            return
        
        # Create a dropdown to filter by job
        job_titles = ["All Jobs"] + [job['title'] for job in jobs]
        job_ids = [None] + [job['job_id'] for job in jobs]
        
        job_index = 0
        selected_job_id = st.session_state.get('selected_job_id')
        if selected_job_id:
            try:
                job_index = job_ids.index(selected_job_id)
            except ValueError:
                job_index = 0
        
        selected_job_title = st.selectbox("Filter by job posting", job_titles, index=job_index)
        
        if selected_job_title != "All Jobs":
            selected_job_id = jobs[job_titles.index(selected_job_title) - 1]['job_id']
            st.session_state['selected_job_id'] = selected_job_id
        else:
            selected_job_id = None
            st.session_state['selected_job_id'] = None
        
        # Filter for status
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Pending", "Accepted", "Rejected", "Completed", "Withdrawn"],
            index=0
        )
        
        # Build query based on filters
        query = """
            SELECT 
                a.*,
                j.title as job_title,
                u.name as applicant_name,
                u.email as applicant_email,
                u.phone as applicant_phone,
                (SELECT COUNT(*) FROM messages 
                 WHERE receiver_id = ? 
                 AND sender_id = a.applicant_id 
                 AND is_read = 0) as unread_messages
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN users u ON a.applicant_id = u.user_id
            WHERE j.job_poster_id = ?
        """
        
        params = [user['user_id'], user['user_id']]
        
        if selected_job_id:
            query += " AND j.job_id = ?"
            params.append(selected_job_id)
        
        if status_filter != "All":
            query += " AND a.status = ?"
            params.append(status_filter)
        
        query += """
            ORDER BY 
                CASE a.status
                    WHEN 'Pending' THEN 1
                    WHEN 'Accepted' THEN 2
                    WHEN 'Completed' THEN 3
                    WHEN 'Withdrawn' THEN 4
                    WHEN 'Rejected' THEN 5
                    ELSE 6
                END,
                a.updated_at DESC
        """
        
        cursor.execute(query, tuple(params))
        applications = cursor.fetchall()
        
        if st.session_state.get('debug_applications'):
            st.write("Debug: Applications fetched:", len(applications))
            st.json(applications)
        
        if not applications:
            st.info("No applications match your filters.")
            return
        
        # Get the selected application ID from session state
        selected_application_id = st.session_state.get('selected_application_id')
        
        # Display applications
        for app in applications:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {app['job_title']}")
                    st.markdown(f"**Applicant:** {app['applicant_name']}")
                    st.markdown(f"**Applied:** {app['created_at'][:10]}")
                    
                    # Determine badge color based on status
                    status_colors = {
                        'Pending': 'blue',
                        'Accepted': 'green',
                        'Rejected': 'red',
                        'Completed': 'purple',
                        'Withdrawn': 'gray'
                    }
                    status_color = status_colors.get(app['status'], 'gray')
                    st.markdown(f"**Status:** :{status_color}[{app['status']}]")
                
                with col2:
                    # Action buttons based on status
                    if app['status'] == 'Pending':
                        cols = st.columns(2)
                        with cols[0]:
                            if st.button("Accept", key=f"accept_{app['application_id']}"):
                                update_application_status(app['application_id'], 'Accepted')
                                st.rerun()
                        with cols[1]:
                            if st.button("Reject", key=f"reject_{app['application_id']}"):
                                update_application_status(app['application_id'], 'Rejected')
                                st.rerun()
                    
                    if app['status'] == 'Accepted':
                        # Show message button with unread count
                        message_label = "Message Applicant"
                        if app['unread_messages'] > 0:
                            message_label = f"Message ({app['unread_messages']} unread)"
                        
                        if st.button(message_label, key=f"message_{app['application_id']}"):
                            # Set up session state for messages page
                            st.session_state['message_user_id'] = app['applicant_id']
                            st.session_state['current_job_context'] = app['job_title']
                            st.session_state['prev_page'] = 'applications'
                            st.switch_page("pages/messages.py")
                
                # Application details
                if st.button("View Details", key=f"details_{app['application_id']}"):
                    if selected_application_id == app['application_id']:
                        st.session_state['selected_application_id'] = None  # Toggle off
                    else:
                        st.session_state['selected_application_id'] = app['application_id']  # Toggle on
                    st.rerun()
                
                # Show application details if selected
                if selected_application_id == app['application_id']:
                    with st.expander("Applicant Contact Information", expanded=True):
                        st.markdown(f"**Email:** {app['applicant_email']}")
                        if app['applicant_phone']:
                            st.markdown(f"**Phone:** {app['applicant_phone']}")
                    
                    try:
                        cursor.execute("""
                            SELECT * FROM application_fields
                            WHERE application_id = ?
                        """, (app['application_id'],))
                        
                        fields = cursor.fetchall()
                        
                        if fields:
                            st.subheader("Application Details")
                            for field in fields:
                                st.markdown(f"**{field['field_name']}:** {field['field_value']}")
                        else:
                            st.info("No detailed information available for this application.")
                    except Exception as e:
                        st.error(f"Could not load application details: {str(e)}")
                
                st.divider()
    
    except Exception as e:
        st.error(f"An error occurred while loading applications: {str(e)}")
    
    finally:
        conn.close()

def update_application_status(application_id, new_status):
    """Update the status of an application and create notifications"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Update the application status
        cursor.execute("""
            UPDATE applications 
            SET status = ?, updated_at = ? 
            WHERE application_id = ?
        """, (new_status, datetime.now().isoformat(), application_id))
        
        conn.commit()
        
        # Create notifications
        try:
            NotificationManager.notify_application_status_change(application_id, new_status)
        except Exception as e:
            st.warning(f"Notification could not be sent, but status was updated: {str(e)}")
        
        st.success(f"Application status updated to {new_status}")
        return True
        
    except Exception as e:
        st.error(f"Could not update application status: {str(e)}")
        return False
    
    finally:
        conn.close()
