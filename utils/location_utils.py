import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on the Earth's surface
    using the Haversine formula
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Earth radius in kilometers
    earth_radius = 6371.0
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = earth_radius * c
    
    return distance

def update_user_location(user_id, latitude, longitude, location_name, postal_code=None):
    """
    Update a user's location information in the database
    
    Args:
        user_id: ID of the user
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        location_name: Human-readable location name (city, state, etc.)
        postal_code: Optional postal/zip code
        
    Returns:
        True if update was successful, False otherwise
    """
    from utils.database import get_db
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if postal_code:
            cursor.execute("""
                UPDATE users
                SET latitude = ?, longitude = ?, location = ?, postal_code = ?, updated_at = datetime('now')
                WHERE user_id = ?
            """, (latitude, longitude, location_name, postal_code, user_id))
        else:
            cursor.execute("""
                UPDATE users
                SET latitude = ?, longitude = ?, location = ?, updated_at = datetime('now')
                WHERE user_id = ?
            """, (latitude, longitude, location_name, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating user location: {str(e)}")
        return False
    finally:
        conn.close()

def get_nearby_users(db_conn, user_id, user_role, distance_km=50, zip_code=None):
    """
    Find nearby users based on a user's location and role
    
    Args:
        db_conn: Database connection
        user_id: ID of the user
        user_role: Role of the user ('Job Seeker' or 'Job Poster')
        distance_km: Maximum distance in kilometers (default: 50)
        zip_code: Optional filter by zip/postal code
        
    Returns:
        List of nearby users with opposite role
    """
    cursor = db_conn.cursor()
    
    # Get the user's location
    cursor.execute("""
        SELECT latitude, longitude, postal_code 
        FROM users 
        WHERE user_id = ?
    """, (user_id,))
    
    user_location = cursor.fetchone()
    
    # If zip_code filter is provided, use it instead of distance calculation
    if zip_code:
        # Determine the role we're looking for - we only want job seekers if we're a job poster
        target_role = 'Job Seeker'
        
        try:
            # Find users with matching zip/postal code
            cursor.execute("""
                SELECT user_id, name, email, company_name, location, latitude, longitude, 
                       picture_url, skills, preferred_trades, postal_code
                FROM users
                WHERE role = ? AND postal_code = ?
            """, (target_role, zip_code))
            
            matches = cursor.fetchall()
            
            # Add distance = 0 to indicate they're in the same zip code
            nearby_users = []
            for user in matches:
                if user['user_id'] != user_id:  # Don't include the current user
                    user_data = dict(user)
                    user_data['distance'] = 0  # Same zip code, so distance is considered 0
                    nearby_users.append(user_data)
                
            return nearby_users
            
        except Exception as e:
            # Handle case where postal_code column might not exist yet
            print(f"Error in zip code query: {str(e)}")
            return []
    
    # If user doesn't have location data, return empty list
    if not user_location or not user_location['latitude'] or not user_location['longitude']:
        return []
    
    user_lat = user_location['latitude']
    user_lon = user_location['longitude']
    
    # Determine the role we're looking for - we only want job seekers if we're a job poster
    target_role = 'Job Seeker'
    
    # Find users with the opposite role
    cursor.execute("""
        SELECT user_id, name, email, company_name, location, latitude, longitude, 
               picture_url, skills, preferred_trades
        FROM users
        WHERE role = ? AND latitude IS NOT NULL AND longitude IS NOT NULL
    """, (target_role,))
    
    potential_matches = cursor.fetchall()
    nearby_users = []
    
    for user in potential_matches:
        if user['user_id'] != user_id and user['latitude'] and user['longitude']:  # Don't include the current user
            dist = calculate_distance(
                user_lat, user_lon, 
                user['latitude'], user['longitude']
            )
            
            if dist <= distance_km:
                user_data = dict(user)
                user_data['distance'] = round(dist, 1)
                nearby_users.append(user_data)
    
    # Sort by distance
    nearby_users.sort(key=lambda x: x['distance'])
    
    return nearby_users 