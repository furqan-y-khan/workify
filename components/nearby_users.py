import streamlit as st
from utils.database import get_db
from utils.location_utils import get_nearby_users, update_user_location
from streamlit_folium import folium_static
import folium
import requests

def show_nearby_users(user_id, user_role, max_distance=50, premium_only=False, section_id="default"):
    """
    Display nearby users based on the current user's role.
    
    Args:
        user_id: Current user's ID
        user_role: Current user's role ('Job Seeker' or 'Job Poster')
        max_distance: Maximum distance in kilometers
        premium_only: If False, show for all users (default is False)
        section_id: Unique identifier for the section where this component is used
    """
    # Only job posters can see nearby job seekers
    if user_role != 'Job Poster':
        return
        
    conn = get_db()
    
    try:
        # Get user location information and check premium status
        cursor = conn.cursor()
        cursor.execute("""
            SELECT location, latitude, longitude, is_premium
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        user_info = cursor.fetchone()
        
        # Check if user is premium, but only if premium_only is True
        is_premium = False
        if user_info and 'is_premium' in user_info:
            is_premium = bool(user_info['is_premium'])
        
        # Display heading for job poster
        st.subheader("👥 Nearby Job Seekers")
        
        # If premium-only feature and user is not premium, show upgrade message
        # But only check if premium_only parameter is True and user is not already premium
        if premium_only and not is_premium:
            st.info("👑 Upgrade to Pro to see users near you!")
            
            # Check if user is already on subscription page to avoid duplicating the upgrade button
            if st.session_state.get('page') != 'subscription':
                if st.button("Upgrade to Pro", key=f"upgrade_nearby_{user_role}_{user_id}_{section_id}"):
                    st.session_state['page'] = 'subscription'
                    st.rerun()
            return
        
        # Create tabs for different search methods
        tab1, tab2, tab3 = st.tabs(["Search by Distance", "Search by Postal Code", "Map View"])
        
        with tab1:
            # Allow user to set max distance
            col1, col2 = st.columns([3, 1])
            with col1:
                new_distance = st.slider(
                    "Maximum Distance (km)", 
                    min_value=5, 
                    max_value=100, 
                    value=max_distance,
                    step=5,
                    key=f"nearby_distance_slider_{user_role}_{user_id}_{section_id}"
                )
            
            with col2:
                if st.button("Update", key=f"update_distance_{user_role}_{user_id}_{section_id}"):
                    # Update the max_distance
                    max_distance = new_distance
            
            # Get nearby users based on distance
            nearby_users = get_nearby_users(conn, user_id, user_role, max_distance)
            
            # Display users for distance-based search
            if not nearby_users:
                st.info("No users found within the specified distance. Try increasing the distance or use postal code search.")
            else:
                _display_users(nearby_users, user_role, section_id, "distance", is_premium)
        
        with tab2:
            # Allow user to search by postal code
            col1, col2 = st.columns([3, 1])
            with col1:
                # Use empty string as default if postal_code doesn't exist
                postal_code = st.text_input(
                    "Postal Code / ZIP", 
                    value="",
                    key=f"postal_code_{user_role}_{user_id}_{section_id}"
                )
            
            with col2:
                search_button = st.button(
                    "Search", 
                    key=f"search_postal_{user_role}_{user_id}_{section_id}"
                )
            
            # Only search if button is clicked and postal code is provided
            if search_button and postal_code:
                # Get nearby users based on postal code
                nearby_users = get_nearby_users(conn, user_id, user_role, zip_code=postal_code)
                
                # Display users for postal-based search
                if not nearby_users:
                    st.info(f"No users found with postal code {postal_code}.")
                else:
                    _display_users(nearby_users, user_role, section_id, "postal", is_premium)
        
        with tab3:
            # Map View
            if not user_info or not user_info['latitude'] or not user_info['longitude']:
                # User has no location, provide option to get current location
                st.warning("Your location is not set. Please update your profile with location information to use the map view.")
                
                # Option to get current location
                if st.button("Get My Current Location", key=f"get_location_{section_id}"):
                    try:
                        # Use IP-based geolocation
                        response = requests.get('https://ipinfo.io/json')
                        if response.status_code == 200:
                            data = response.json()
                            if 'loc' in data:
                                lat, lng = map(float, data['loc'].split(','))
                                # Update user's location
                                city = data.get('city', '')
                                region = data.get('region', '')
                                postal = data.get('postal', '')
                                location_string = f"{city}, {region}"
                                
                                update_user_location(user_id, lat, lng, location_string, postal)
                                st.success("Location updated! Refreshing the page...")
                                st.rerun()
                            else:
                                st.error("Couldn't determine your location. Please enter it manually in your profile.")
                        else:
                            st.error("Failed to retrieve location information.")
                    except Exception as e:
                        st.error(f"Error getting location: {str(e)}")
            else:
                # Create a map centered on user's location
                user_location = (user_info['latitude'], user_info['longitude'])
                m = folium.Map(location=user_location, zoom_start=11)
                
                # Add marker for current user
                folium.Marker(
                    location=user_location,
                    popup="Your Location",
                    icon=folium.Icon(color="red", icon="home"),
                ).add_to(m)
                
                # Get nearby users for map view (using distance approach)
                nearby_users = get_nearby_users(conn, user_id, user_role, max_distance)
                
                # Add markers for nearby users
                for user in nearby_users:
                    if user['latitude'] and user['longitude']:
                        # Create a popup with user info
                        display_name = user['name']
                        popup_html = f"""
                        <b>{display_name}</b><br>
                        Distance: {user['distance']:.1f} km<br>
                        """
                        if user.get('skills'):
                            popup_html += f"Skills: {user['skills']}<br>"
                        
                        # Add marker to map
                        folium.Marker(
                            location=(user['latitude'], user['longitude']),
                            popup=popup_html,
                            icon=folium.Icon(color="blue", icon="info-sign"),
                        ).add_to(m)
                
                # Add circle representing search radius
                folium.Circle(
                    location=user_location,
                    radius=max_distance * 1000,  # Convert km to meters
                    color="#4A6FDC",
                    fill=True,
                    fill_opacity=0.2
                ).add_to(m)
                
                # Display the map
                st.write("### Nearby Job Seekers Map")
                folium_static(m, width=700, height=500)
                
                if not nearby_users:
                    st.info("No users found within the specified distance. Try increasing the search distance.")
                else:
                    st.write(f"Found {len(nearby_users)} nearby job seekers within {max_distance} km")
    finally:
        conn.close()

def _display_users(users, user_role, section_id, search_type, is_premium):
    """Helper function to display user cards"""
    # Create cards for each nearby user
    for idx, user in enumerate(users):
        with st.container():
            cols = st.columns([1, 3])
            
            with cols[0]:
                # Display user image or placeholder
                if user.get('picture_url'):
                    st.image(user['picture_url'], width=80)
                else:
                    st.write("👤")  # Use text emoji instead of HTML to avoid TypeError
            
            with cols[1]:
                # Display job seeker info
                st.markdown(f"**{user['name']}**")
                    
                if user.get('skills'):
                    st.markdown(f"*Skills:* {user['skills']}")
                
                # Show location and distance
                if search_type == "distance":
                    st.markdown(f"📍 {user['location']} ({user['distance']:.1f} km away)")
                else:
                    st.markdown(f"📍 {user['location']} (Same postal code)")
                
                # Add button to message user with more unique key
                msg_key = f"msg_{user_role}_{user['user_id']}_{section_id}_{idx}_{search_type}"
                
                # Message button behavior depends on premium status
                if st.button("Message", key=msg_key):
                    if is_premium:
                        st.session_state['selected_conversation'] = user['user_id']
                        st.session_state['page'] = 'messages'
                        st.rerun()
                    else:
                        st.warning("You need to upgrade to Pro to message users. Upgrade now!")
                        if st.session_state.get('page') != 'subscription':
                            st.session_state['page'] = 'subscription'
                            st.rerun()
            
            # Add a divider between users
            st.markdown("---") 