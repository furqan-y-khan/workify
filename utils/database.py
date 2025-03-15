import sqlite3
import logging
import os
from datetime import datetime
from config import ADMIN_PASSWORD_HASH
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def dict_factory(cursor, row):
    """Convert database row objects into dictionaries"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_db():
    """Get a database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workify.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    return conn

def migrate_database():
    """Perform database migrations to update the schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if postal_code column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col['name'] for col in columns]
        
        # Add postal_code column if it doesn't exist
        if 'postal_code' not in column_names:
            print("Adding postal_code column to users table")
            cursor.execute("ALTER TABLE users ADD COLUMN postal_code TEXT")
            conn.commit()
            print("Migration completed successfully")
        
        # Check if postal_code column exists in jobs table
        cursor.execute("PRAGMA table_info(jobs)")
        job_columns = cursor.fetchall()
        job_column_names = [col['name'] for col in job_columns]
        
        # Add postal_code column to jobs table if it doesn't exist
        if 'postal_code' not in job_column_names:
            print("Adding postal_code column to jobs table")
            cursor.execute("ALTER TABLE jobs ADD COLUMN postal_code TEXT")
            conn.commit()
            print("Jobs table migration completed successfully")
            
        # Check if job_latitude and job_longitude columns exist in jobs table
        if 'job_latitude' not in job_column_names:
            print("Adding job_latitude column to jobs table")
            cursor.execute("ALTER TABLE jobs ADD COLUMN job_latitude REAL")
            conn.commit()
        
        if 'job_longitude' not in job_column_names:
            print("Adding job_longitude column to jobs table")
            cursor.execute("ALTER TABLE jobs ADD COLUMN job_longitude REAL")
            conn.commit()
            print("Location coordinates columns added to jobs table")
            
        # Check if is_remote column exists in jobs table
        if 'is_remote' not in job_column_names:
            print("Adding is_remote column to jobs table")
            cursor.execute("ALTER TABLE jobs ADD COLUMN is_remote INTEGER DEFAULT 0")
            conn.commit()
            print("Remote job flag added to jobs table")
    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        conn.close()

def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        create_tables(conn)
        
        conn.commit()
        
        # Run migrations to update schema if needed
        migrate_database()
        
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
    finally:
        conn.close()

def create_tables(conn):
    """Create database tables if they don't exist"""
    cursor = conn.cursor()
    
    try:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                picture_url TEXT,
                bio TEXT,
                location TEXT,
                skills TEXT,
                certifications TEXT,
                company_name TEXT,
                company_description TEXT,
                avg_rating REAL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                postal_code TEXT,
                phone TEXT,
                website TEXT,
                experience_years INTEGER,
                rating REAL,
                rating_count INTEGER,
                service_radius INTEGER DEFAULT 50,
                is_verified INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                last_login TEXT,
                password_reset_token TEXT,
                email_verification_token TEXT,
                background_check_status TEXT
            )
        """)
        
        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_poster_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                job_type TEXT NOT NULL,
                trade_category TEXT NOT NULL,
                payment_type TEXT NOT NULL,
                payment_amount REAL,
                urgency TEXT,
                start_date TEXT,
                requirements TEXT,
                tools_needed TEXT,
                status TEXT DEFAULT 'Open',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (job_poster_id) REFERENCES users (user_id)
            )
        """)
        
        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                job_poster_id TEXT NOT NULL,
                applicant_id TEXT NOT NULL,
                cover_letter TEXT,
                tools_equipment TEXT,
                licenses_certs TEXT,
                approach TEXT,
                reference_info TEXT,
                preferred_contact TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs (job_id),
                FOREIGN KEY (job_poster_id) REFERENCES users (user_id),
                FOREIGN KEY (applicant_id) REFERENCES users (user_id)
            )
        """)
        
        # Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reviewer_id TEXT NOT NULL,
                reviewed_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (reviewer_id) REFERENCES users (user_id),
                FOREIGN KEY (reviewed_id) REFERENCES users (user_id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                content TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (sender_id) REFERENCES users (user_id),
                FOREIGN KEY (receiver_id) REFERENCES users (user_id)
            )
        """)
        
        # Subscriptions table - Updated schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                valid_until TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        conn.commit()
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logging.error(f"Error creating tables: {str(e)}")
        raise

