import requests
import os
from math import radians, sin, cos, sqrt, atan2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def geocode_address(address):
    """Convert address to coordinates using OpenStreetMap Nominatim API"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        headers = {
            'User-Agent': 'Workify/1.0',
            'From': os.getenv('OPENSTREETMAP_EMAIL', '')
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
        return None
    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return round(distance, 2)

def get_location_details(address):
    """Get full location details including coordinates and formatted address"""
    location = geocode_address(address)
    if location:
        return {
            'latitude': location['lat'],
            'longitude': location['lon'],
            'formatted_address': location['display_name']
        }
    return None

def format_distance(distance_km):
    """Format distance in a human-readable way"""
    if distance_km < 1:
        return f"{int(distance_km * 1000)}m"
    elif distance_km < 10:
        return f"{distance_km:.1f}km"
    else:
        return f"{int(distance_km)}km" 