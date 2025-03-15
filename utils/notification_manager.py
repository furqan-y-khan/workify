import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from utils.database import get_db
from utils.location_manager import calculate_distance
from dotenv import load_dotenv
import streamlit as st
import sqlite3

# Load environment variables
load_dotenv()

class NotificationManager:
    # Email configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'JobCon')

    @staticmethod
    def send_email(to_email, subject, body):
        """Send email notification"""
        if not all([NotificationManager.SMTP_USERNAME, NotificationManager.SMTP_PASSWORD]):
            print("Email configuration missing. Please set up SMTP credentials.")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{NotificationManager.SMTP_FROM_NAME} <{NotificationManager.SMTP_USERNAME}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(NotificationManager.SMTP_SERVER, NotificationManager.SMTP_PORT)
            server.starttls()
            server.login(NotificationManager.SMTP_USERNAME, NotificationManager.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    @staticmethod
    def check_job_alerts():
        """Check for new jobs matching premium users' preferences"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Get premium users with active alerts
            cursor.execute("""
                SELECT u.*, ja.trade_categories, ja.keywords, ja.max_distance,
                       ja.min_pay, ja.job_types
                FROM users u
                JOIN job_alerts ja ON u.user_id = ja.user_id
                WHERE u.is_premium = 1 
                AND u.premium_until > ?
                AND ja.is_active = 1
            """, (datetime.now().isoformat(),))
            
            users = cursor.fetchall()
            
            for user in users:
                # Get jobs posted in the last hour
                cursor.execute("""
                    SELECT j.*, u.company_name, u.name as poster_name
                    FROM jobs j
                    JOIN users u ON j.job_poster_id = u.user_id
                    WHERE j.created_at > datetime('now', '-1 hour')
                    AND j.status = 'Open'
                """)
                
                new_jobs = cursor.fetchall()
                matching_jobs = []
                
                for job in new_jobs:
                    # Check if job matches user preferences
                    if user['trade_categories'] and job['trade_category'] not in user['trade_categories'].split(','):
                        continue
                        
                    if user['job_types'] and job['job_type'] not in user['job_types'].split(','):
                        continue
                        
                    if user['min_pay'] and job['payment_amount'] and job['payment_amount'] < user['min_pay']:
                        continue
                    
                    # Check distance if both locations are available
                    if (user['latitude'] and user['longitude'] and 
                        job['latitude'] and job['longitude'] and 
                        user['max_distance']):
                        
                        distance = calculate_distance(
                            user['latitude'], user['longitude'],
                            job['latitude'], job['longitude']
                        )
                        
                        if distance > user['max_distance']:
                            continue
                    
                    # Check keywords
                    if user['keywords']:
                        keywords = user['keywords'].lower().split(',')
                        job_text = f"{job['title']} {job['description']}".lower()
                        if not any(kw in job_text for kw in keywords):
                            continue
                    
                    matching_jobs.append(job)
                
                # Send notifications for matching jobs
                if matching_jobs:
                    # Create in-app notification
                    notification_text = f"Found {len(matching_jobs)} new job{'s' if len(matching_jobs) > 1 else ''} matching your preferences!"
                    cursor.execute("""
                        INSERT INTO notifications (user_id, message, created_at)
                        VALUES (?, ?, ?)
                    """, (user['user_id'], notification_text, datetime.now().isoformat()))
                    
                    # Send email notification
                    email_body = "<h2>New Jobs Matching Your Preferences</h2>"
                    for job in matching_jobs:
                        company = job['company_name'] or job['poster_name']
                        email_body += f"""
                            <div style='margin-bottom: 20px;'>
                                <h3>{job['title']} at {company}</h3>
                                <p>📍 {job['location']}</p>
                                <p>💰 {job['payment_type']}: ${job['payment_amount']}</p>
                                <p>{job['description'][:200]}...</p>
                            </div>
                        """
                    
                    NotificationManager.send_email(
                        user['email'],
                        "New Job Matches Found!",
                        email_body
                    )
            
            conn.commit()
            
        finally:
            conn.close()
    
    @staticmethod
    def send_application_update(application_id, status_change=True):
        """Send notification for application status updates"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT a.*, j.title, u.email, u.name,
                       jp.company_name, jp.name as poster_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.job_id
                JOIN users u ON a.applicant_id = u.user_id
                JOIN users jp ON j.job_poster_id = jp.user_id
                WHERE a.application_id = ?
            """, (application_id,))
            
            app = cursor.fetchone()
            if not app:
                return
            
            company = app['company_name'] or app['poster_name']
            
            # Send email notification
            subject = f"Application Update: {app['title']}"
            body = f"""
                <h2>Application Status Update</h2>
                <p>Your application for <strong>{app['title']}</strong> at {company}
                has been marked as <strong>{app['status']}</strong>.</p>
            """
            
            if app['status'] == 'Accepted':
                body += """
                    <p>Congratulations! The employer has accepted your application.
                    Please check your messages for further instructions.</p>
                """
            
            NotificationManager.send_email(app['email'], subject, body)
            
        finally:
            conn.close()
    
    @staticmethod
    def create_notification(user_id, message, link=None, notification_type='general'):
        """
        Create a notification for a user
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO notifications (user_id, message, link, is_read, created_at, notification_type)
                VALUES (?, ?, ?, 0, ?, ?)
                """,
                (user_id, message, link, datetime.now().isoformat(), notification_type)
            )
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating notification: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def mark_notification_read(notification_id):
        """
        Mark a notification as read
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE notifications
                SET is_read = 1
                WHERE notification_id = ?
                """,
                (notification_id,)
            )
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_notifications(user_id, limit=20, offset=0, include_read=False):
        """
        Get notifications for a user
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            if include_read:
                cursor.execute(
                    """
                    SELECT *
                    FROM notifications
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, limit, offset)
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM notifications
                    WHERE user_id = ? AND is_read = 0
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, limit, offset)
                )
            
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def get_unread_count(user_id):
        """
        Get count of unread notifications for a user
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM notifications
                WHERE user_id = ? AND is_read = 0
                """,
                (user_id,)
            )
            
            result = cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error getting unread notification count: {e}")
            return 0
        finally:
            conn.close()
    
    @staticmethod
    def notify_application_status_change(application_id, new_status):
        """
        Notify both job seeker and job poster about an application status change
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get application details including job title and usernames
            cursor.execute(
                """
                SELECT 
                    a.*, 
                    j.title as job_title,
                    j.job_poster_id,
                    u_seeker.name as applicant_name,
                    u_poster.name as poster_name,
                    u_poster.company_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.job_id
                JOIN users u_seeker ON a.applicant_id = u_seeker.user_id
                JOIN users u_poster ON j.job_poster_id = u_poster.user_id
                WHERE a.application_id = ?
                """,
                (application_id,)
            )
            
            app_details = cursor.fetchone()
            
            if not app_details:
                print(f"Could not find application with ID {application_id}")
                return False
            
            # Create the application link for notifications
            app_link = f"/applications?application_id={application_id}"
            
            # Create notification for the job seeker
            seeker_message = NotificationManager._get_status_change_message_for_seeker(
                new_status, 
                app_details.get('job_title', 'a job'), 
                app_details.get('company_name') or app_details.get('poster_name', 'the employer')
            )
            
            NotificationManager.create_notification(
                app_details['applicant_id'],
                seeker_message,
                app_link,
                'application_update'
            )
            
            # Create notification for the job poster
            poster_message = NotificationManager._get_status_change_message_for_poster(
                new_status, 
                app_details.get('job_title', 'your job posting'), 
                app_details.get('applicant_name', 'An applicant')
            )
            
            NotificationManager.create_notification(
                app_details['job_poster_id'],
                poster_message,
                app_link,
                'application_update'
            )
            
            # If status is accepted, create a message thread between job seeker and poster
            if new_status == 'Accepted':
                NotificationManager._create_accepted_message_thread(
                    app_details['applicant_id'],
                    app_details['job_poster_id'],
                    app_details['job_title'],
                    application_id
                )
            
            return True
        except Exception as e:
            print(f"Error notifying about application status change: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def _get_status_change_message_for_seeker(status, job_title, employer_name):
        """Generate notification message for job seeker based on status change"""
        if status == 'Accepted':
            return f"Congratulations! Your application for '{job_title}' has been accepted by {employer_name}."
        elif status == 'Rejected':
            return f"Your application for '{job_title}' was not selected by {employer_name}."
        elif status == 'Completed':
            return f"Your job '{job_title}' with {employer_name} has been marked as completed."
        elif status == 'Withdrawn':
            return f"You have withdrawn your application for '{job_title}'."
        else:
            return f"Your application status for '{job_title}' has been updated to {status}."
    
    @staticmethod
    def _get_status_change_message_for_poster(status, job_title, applicant_name):
        """Generate notification message for job poster based on status change"""
        if status == 'Accepted':
            return f"You've accepted {applicant_name}'s application for '{job_title}'."
        elif status == 'Rejected':
            return f"You've declined {applicant_name}'s application for '{job_title}'."
        elif status == 'Completed':
            return f"The job '{job_title}' with {applicant_name} has been marked as completed."
        elif status == 'Withdrawn':
            return f"{applicant_name} has withdrawn their application for '{job_title}'."
        else:
            return f"{applicant_name}'s application status for '{job_title}' has been updated to {status}."
    
    @staticmethod
    def _create_accepted_message_thread(seeker_id, poster_id, job_title, application_id):
        """
        Create initial message thread between job seeker and job poster when application is accepted
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get current time
            now = datetime.now().isoformat()
            
            # Try to create welcome message using either 'message' or 'content' field
            seeker_welcome = f"Congratulations on your application for '{job_title}'! You can use this chat to coordinate next steps with the employer."
            poster_welcome = f"You've accepted an application for '{job_title}'. Use this chat to coordinate next steps with the applicant."
            
            # First try with 'message' field
            try:
                # Message to job seeker
                cursor.execute(
                    """
                    INSERT INTO messages (sender_id, receiver_id, message, created_at, is_read, application_id)
                    VALUES (?, ?, ?, ?, 0, ?)
                    """,
                    (poster_id, seeker_id, seeker_welcome, now, application_id)
                )
                
                # Message to job poster
                cursor.execute(
                    """
                    INSERT INTO messages (sender_id, receiver_id, message, created_at, is_read, application_id)
                    VALUES (?, ?, ?, ?, 0, ?)
                    """,
                    (0, poster_id, poster_welcome, now, application_id)  # System message (sender_id = 0)
                )
            except sqlite3.OperationalError:
                # Try with 'content' field
                try:
                    # Message to job seeker
                    cursor.execute(
                        """
                        INSERT INTO messages (sender_id, receiver_id, content, created_at, is_read, application_id)
                        VALUES (?, ?, ?, ?, 0, ?)
                        """,
                        (poster_id, seeker_id, seeker_welcome, now, application_id)
                    )
                    
                    # Message to job poster
                    cursor.execute(
                        """
                        INSERT INTO messages (sender_id, receiver_id, content, created_at, is_read, application_id)
                        VALUES (?, ?, ?, ?, 0, ?)
                        """,
                        (0, poster_id, poster_welcome, now, application_id)  # System message (sender_id = 0)
                    )
                except Exception as e2:
                    print(f"Could not create welcome messages: {e2}")
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating message thread: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def notify_message_received(sender_id, receiver_id, message_id=None):
        """
        Create a notification for a new message
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get sender info
            cursor.execute("SELECT name, company_name FROM users WHERE user_id = ?", (sender_id,))
            sender = cursor.fetchone()
            
            if not sender:
                return False
            
            sender_name = sender['company_name'] or sender['name']
            
            # Create notification message
            message = f"You have a new message from {sender_name}"
            
            # Create link to messages page
            link = f"/messages?user_id={sender_id}"
            
            # Create notification
            NotificationManager.create_notification(
                receiver_id,
                message,
                link,
                'message'
            )
            
            return True
        except Exception as e:
            print(f"Error notifying about message: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def notify_new_application(application_id):
        """
        Notify job poster about a new application
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get application details
            cursor.execute(
                """
                SELECT 
                    a.*, 
                    j.title as job_title,
                    j.job_poster_id,
                    u.name as applicant_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.job_id
                JOIN users u ON a.applicant_id = u.user_id
                WHERE a.application_id = ?
                """,
                (application_id,)
            )
            
            app_details = cursor.fetchone()
            
            if not app_details:
                return False
            
            # Create notification message
            message = f"{app_details['applicant_name']} has applied for '{app_details['job_title']}'"
            
            # Create link to applications page
            link = f"/applications?view=received&application_id={application_id}"
            
            # Create notification
            NotificationManager.create_notification(
                app_details['job_poster_id'],
                message,
                link,
                'new_application'
            )
            
            return True
        except Exception as e:
            print(f"Error notifying about new application: {e}")
            return False
        finally:
            conn.close() 