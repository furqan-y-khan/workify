import streamlit as st
from utils.database import get_db
from datetime import datetime
import time

def show_messages():
    """Show messaging interface"""
    user = st.session_state.get('user')
    
    if not user:
        st.error("Please log in to view messages")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    # First, check the schema of the messages table
    try:
        cursor.execute("PRAGMA table_info(messages)")
        columns = {col['name'] for col in cursor.fetchall()}
        message_column = 'message' if 'message' in columns else 'content'
        
        if not ('message' in columns or 'content' in columns):
            st.error("Message table schema is incompatible. Please contact support.")
            return
    except Exception as e:
        st.error("Unable to access messages. Please try again later.")
        return
    
    try:
        # Get all conversations - use the correct column name
        query = f"""
            SELECT DISTINCT 
                CASE 
                    WHEN m.sender_id = ? THEN m.receiver_id 
                    ELSE m.sender_id 
                END as other_user_id,
                u.name as other_user_name,
                u.company_name,
                (SELECT COUNT(*) FROM messages 
                 WHERE receiver_id = ? 
                 AND sender_id = other_user_id 
                 AND is_read = 0) as unread_count,
                (SELECT {message_column} FROM messages 
                 WHERE (sender_id = ? AND receiver_id = other_user_id)
                 OR (sender_id = other_user_id AND receiver_id = ?)
                 ORDER BY created_at DESC LIMIT 1) as last_message
            FROM messages m
            JOIN users u ON u.user_id = 
                CASE 
                    WHEN m.sender_id = ? THEN m.receiver_id 
                    ELSE m.sender_id 
                END
            WHERE m.sender_id = ? OR m.receiver_id = ?
            ORDER BY (SELECT created_at FROM messages 
                     WHERE (sender_id = ? AND receiver_id = other_user_id)
                     OR (sender_id = other_user_id AND receiver_id = ?)
                     ORDER BY created_at DESC LIMIT 1) DESC
        """
        
        cursor.execute(query, (
            user['user_id'], user['user_id'], 
            user['user_id'], user['user_id'],
            user['user_id'], user['user_id'], user['user_id'],
            user['user_id'], user['user_id']
        ))
        
        conversations = cursor.fetchall()
        
        # Check if we have any application context data to display
        related_applications = []
        if user['role'] == 'Job Seeker':
            # Get applications for this job seeker to provide context
            cursor.execute("""
                SELECT a.*, j.title as job_title, u.name as poster_name, u.company_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.job_id
                JOIN users u ON j.job_poster_id = u.user_id
                WHERE a.applicant_id = ? AND a.status = 'Accepted'
                ORDER BY a.updated_at DESC
            """, (user['user_id'],))
            related_applications = cursor.fetchall()
        elif user['role'] == 'Job Poster':
            # Get applications for this job poster to provide context
            cursor.execute("""
                SELECT a.*, j.title as job_title, u.name as applicant_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.job_id
                JOIN users u ON a.applicant_id = u.user_id
                WHERE j.job_poster_id = ? AND a.status = 'Accepted'
                ORDER BY a.updated_at DESC
            """, (user['user_id'],))
            related_applications = cursor.fetchall()
        
        # Get or set the current conversation partner
        current_partner = st.session_state.get('message_user_id')
        
        # Create a two-column layout
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Show conversation list
            st.subheader("Conversations")
            
            # First show related applications for easy access
            if related_applications:
                st.write("#### Active Jobs")
                for app in related_applications:
                    if user['role'] == 'Job Seeker':
                        other_id = app['job_poster_id']
                        other_name = app['company_name'] or app['poster_name']
                        label = f"📋 {app['job_title']} ({other_name})"
                    else:  # Job Poster
                        other_id = app['applicant_id']
                        other_name = app['applicant_name']
                        label = f"📋 {app['job_title']} ({other_name})"
                    
                    if st.button(label, key=f"app_{app['application_id']}"):
                        current_partner = other_id
                        st.session_state['message_user_id'] = current_partner
                        st.session_state['current_job_context'] = app['job_title']
                        st.rerun()
            
            # Then show all conversations
            if conversations:
                st.write("#### All Messages")
                for conv in conversations:
                    other_name = conv['company_name'] or conv['other_user_name']
                    if conv['unread_count'] > 0:
                        label = f"📫 {other_name} ({conv['unread_count']})"
                    else:
                        label = f"📪 {other_name}"
                    
                    if st.button(label, key=f"conv_{conv['other_user_id']}"):
                        current_partner = conv['other_user_id']
                        st.session_state['message_user_id'] = current_partner
                        st.rerun()
            else:
                st.info("No conversations yet")
        
        with col2:
            # Show current conversation
            if current_partner:
                cursor.execute("SELECT name, company_name, role FROM users WHERE user_id = ?", (current_partner,))
                partner = cursor.fetchone()
                
                if not partner:
                    st.error("Could not find the user you're trying to message.")
                    return
                
                partner_name = partner['company_name'] or partner['name']
                
                # Job context header
                job_context = st.session_state.get('current_job_context')
                if job_context:
                    st.header(f"Messages about: {job_context}")
                    st.subheader(f"With: {partner_name}")
                else:
                    st.header(f"Chat with {partner_name}")
                
                # Get messages using the detected column
                query = f"""
                    SELECT m.*, u.name as sender_name, u.company_name,
                           m.{message_column} as message_text
                    FROM messages m
                    JOIN users u ON m.sender_id = u.user_id
                    WHERE (m.sender_id = ? AND m.receiver_id = ?)
                    OR (m.sender_id = ? AND m.receiver_id = ?)
                    ORDER BY m.created_at ASC
                """
                
                cursor.execute(query, (user['user_id'], current_partner, current_partner, user['user_id']))
                messages = cursor.fetchall()
                
                # Mark messages as read
                try:
                    cursor.execute("""
                        UPDATE messages 
                        SET is_read = 1 
                        WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
                    """, (current_partner, user['user_id']))
                    conn.commit()
                except Exception:
                    pass  # Silent error handling for marking messages as read
                
                # Messages container with scrollable height
                message_container = st.container(height=400)
                
                # Show messages
                with message_container:
                    if not messages:
                        st.info("No messages yet. Send a message to start the conversation.")
                    else:
                        for msg in messages:
                            is_own_message = msg['sender_id'] == user['user_id']
                            sender_name = "You" if is_own_message else (msg['company_name'] or msg['sender_name'])
                            
                            # Get the message content using the consistent field name and strip any HTML
                            message_content = msg.get('message_text', '')
                            # Remove any HTML div tags that might have been included
                            message_content = message_content.replace('<div>', '').replace('</div>', '')
                            
                            if not message_content:
                                continue  # Skip empty messages
                            
                            message_time = msg['created_at'][:16].replace('T', ' ')
                            
                            # Simplified message display without excessive HTML
                            if is_own_message:
                                st.container().markdown(f"""
                                    <div style="text-align: right; margin: 10px 0;">
                                        <small style="color: #666;">{message_time}</small><br>
                                        <div style="background-color: #0084ff; color: white; padding: 10px; border-radius: 15px; display: inline-block; max-width: 80%; text-align: left;">
                                            {message_content}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.container().markdown(f"""
                                    <div style="text-align: left; margin: 10px 0;">
                                        <small style="color: #666;">{sender_name} - {message_time}</small><br>
                                        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 15px; display: inline-block; max-width: 80%;">
                                            {message_content}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                
                # Message input
                st.write("### Send a message")
                
                # Check if we have a message template
                default_message = ""
                if 'message_template' in st.session_state:
                    default_message = st.session_state['message_template']
                    # Clear it after use
                    st.session_state['message_template'] = ""
                
                # Use a form for message submission to avoid session state issues
                with st.form(key="message_form", clear_on_submit=True):
                    new_message = st.text_area("Type your message", value=default_message, height=100, key="message_input")
                    send_button = st.form_submit_button("Send Message", use_container_width=True)
                
                    if send_button and new_message.strip():
                        # Remove any HTML div tags that might be in the message
                        clean_message = new_message.strip().replace('<div>', '').replace('</div>', '')
                        
                        # Check if the table has an 'other_user_id' column
                        has_other_user_id = 'other_user_id' in columns
                        
                        try:
                            if has_other_user_id:
                                # Schema with other_user_id column
                                query = f"""
                                    INSERT INTO messages (
                                        sender_id, receiver_id, {message_column}, 
                                        other_user_id, created_at, is_read
                                    ) VALUES (?, ?, ?, ?, ?, 0)
                                """
                                cursor.execute(query, (
                                    user['user_id'], 
                                    current_partner, 
                                    clean_message,
                                    current_partner,  # other_user_id is set to the conversation partner
                                    datetime.now().isoformat()
                                ))
                            else:
                                # Standard schema without other_user_id
                                query = f"""
                                    INSERT INTO messages (
                                        sender_id, receiver_id, {message_column}, 
                                        created_at, is_read
                                    ) VALUES (?, ?, ?, ?, 0)
                                """
                                cursor.execute(query, (
                                    user['user_id'], 
                                    current_partner, 
                                    clean_message, 
                                    datetime.now().isoformat()
                                ))
                            
                            conn.commit()
                            st.success("Message sent!")
                            time.sleep(0.5)  # Small delay to show success
                            st.rerun()
                        except Exception:
                            st.error("Unable to send message. Please try again.")
            else:
                st.info("Select a conversation from the left to start chatting.")
                
    except Exception:
        st.error("An error occurred while loading messages. Please refresh and try again.")
    finally:
        conn.close() 