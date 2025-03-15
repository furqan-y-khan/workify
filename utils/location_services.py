import streamlit as st
import folium
from folium import plugins
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import json
from streamlit_folium import folium_static
import requests
from typing import Tuple, Optional

# Initialize the geocoder
geocoder = Nominatim(user_agent="jobcon_app")

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """Convert address to coordinates using Nominatim"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        response = requests.get(url, headers={'User-Agent': 'JobCon/1.0'})
        data = response.json()
        
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return (lat, lon)
        return None
    except Exception as e:
        st.error(f"Error geocoding address: {str(e)}")
        return None

def reverse_geocode(lat, lon):
    """Convert coordinates to address"""
    try:
        location = geocoder.reverse((lat, lon))
        if location:
            return location.address
    except Exception as e:
        st.error(f"Error reverse geocoding: {str(e)}")
    return None

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates in kilometers"""
    return geodesic(coord1, coord2).kilometers

def create_map(center_lat=0, center_lon=0, zoom_start=13):
    """Create a Folium map centered at the specified coordinates"""
    m = folium.Map(location=[center_lat, center_lon], 
                  zoom_start=zoom_start,
                  tiles="OpenStreetMap")
    return m

def add_marker(map_obj, lat, lon, popup_text, icon_color='red'):
    """Add a marker to the map"""
    folium.Marker(
        [lat, lon],
        popup=popup_text,
        icon=folium.Icon(color=icon_color)
    ).add_to(map_obj)

def show_location_picker(default_location: str = "", height: int = 400) -> Tuple[str, Optional[Tuple[float, float]]]:
    """Show location picker with map"""
    location = st.text_input("Location", value=default_location)
    coordinates = None
    
    if location:
        coordinates = geocode_address(location)
        if coordinates:
            # Create map centered on the location
            m = folium.Map(location=coordinates, zoom_start=13)
            
            # Add marker
            folium.Marker(
                coordinates,
                popup=location,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
            
            # Display map
            folium_static(m, height=height)
        else:
            st.warning("Could not find location on map")
    
    return location, coordinates

def show_job_map(jobs: list, height: int = 600):
    """Show multiple jobs on a map"""
    if not jobs:
        return
    
    # Create map centered on the first job
    first_job = jobs[0]
    coordinates = geocode_address(first_job['location'])
    if not coordinates:
        return
    
    m = folium.Map(location=coordinates, zoom_start=11)
    
    # Add markers for all jobs
    for job in jobs:
        coords = geocode_address(job['location'])
        if coords:
            # Create popup content
            popup_html = f"""
                <b>{job['title']}</b><br>
                at {job.get('company_name', job['poster_name'])}<br>
                {job['job_type']}<br>
                {job.get('payment_type', '')}
            """
            
            # Add marker
            folium.Marker(
                coords,
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
    
    # Display map
    folium_static(m, height=height)

def show_service_area(location: str, radius_km: float = 5, height: int = 400):
    """Show service area circle on map"""
    coordinates = geocode_address(location)
    if coordinates:
        m = folium.Map(location=coordinates, zoom_start=12)
        
        # Add center marker
        folium.Marker(
            coordinates,
            popup=location,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Add circle for service area
        folium.Circle(
            coordinates,
            radius=radius_km * 1000,  # Convert km to meters
            color='blue',
            fill=True,
            popup=f'{radius_km}km radius'
        ).add_to(m)
        
        # Display map
        folium_static(m, height=height)

def find_nearby_providers(job_location, radius_km=20):
    """Find service providers within a specified radius of a job location"""
    # This function would typically query the database
    # Returns a list of providers within the specified radius
    pass 