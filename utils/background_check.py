import requests
import os
from datetime import datetime, timedelta
from utils.database import get_db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BackgroundCheckManager:
    # Load API configuration from environment variables
    API_KEY = os.getenv('BACKGROUND_CHECK_API_KEY')
    API_URL = os.getenv('BACKGROUND_CHECK_API_URL', 'https://api.backgroundcheck-provider.com/v1')
    PROVIDER = os.getenv('BACKGROUND_CHECK_PROVIDER', 'provider-name')
    
    @staticmethod
    def request_background_check(user_id, user_data):
        """Request a new background check for a user"""
        if not BackgroundCheckManager.API_KEY:
            print("Background check API key not configured")
            return {'status': 'error', 'message': 'Background check service not configured'}
            
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Check if user already has a valid background check
            cursor.execute("""
                SELECT * FROM background_checks
                WHERE user_id = ?
                AND valid_until > ?
                AND status = 'completed'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, datetime.now().isoformat()))
            
            existing_check = cursor.fetchone()
            if existing_check:
                return {
                    'status': 'valid',
                    'report_url': existing_check['report_url'],
                    'valid_until': existing_check['valid_until']
                }
            
            # Prepare background check request
            payload = {
                'first_name': user_data['name'].split()[0],
                'last_name': user_data['name'].split()[-1],
                'email': user_data['email'],
                'phone': user_data.get('phone', ''),
                'address': user_data.get('location', ''),
                'ssn_last4': user_data.get('ssn_last4', ''),  # Only last 4 digits for security
                'dob': user_data.get('dob', ''),
                'callback_url': f"{os.getenv('APP_URL', 'http://localhost:8000')}/api/background-check/callback/{user_id}"
            }
            
            # Make API request to background check provider
            headers = {
                'Authorization': f'Bearer {BackgroundCheckManager.API_KEY}',
                'Content-Type': 'application/json',
                'User-Agent': 'Workify/1.0'
            }
            
            try:
                response = requests.post(
                    f"{BackgroundCheckManager.API_URL}/checks",
                    json=payload,
                    headers=headers,
                    timeout=30  # 30 second timeout
                )
                response.raise_for_status()  # Raise exception for bad status codes
                
                check_data = response.json()
                
                # Store check request in database
                cursor.execute("""
                    INSERT INTO background_checks 
                    (user_id, status, provider, report_url, valid_until, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    'pending',
                    BackgroundCheckManager.PROVIDER,
                    None,
                    (datetime.now() + timedelta(days=365)).isoformat(),  # Valid for 1 year
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
                return {
                    'status': 'pending',
                    'check_id': check_data['check_id']
                }
            except requests.exceptions.RequestException as e:
                print(f"Background check API error: {str(e)}")
                return {
                    'status': 'error',
                    'message': 'Failed to communicate with background check service'
                }
                
        finally:
            conn.close()
    
    @staticmethod
    def handle_callback(check_id, status, report_data):
        """Handle background check completion callback"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            if status == 'completed':
                # Update background check record
                cursor.execute("""
                    UPDATE background_checks
                    SET status = ?, report_url = ?, updated_at = ?
                    WHERE check_id = ?
                """, ('completed', report_data['report_url'], 
                     datetime.now().isoformat(), check_id))
                
                # Get user details
                cursor.execute("""
                    SELECT user_id, email FROM users
                    WHERE user_id = (
                        SELECT user_id FROM background_checks
                        WHERE check_id = ?
                    )
                """, (check_id,))
                
                user = cursor.fetchone()
                if user:
                    # Send notification
                    cursor.execute("""
                        INSERT INTO notifications 
                        (user_id, message, created_at)
                        VALUES (?, ?, ?)
                    """, (
                        user['user_id'],
                        "Your background check has been completed successfully!",
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
                return True
            else:
                # Handle failed checks
                cursor.execute("""
                    UPDATE background_checks
                    SET status = ?, updated_at = ?
                    WHERE check_id = ?
                """, ('failed', datetime.now().isoformat(), check_id))
                
                conn.commit()
                return False
                
        finally:
            conn.close()
    
    @staticmethod
    def verify_background_check(user_id):
        """Verify if a user has a valid background check"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM background_checks
                WHERE user_id = ?
                AND valid_until > ?
                AND status = 'completed'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, datetime.now().isoformat()))
            
            check = cursor.fetchone()
            if check:
                return {
                    'verified': True,
                    'valid_until': check['valid_until'],
                    'report_url': check['report_url']
                }
            return {'verified': False}
            
        finally:
            conn.close()
    
    @staticmethod
    def get_background_check_status(user_id):
        """Get the current status of a user's background check"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT status, created_at, valid_until, report_url
                FROM background_checks
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            check = cursor.fetchone()
            if not check:
                return {
                    'status': 'not_started',
                    'message': 'No background check found'
                }
            
            return {
                'status': check['status'],
                'created_at': check['created_at'],
                'valid_until': check['valid_until'],
                'report_url': check['report_url']
            }
            
        finally:
            conn.close() 