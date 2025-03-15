import streamlit as st
from utils.database import get_db, update_user_profile
from datetime import datetime
from utils.location_utils import update_user_location
import requests
import folium
from streamlit_folium import folium_static

def update_profile(user_id, data):
    """Update user profile information"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Update user information
        cursor.execute("""
            UPDATE users 
            SET name = ?,
                bio = ?,
                location = ?,
                company_name = ?,
                company_description = ?,
                website = ?,
                phone = ?,
                skills = ?,
                experience_years = ?,
                postal_code = ?,
                updated_at = ?
            WHERE user_id = ?
        """, (
            data.get('name'),
            data.get('bio'),
            data.get('location'),
            data.get('company_name'),
            data.get('company_description'),
            data.get('website'),
            data.get('phone'),
            data.get('skills'),
            data.get('experience_years'),
            data.get('postal_code'),
            datetime.now().isoformat(),
            user_id
        ))
        
        # Update location coordinates if provided
        if data.get('latitude') and data.get('longitude'):
            cursor.execute("""
                UPDATE users
                SET latitude = ?, longitude = ?
                WHERE user_id = ?
            """, (data.get('latitude'), data.get('longitude'), user_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        st.error(f"Error updating profile: {str(e)}")
        return False
    finally:
        conn.close()

def show_profile():
    """Show and edit user profile"""
    if 'user' not in st.session_state:
        st.error("Please log in to view your profile")
        st.session_state['page'] = 'landing'
        st.rerun()
        return
    
    user = st.session_state['user']
    st.title("My Profile")
    
    # Create tabs for different sections
    tabs = st.tabs(["📝 Basic Info", "🔧 Professional Details", "⚙️ Account Settings", "📍 Location"])
    
    with tabs[0]:
        with st.form("basic_info_form"):
            st.subheader("Basic Information")
            name = st.text_input("Name", value=user.get('name', ''))
            email = st.text_input("Email", value=user.get('email', ''), disabled=True)
            bio = st.text_area("Bio", value=user.get('bio', ''), 
                             help="Tell us about yourself")
            location = st.text_input("Location", value=user.get('location', ''))
            postal_code = st.text_input("Postal/ZIP Code", value=user.get('postal_code', ''), 
                                      help="Your postal or ZIP code for more accurate location-based services")
            
            if user['role'] == 'Job Poster':
                company_name = st.text_input("Company Name", 
                                           value=user.get('company_name', ''))
                company_description = st.text_area("Company Description", 
                                                 value=user.get('company_description', ''))
            
            submit_basic = st.form_submit_button("Save Basic Info")
            
            if submit_basic:
                try:
                    conn = get_db()
                    cursor = conn.cursor()
                    
                    update_data = {
                        'name': name,
                        'bio': bio,
                        'location': location,
                        'postal_code': postal_code,
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    if user['role'] == 'Job Poster':
                        update_data.update({
                            'company_name': company_name,
                            'company_description': company_description
                        })
                    
                    # Build the SQL query dynamically
                    fields = ', '.join([f"{k} = ?" for k in update_data.keys()])
                    sql = f"UPDATE users SET {fields} WHERE user_id = ?"
                    
                    # Execute the update
                    cursor.execute(sql, list(update_data.values()) + [user['user_id']])
                    conn.commit()
                    
                    # Update session state
                    cursor.execute("SELECT * FROM users WHERE user_id = ?", 
                                 (user['user_id'],))
                    updated_user = cursor.fetchone()
                    st.session_state['user'] = dict(updated_user)
                    
                    st.success("Profile updated successfully!")
                    
                except Exception as e:
                    st.error(f"Error updating profile: {str(e)}")
                finally:
                    conn.close()
    
    with tabs[1]:
        with st.form("professional_details_form"):
            st.subheader("Professional Details")
            
            if user['role'] == 'Job Seeker':
                skills = st.text_area("Skills", value=user.get('skills', ''),
                                    help="List your skills (comma separated)")
                certifications = st.text_area("Certifications & Licenses", 
                                            value=user.get('certifications', ''),
                                            help="List your certifications")
                
            submit_prof = st.form_submit_button("Save Professional Details")
            
            if submit_prof and user['role'] == 'Job Seeker':
                try:
                    conn = get_db()
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE users 
                        SET skills = ?, certifications = ?, updated_at = ?
                        WHERE user_id = ?
                    """, (skills, certifications, datetime.now().isoformat(), 
                         user['user_id']))
                    conn.commit()
                    
                    # Update session state
                    cursor.execute("SELECT * FROM users WHERE user_id = ?", 
                                 (user['user_id'],))
                    updated_user = cursor.fetchone()
                    st.session_state['user'] = dict(updated_user)
                    
                    st.success("Professional details updated successfully!")
                    
                except Exception as e:
                    st.error(f"Error updating professional details: {str(e)}")
                finally:
                    conn.close()
    
    with tabs[2]:
        st.subheader("Account Settings")
        
        # Delete Account
        st.error("⚠️ Danger Zone")
        with st.form("delete_account_form"):
            st.warning(
                "Deleting your account is permanent and cannot be undone. "
                "All your data will be permanently removed."
            )
            confirm_delete = st.text_input(
                "Type 'DELETE' to confirm account deletion",
                help="This action cannot be undone"
            )
            
            submit_delete = st.form_submit_button("🗑️ Delete Account")
            
            if submit_delete:
                if confirm_delete == 'DELETE':
                    try:
                        conn = get_db()
                        cursor = conn.cursor()
                        
                        # Delete user's data
                        if user['role'] == 'Job Poster':
                            # Delete job applications
                            cursor.execute("""
                                DELETE FROM applications 
                                WHERE job_id IN (
                                    SELECT job_id FROM jobs 
                                    WHERE job_poster_id = ?
                                )
                            """, (user['user_id'],))
                            
                            # Delete jobs
                            cursor.execute("""
                                DELETE FROM jobs 
                                WHERE job_poster_id = ?
                            """, (user['user_id'],))
                        
                        # Delete user's applications if they're a job seeker
                        cursor.execute("""
                            DELETE FROM applications 
                            WHERE applicant_id = ?
                        """, (user['user_id'],))
                        
                        # Delete user's messages
                        cursor.execute("""
                            DELETE FROM messages 
                            WHERE sender_id = ? OR receiver_id = ?
                        """, (user['user_id'], user['user_id']))
                        
                        # Delete user's reviews
                        cursor.execute("""
                            DELETE FROM reviews 
                            WHERE reviewer_id = ? OR reviewed_id = ?
                        """, (user['user_id'], user['user_id']))
                        
                        # Finally, delete the user
                        cursor.execute("""
                            DELETE FROM users 
                            WHERE user_id = ?
                        """, (user['user_id'],))
                        
                        conn.commit()
                        
                        # Clear session and redirect to landing
                        st.session_state.clear()
                        st.success("Account deleted successfully")
                        st.session_state['page'] = 'landing'
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error deleting account: {str(e)}")
                    finally:
                        conn.close()
                else:
                    st.error("Please type 'DELETE' to confirm account deletion")

    with tabs[3]:
        st.subheader("Location Settings")
        
        # Current location info
        current_location = user.get('location', '')
        current_postal = user.get('postal_code', '')
        current_lat = user.get('latitude')
        current_lng = user.get('longitude')
        
        # Show current location summary
        st.write("#### Current Location Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Location:** {current_location or 'Not set'}")
            st.write(f"**Postal/ZIP Code:** {current_postal or 'Not set'}")
        
        with col2:
            if current_lat and current_lng:
                st.write(f"**Coordinates:** {current_lat:.6f}, {current_lng:.6f}")
                location_status = "✅ Location coordinates set"
            else:
                st.write("**Coordinates:** Not set")
                location_status = "⚠️ Location coordinates not set"
            
            st.write(f"**Status:** {location_status}")
        
        # Show current location on map if coordinates exist
        if current_lat and current_lng:
            st.write("#### Your Location on Map")
            m = folium.Map(location=[current_lat, current_lng], zoom_start=13)
            folium.Marker(
                location=[current_lat, current_lng],
                popup=current_location,
                icon=folium.Icon(color="red", icon="home"),
            ).add_to(m)
            folium_static(m, width=700, height=300)
        else:
            st.warning("Your location doesn't have coordinates set. This will limit your ability to use distance-based search and other location features. Please update your location using one of the methods below.")
        
        # Location update options
        st.write("#### Update Your Location")
        st.info("Having accurate location information allows you to search for jobs based on distance and lets job posters find workers near them.")
        
        update_option = st.radio(
            "Choose how to update your location:",
            ["Enter Address Manually", "Use Current Browser Location", "Pick on Map"]
        )
        
        new_lat, new_lng, new_location, new_postal = None, None, current_location, current_postal
        
        if update_option == "Enter Address Manually":
            with st.form("location_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_location = st.text_input("Location (City, State)", 
                                               value=current_location,
                                               help="Enter your city and state, e.g. 'Boston, MA'")
                with col2:
                    new_postal = st.text_input("Postal/ZIP Code", 
                                             value=current_postal,
                                             help="Enter your postal or ZIP code")
                
                st.write("You can enter just the city and state, or just the postal code, or both for the most accurate results.")
                
                if st.form_submit_button("Find Location", use_container_width=True):
                    try:
                        # Show searching indicator
                        with st.spinner("Searching for location..."):
                            # Try to geocode the address
                            location_query = f"{new_location} {new_postal}"
                            response = requests.get(
                                f"https://nominatim.openstreetmap.org/search?q={location_query}&format=json&limit=1",
                                headers={"User-Agent": "Workify/1.0"}
                            )
                            
                            if response.status_code == 200:
                                results = response.json()
                                if results:
                                    new_lat = float(results[0]['lat'])
                                    new_lng = float(results[0]['lon'])
                                    
                                    # Extract detailed address information
                                    address = results[0].get('display_name', '').split(',')
                                    if len(address) >= 2:
                                        # Use the first two parts of the address for a cleaner display
                                        new_location = f"{address[0].strip()}, {address[1].strip()}"
                                    
                                    # Try to get the postal code from the result
                                    if not new_postal and 'address' in results[0]:
                                        new_postal = results[0]['address'].get('postcode', '')
                                    
                                    # Show the found location on map
                                    st.success(f"Location found: {new_location}")
                                    if new_postal:
                                        st.write(f"Postal/ZIP Code: {new_postal}")
                                    
                                    m = folium.Map(location=[new_lat, new_lng], zoom_start=13)
                                    folium.Marker(
                                        location=[new_lat, new_lng],
                                        popup=new_location,
                                        icon=folium.Icon(color="green", icon="info-sign"),
                                    ).add_to(m)
                                    folium_static(m, width=700, height=300)
                                    
                                    # Save button - now part of the form submit
                                    if st.form_submit_button("Save This Location"):
                                        update_data = {
                                            'location': new_location,
                                            'postal_code': new_postal,
                                            'latitude': new_lat,
                                            'longitude': new_lng
                                        }
                                        
                                        if update_profile(user['user_id'], {**user, **update_data}):
                                            st.success("Location updated successfully!")
                                            # Update session state
                                            st.session_state['user']['location'] = new_location
                                            st.session_state['user']['postal_code'] = new_postal
                                            st.session_state['user']['latitude'] = new_lat
                                            st.session_state['user']['longitude'] = new_lng
                                            st.rerun()
                                else:
                                    st.error("Location not found. Try a different address or add more details like city, state or country.")
                            else:
                                st.error("Error contacting location service. Please try again later.")
                    except Exception as e:
                        st.error(f"Error finding location: {str(e)}")
                        
                # Quick update without coordinates
                st.write("---")
                st.write("Or just update your location text without coordinates:")
                col1, col2 = st.columns(2)
                with col1:
                    quick_location = st.text_input("Quick Location Update", 
                                                value=current_location,
                                                help="This won't set coordinates")
                with col2:
                    quick_postal = st.text_input("Quick Postal Code Update", 
                                              value=current_postal,
                                              help="This won't set coordinates")
                
                if st.form_submit_button("Update Location Text Only", use_container_width=True):
                    # Update just the text fields
                    update_data = {
                        'location': quick_location,
                        'postal_code': quick_postal
                    }
                    
                    if update_profile(user['user_id'], {**user, **update_data}):
                        st.success("Location text updated successfully! Note: Coordinates were not set.")
                        # Update session state
                        st.session_state['user']['location'] = quick_location
                        st.session_state['user']['postal_code'] = quick_postal
                        st.rerun()