def create_or_update_user(google_data, role):
    """Create or update a user based on Google OAuth data"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (google_data['id'],))
        user = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if user:
            # Update existing user, preserving their role unless explicitly changed
            update_role = role if role else user['role']
            cursor.execute("""
                UPDATE users 
                SET email = ?, name = ?, picture_url = ?, role = ?, updated_at = ?
                WHERE user_id = ?
            """, (
                google_data['email'],
                google_data['name'],
                google_data.get('picture', ''),
                update_role,
                now,
                google_data['id']
            ))
        else:
            # Create new user
            cursor.execute("""
                INSERT INTO users (
                    user_id, email, name, role, picture_url,
                    company_name, company_description,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                google_data['id'],
                google_data['email'],
                google_data['name'],
                role,
                google_data.get('picture', ''),
                google_data['name'] if role == 'Job Poster' else None,
                "Tell us about your company" if role == 'Job Poster' else None,
                now,
                now
            ))
        
        conn.commit()
        
        # Get the updated user data
        cursor.execute("""
            SELECT * FROM users WHERE user_id = ?
        """, (google_data['id'],))
        
        user = cursor.fetchone()
        if user:
            return dict(user)
        else:
            raise Exception("Failed to retrieve user after creation/update")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error creating/updating user: {str(e)}")
        raise
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def update_user_profile(user_id, profile_data):
    """Update user profile"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET bio = ?, location = ?, skills = ?, 
                certifications = ?, updated_at = ?
            WHERE user_id = ?
        """, (
            profile_data.get('bio', ''),
            profile_data.get('location', ''),
            profile_data.get('skills', ''),
            profile_data.get('certifications', ''),
            datetime.now().isoformat(),
            user_id
        ))
        
        conn.commit()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(cursor.fetchone())
    finally:
        conn.close()

def create_user(email, name, password, role, google_id=None):
    """Create a new user"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (email, name, password, role, google_id, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (email, name, password, role, google_id))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    """Get user by email"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def get_user_by_google_id(google_id):
    """Get user by Google ID"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (google_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def update_user_location(user_id, location, latitude, longitude, service_radius):
    """Update user's location information"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE users 
        SET location = ?, latitude = ?, longitude = ?, service_radius = ?
        WHERE user_id = ?
        """, (location, latitude, longitude, service_radius, user_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def create_job(poster_id, title, description, category_id, location, latitude, longitude, 
               budget_min, budget_max, required_experience, is_urgent=False):
    """Create a new job posting"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO jobs (
            poster_id, title, description, category_id, location, 
            latitude, longitude, budget_min, budget_max, 
            required_experience, is_urgent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            poster_id, title, description, category_id, location,
            latitude, longitude, budget_min, budget_max,
            required_experience, is_urgent
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception:
        return None
    finally:
        conn.close()

def get_nearby_jobs(latitude, longitude, radius_km, category_id=None):
    """Get jobs within specified radius"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Basic query without category filter
    query = """
    SELECT j.*, u.name as poster_name, sc.name as category_name,
           (6371 * acos(cos(radians(?)) * cos(radians(latitude)) * 
            cos(radians(longitude) - radians(?)) + 
            sin(radians(?)) * sin(radians(latitude)))) AS distance
    FROM jobs j
    JOIN users u ON j.poster_id = u.user_id
    JOIN service_categories sc ON j.category_id = sc.category_id
    WHERE j.status = 'open'
    HAVING distance <= ?
    """
    
    params = [latitude, longitude, latitude, radius_km]
    
    if category_id:
        query += " AND j.category_id = ?"
        params.append(category_id)
    
    query += " ORDER BY distance"
    
    cursor.execute(query, params)
    jobs = cursor.fetchall()
    conn.close()
    
    return [dict(job) for job in jobs] 