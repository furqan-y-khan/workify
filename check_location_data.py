import sqlite3

# Connect to the database
conn = sqlite3.connect('jobcon.db')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# Get users with different roles
cursor.execute("""
    SELECT user_id, name, role 
    FROM users 
    ORDER BY role
    LIMIT 10
""")

users = cursor.fetchall()
print(f"Found {len(users)} users")

if users:
    print("\nAdding sample location data to users...")
    
    # Sample coordinates (New York, Los Angeles, Chicago, Houston, Miami)
    locations = [
        ("New York, NY", 40.7128, -74.0060),
        ("Los Angeles, CA", 34.0522, -118.2437),
        ("Chicago, IL", 41.8781, -87.6298),
        ("Houston, TX", 29.7604, -95.3698),
        ("Miami, FL", 25.7617, -80.1918),
        ("Boston, MA", 42.3601, -71.0589),
        ("San Francisco, CA", 37.7749, -122.4194),
        ("Seattle, WA", 47.6062, -122.3321),
        ("Denver, CO", 39.7392, -104.9903),
        ("Atlanta, GA", 33.7490, -84.3880)
    ]
    
    for i, user in enumerate(users):
        loc_index = i % len(locations)
        
        cursor.execute("""
            UPDATE users
            SET location = ?, latitude = ?, longitude = ?
            WHERE user_id = ?
        """, (locations[loc_index][0], locations[loc_index][1], locations[loc_index][2], user['user_id']))
        
        print(f"Updated user {user['user_id']} ({user['name']}) with {locations[loc_index][0]} coordinates")
    
    conn.commit()
    print("Sample location data added successfully.")
else:
    print("No users found in the database.")

# Check users with location data after update
print("\nUsers with location data after update:")
cursor.execute("""
    SELECT user_id, name, role, location, latitude, longitude
    FROM users
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    LIMIT 10
""")

users = cursor.fetchall()
if users:
    for user in users:
        print(f"User ID: {user['user_id']}, Name: {user['name']}, Role: {user['role']}")
        print(f"Location: {user['location']}, Lat: {user['latitude']}, Long: {user['longitude']}")
        print("-" * 50)
else:
    print("No users with location data found after update.")

# Close the connection
conn.close() 