def update_profile_old(user_id, data):
    """Update user profile information"""
    try:
        cursor.execute("BEGIN TRANSACTION")
        
        # Update basic info
        cursor.execute("""
            UPDATE users 
            SET name = ?,
                bio = ?,
                location = ?,
                latitude = ?,
                longitude = ?,
                service_radius = ?
            WHERE user_id = ?
        """, (
            data['name'],
            data['bio'],
            data['location'],
            data['latitude'],
            data['longitude'],
            data['service_radius'],
            user_id
        ))
        
        # Update service categories if provider
        if data.get('services'):
            # First, remove existing services
            cursor.execute("DELETE FROM provider_services WHERE user_id = ?", (user_id,))
            
            # Add new services
            for service in data['services']:
                cursor.execute("""
                    INSERT INTO provider_services (
                        user_id, category_id, hourly_rate, description
                    ) VALUES (?, ?, ?, ?)
                """, (
                    user_id,
                    service['category_id'],
                    service['rate'],
                    service['description']
                ))
        
        cursor.execute("COMMIT")
        return True
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        st.error(f"Error updating profile: {str(e)}")
        return False

def show_profile_old():
    st.title("Profile")
    
    # Get current user data
    cursor.execute("""
        SELECT 
            u.*,
            GROUP_CONCAT(ps.category_id) as service_categories,
            GROUP_CONCAT(ps.hourly_rate) as service_rates,
            GROUP_CONCAT(ps.description) as service_descriptions
        FROM users u
        LEFT JOIN provider_services ps ON u.user_id = ps.user_id
        WHERE u.email = ?
        GROUP BY u.user_id
    """, (st.session_state.user['email'],))
    
    user_data = cursor.fetchone()
    
    # Profile Information
    st.markdown("### 👤 Profile Information")
    with st.form("profile_form"):
        name = st.text_input("Full Name", value=user_data[1])
        email = st.text_input("Email", value=user_data[2], disabled=True)
        bio = st.text_area("Bio", value=user_data[6] or "")
        
        # Location Selection
        st.markdown("### 📍 Location Settings")
        if user_data[9]:  # If location exists
            st.write(f"Current Location: {user_data[9]}")
            if st.checkbox("Update Location", key="update_location_checkbox"):
                location_data = show_location_picker(
                    default_location=(user_data[10], user_data[11])
                )
        else:
            location_data = show_location_picker()
        
        if location_data:
            st.success("Location updated!")
            
            # Show service area if provider
            if st.session_state.user['role'] == "Job Seeker":
                st.markdown("### 🎯 Service Area")
                service_map = show_service_area(location_data, location_data['radius'])
                st.components.v1.html(service_map._repr_html_(), height=400)
        
        submit = st.form_submit_button("Update Profile")
        if submit:
            update_data = {
                'name': name,
                'bio': bio,
                'location': location_data['address'] if location_data else user_data[9],
                'latitude': location_data['latitude'] if location_data else user_data[10],
                'longitude': location_data['longitude'] if location_data else user_data[11],
                'service_radius': location_data['radius'] if location_data else user_data[12]
            }
            
            if update_profile(user_data[0], update_data):
                st.success("Profile updated successfully!")
                st.rerun()
    
    # Skills and Experience (for Job Seekers)
    if st.session_state.user['role'] == "Job Seeker":
        st.markdown("### 🎯 Services Offered")
        
        # Get service categories
        cursor.execute("SELECT category_id, name, description FROM service_categories")
        categories = cursor.fetchall()
        
        with st.form("services_form"):
            # Get current services
            cursor.execute("""
                SELECT category_id, hourly_rate, description
                FROM provider_services
                WHERE user_id = ?
            """, (user_data[0],))
            current_services = {row[0]: {'rate': row[1], 'desc': row[2]} 
                              for row in cursor.fetchall()}
            
            services_data = []
            for category in categories:
                if st.checkbox(f"Offer {category[1]}", 
                             value=category[0] in current_services,
                             key=f"service_checkbox_{category[0]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        rate = st.number_input(
                            f"Hourly Rate for {category[1]} ($)",
                            value=current_services.get(category[0], {}).get('rate', 0),
                            min_value=0,
                            key=f"rate_input_{category[0]}"
                        )
                    with col2:
                        desc = st.text_area(
                            f"Description for {category[1]}",
                            value=current_services.get(category[0], {}).get('desc', ''),
                            height=100,
                            key=f"desc_input_{category[0]}"
                        )
                    services_data.append({
                        'category_id': category[0],
                        'rate': rate,
                        'description': desc
                    })
            
            submit = st.form_submit_button("Update Services")
            if submit:
                update_data = {
                    'name': name,
                    'bio': bio,
                    'location': user_data[9],
                    'latitude': user_data[10],
                    'longitude': user_data[11],
                    'service_radius': user_data[12],
                    'services': services_data
                }
                
                if update_profile(user_data[0], update_data):
                    st.success("Services updated successfully!")
                    st.rerun()
    
    # Company Information (for Job Posters)
    else:
        st.markdown("### 🏢 Company Information")
        with st.form("company_form"):
            company_name = st.text_input("Company Name", 
                                       value=user_data[1],
                                       key="company_name_input")
            company_description = st.text_area("Company Description", 
                                             value=user_data[6] or "",
                                             key="company_desc_input")
            website = st.text_input("Website", key="website_input")
            
            submit = st.form_submit_button("Update Company Info")
            if submit:
                update_data = {
                    'name': company_name,
                    'bio': company_description,
                    'location': user_data[9],
                    'latitude': user_data[10],
                    'longitude': user_data[11],
                    'service_radius': user_data[12]
                }
                
                if update_profile(user_data[0], update_data):
                    st.success("Company information updated successfully!")
                    st.rerun() 