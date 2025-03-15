import sqlite3
from datetime import datetime, timedelta

# Connect to the database
conn = sqlite3.connect('jobcon.db')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# Get first user of each role
cursor.execute("""
    SELECT user_id, name, role 
    FROM users 
    GROUP BY role
    LIMIT 2
""")

users = cursor.fetchall()
print(f"Found {len(users)} users to make premium")

if users:
    # Set premium status and expiration date (3 months from now)
    premium_until = (datetime.now() + timedelta(days=90)).isoformat()
    
    for user in users:
        cursor.execute("""
            UPDATE users
            SET is_premium = 1, premium_until = ?
            WHERE user_id = ?
        """, (premium_until, user['user_id']))
        
        print(f"Updated user {user['user_id']} ({user['name']}) to premium status")
    
    conn.commit()
    print("Premium status added successfully.")
    
    # List all premium users
    print("\nPremium users:")
    cursor.execute("""
        SELECT user_id, name, role, is_premium, premium_until
        FROM users
        WHERE is_premium = 1
    """)
    
    premium_users = cursor.fetchall()
    for user in premium_users:
        print(f"User ID: {user['user_id']}, Name: {user['name']}, Role: {user['role']}")
        print(f"Premium until: {user['premium_until'][:10]}")
        print("-" * 50)
else:
    print("No users found in the database.")

# Close the connection
conn.close() 