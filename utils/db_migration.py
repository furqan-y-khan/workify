import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('workify.db')
    conn.row_factory = sqlite3.Row
    return conn

def drop_all_tables():
    """Drop all existing tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # Drop each table
        for table in tables:
            if table['name'] != 'sqlite_sequence':
                cursor.execute(f"DROP TABLE IF EXISTS {table['name']}")
        
        conn.commit()
        print("All tables dropped successfully")
        
    except Exception as e:
        print(f"Error dropping tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Create users table with all necessary fields and correct data types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT,
                role TEXT NOT NULL,
                company_name TEXT,
                company_description TEXT,
                location TEXT,
                latitude REAL,
                longitude REAL,
                picture_url TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                skills TEXT,
                experience_years INTEGER,
                preferred_trades TEXT,
                hourly_rate REAL,
                availability TEXT,
                background_check_status TEXT,
                background_check_date TEXT,
                rating REAL DEFAULT 0,
                reviews_count INTEGER DEFAULT 0,
                last_active TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        # Create jobs table with consistent foreign key types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_poster_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                job_type TEXT NOT NULL,
                trade_category TEXT NOT NULL,
                payment_type TEXT,
                payment_amount REAL,
                workers_needed INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Open',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (job_poster_id) REFERENCES users (user_id)
            )
        """)
        
        # Create applications table with consistent foreign key types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                job_poster_id TEXT NOT NULL,
                applicant_id TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                cover_letter TEXT,
                tools_equipment TEXT,
                licenses_certs TEXT,
                approach TEXT,
                reference_info TEXT,
                preferred_contact TEXT,
                is_read INTEGER DEFAULT 0,
                response_time INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (job_id),
                FOREIGN KEY (job_poster_id) REFERENCES users (user_id),
                FOREIGN KEY (applicant_id) REFERENCES users (user_id)
            )
        """)
        
        # Create work_history table with consistent foreign key types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                company_name TEXT NOT NULL,
                position TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                description TEXT,
                trade_category TEXT NOT NULL,
                is_verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create certifications table with consistent foreign key types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certifications (
                cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                issuing_authority TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                expiry_date TEXT,
                certificate_number TEXT,
                verification_url TEXT,
                is_verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create background_checks table with consistent foreign key types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS background_checks (
                check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL,
                provider TEXT NOT NULL,
                report_url TEXT,
                valid_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create messages table with consistent foreign key types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                other_user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (sender_id) REFERENCES users (user_id),
                FOREIGN KEY (receiver_id) REFERENCES users (user_id),
                FOREIGN KEY (other_user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create notifications table with consistent foreign key types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create job_alerts table with consistent foreign key types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_alerts (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                trade_category TEXT,
                location TEXT,
                max_distance INTEGER,
                min_pay REAL,
                job_type TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        conn.commit()
        print("Database schema initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_user_locations():
    """Update user profiles with location data"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get users without coordinates
        cursor.execute("""
            SELECT user_id, location 
            FROM users 
            WHERE location IS NOT NULL 
            AND (latitude IS NULL OR longitude IS NULL)
        """)
        users = cursor.fetchall()
        
        if users:
            from utils.location_manager import geocode_address
            
            for user in users:
                if user['location']:
                    location = geocode_address(user['location'])
                    if location:
                        cursor.execute("""
                            UPDATE users 
                            SET latitude = ?, longitude = ?
                            WHERE user_id = ?
                        """, (location['lat'], location['lon'], user['user_id']))
            
            conn.commit()
            print(f"Updated coordinates for {len(users)} users")
        else:
            print("No users need location updates")
            
    except Exception as e:
        print(f"Error migrating user locations: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def add_premium_fields():
    """Add premium-related fields to existing tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Add fields to applications table
        cursor.execute("PRAGMA table_info(applications)")
        columns = {col['name'] for col in cursor.fetchall()}
        
        if 'job_poster_id' not in columns:
            cursor.execute("ALTER TABLE applications ADD COLUMN job_poster_id TEXT REFERENCES users(user_id)")
        if 'approach' not in columns:
            cursor.execute("ALTER TABLE applications ADD COLUMN approach TEXT")
        if 'reference_info' not in columns:
            cursor.execute("ALTER TABLE applications ADD COLUMN reference_info TEXT")
        if 'preferred_contact' not in columns:
            cursor.execute("ALTER TABLE applications ADD COLUMN preferred_contact TEXT")
        if 'is_read' not in columns:
            cursor.execute("ALTER TABLE applications ADD COLUMN is_read INTEGER DEFAULT 0")
        if 'response_time' not in columns:
            cursor.execute("ALTER TABLE applications ADD COLUMN response_time INTEGER")
        
        # Add fields to messages table
        cursor.execute("PRAGMA table_info(messages)")
        columns = {col['name'] for col in cursor.fetchall()}
        
        if 'message' not in columns and 'content' in columns:
            cursor.execute("ALTER TABLE messages RENAME COLUMN content TO message")
        elif 'message' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN message TEXT")
        if 'other_user_id' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN other_user_id TEXT REFERENCES users(user_id)")
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN updated_at TEXT")
        
        # Add fields to users table
        cursor.execute("PRAGMA table_info(users)")
        columns = {col['name'] for col in cursor.fetchall()}
        
        # Core fields
        if 'picture_url' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN picture_url TEXT")
        if 'company_description' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN company_description TEXT")
            
        # Premium related fields
        if 'is_premium' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
        if 'premium_until' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN premium_until TEXT")
        if 'skills' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN skills TEXT")
        if 'experience_years' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN experience_years INTEGER")
        if 'preferred_trades' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN preferred_trades TEXT")
        if 'hourly_rate' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN hourly_rate REAL")
        if 'availability' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN availability TEXT")
            
        # Background check fields
        if 'background_check_status' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN background_check_status TEXT")
        if 'background_check_date' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN background_check_date TEXT")
            
        # Rating and activity fields
        if 'rating' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN rating REAL DEFAULT 0")
        if 'reviews_count' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN reviews_count INTEGER DEFAULT 0")
        if 'last_active' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_active TEXT")
        
        conn.commit()
        print("Added all fields successfully")
        
    except Exception as e:
        print(f"Error adding fields: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def run_migrations():
    """Run all database migrations"""
    print("Starting database migrations...")
    
    try:
        # Drop all existing tables
        print("\nDropping existing tables...")
        drop_all_tables()
        
        # Initialize database schema
        print("\nInitializing database schema...")
        init_db()
        
        # Add premium fields
        print("\nAdding premium fields...")
        add_premium_fields()
        
        # Update user locations
        print("\nUpdating user locations...")
        migrate_user_locations()
        
        print("\nAll migrations completed successfully!")
        
    except Exception as e:
        print(f"\nError during migrations: {e}")
        raise

if __name__ == "__main__":
    load_dotenv()
    run_migrations() 