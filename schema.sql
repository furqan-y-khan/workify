-- Update users table with additional fields
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    company_name TEXT,
    location TEXT,
    latitude REAL,
    longitude REAL,
    is_premium INTEGER DEFAULT 0,
    premium_until TEXT,
    preferred_trades TEXT,
    skills TEXT,
    experience_years INTEGER,
    background_check_status TEXT,
    background_check_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    last_active TEXT
);

-- Add job alerts table
CREATE TABLE IF NOT EXISTS job_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    trade_categories TEXT,
    keywords TEXT,
    max_distance INTEGER,
    min_pay REAL,
    job_types TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Add work history table
CREATE TABLE IF NOT EXISTS work_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_name TEXT NOT NULL,
    position TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    description TEXT,
    trade_category TEXT,
    is_verified INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Add certifications table
CREATE TABLE IF NOT EXISTS certifications (
    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    issuing_authority TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    expiry_date TEXT,
    certificate_number TEXT,
    verification_url TEXT,
    is_verified INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Add background checks table
CREATE TABLE IF NOT EXISTS background_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    provider TEXT NOT NULL,
    report_url TEXT,
    valid_until TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Add analytics table
CREATE TABLE IF NOT EXISTS user_analytics (
    analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Add notifications table
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Update messages table
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (receiver_id) REFERENCES users(user_id)
);

-- Update applications table
CREATE TABLE IF NOT EXISTS applications (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    applicant_id INTEGER NOT NULL,
    job_poster_id INTEGER NOT NULL,
    status TEXT DEFAULT 'Pending',
    cover_letter TEXT,
    tools_equipment TEXT,
    licenses_certs TEXT,
    is_read INTEGER DEFAULT 0,
    response_time INTEGER,  -- Time to first response in minutes
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id),
    FOREIGN KEY (applicant_id) REFERENCES users(user_id),
    FOREIGN KEY (job_poster_id) REFERENCES users(user_id)
);

-- Update jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_poster_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    job_type TEXT NOT NULL,
    trade_category TEXT NOT NULL,
    payment_type TEXT,
    payment_amount REAL,
    urgency TEXT,
    start_date TEXT,
    requirements TEXT,
    tools_needed TEXT,
    workers_needed INTEGER DEFAULT 1,
    status TEXT DEFAULT 'Open',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (job_poster_id) REFERENCES users(user_id)
);

-- Add reviews table
CREATE TABLE IF NOT EXISTS reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reviewer_id INTEGER NOT NULL,
    reviewed_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id),
    FOREIGN KEY (reviewed_id) REFERENCES users(user_id),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
); 