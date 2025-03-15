import streamlit as st
from utils.database import get_db
from datetime import datetime

def show_admin_reviews():
    """Show reviews management interface for admin"""
    st.title("Reviews Management")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get all reviews with user details
        cursor.execute("""
            SELECT r.*,
                   reviewer.name as reviewer_name,
                   reviewer.role as reviewer_role,
                   reviewed.name as reviewed_name,
                   reviewed.role as reviewed_role
            FROM reviews r
            JOIN users reviewer ON r.reviewer_id = reviewer.user_id
            JOIN users reviewed ON r.reviewed_id = reviewed.user_id
            ORDER BY r.created_at DESC
        """)
        
        reviews = cursor.fetchall()
        
        if not reviews:
            st.info("No reviews in the system yet")
            return
            
        # Display reviews with filtering options
        st.subheader("All Reviews")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            role_filter = st.selectbox(
                "Filter by Role",
                options=["All", "Job Seeker", "Job Poster"],
                key="role_filter"
            )
        with col2:
            rating_filter = st.selectbox(
                "Filter by Rating",
                options=["All"] + list(range(1, 6)),
                key="rating_filter"
            )
            
        # Filter and display reviews
        filtered_reviews = reviews
        if role_filter != "All":
            filtered_reviews = [r for r in reviews if r['reviewer_role'] == role_filter or r['reviewed_role'] == role_filter]
        if rating_filter != "All":
            filtered_reviews = [r for r in filtered_reviews if r['rating'] == rating_filter]
            
        for review in filtered_reviews:
            with st.expander(f"Review: {review['reviewer_name']} → {review['reviewed_name']}", expanded=False):
                st.markdown(f"""
                    **From:** {review['reviewer_name']} ({review['reviewer_role']})  
                    **To:** {review['reviewed_name']} ({review['reviewed_role']})  
                    **Rating:** {"⭐" * review['rating']}  
                    **Comment:**  
                    > {review['comment']}
                    
                    *Posted on: {review['created_at'][:16]}*
                    
                    ---
                """)
                
                # Add option to delete inappropriate reviews
                if st.button("Delete Review", key=f"delete_{review['review_id']}"):
                    try:
                        # Delete the review
                        cursor.execute("DELETE FROM reviews WHERE review_id = ?", (review['review_id'],))
                        
                        # Update user's average rating
                        cursor.execute("""
                            UPDATE users 
                            SET avg_rating = (
                                SELECT AVG(rating) 
                                FROM reviews 
                                WHERE reviewed_id = ?
                            )
                            WHERE user_id = ?
                        """, (review['reviewed_id'], review['reviewed_id']))
                        
                        conn.commit()
                        st.success("Review deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting review: {str(e)}")
        
        # Add summary statistics
        st.subheader("Review Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cursor.execute("SELECT COUNT(*) as count FROM reviews")
            total_reviews = cursor.fetchone()['count']
            st.metric("Total Reviews", total_reviews)
            
        with col2:
            cursor.execute("SELECT AVG(rating) as avg FROM reviews")
            avg_rating = cursor.fetchone()['avg']
            st.metric("Average Rating", f"{avg_rating:.1f}" if avg_rating else "N/A")
            
        with col3:
            cursor.execute("""
                SELECT COUNT(DISTINCT reviewed_id) as count 
                FROM reviews
            """)
            reviewed_users = cursor.fetchone()['count']
            st.metric("Users Reviewed", reviewed_users)
            
    except Exception as e:
        st.error(f"Error loading reviews: {str(e)}")
    finally:
        conn.close()

def show_reviews():
    """Show user reviews"""
    st.title("Reviews")
    
    user = st.session_state.get('user')
    if not user:
        st.error("Please log in to view reviews")
        return
        
    conn = get_db()
    cursor = conn.cursor()
    
    # First, check if the reviews table exists and has the right structure
    try:
        cursor.execute("PRAGMA table_info(reviews)")
        columns = {col['name'] for col in cursor.fetchall()}
        
        required_columns = {'review_id', 'reviewer_id', 'reviewed_id', 'rating', 'comment'}
        missing_columns = required_columns - columns
        
        if missing_columns:
            st.error(f"Reviews system needs database update. Missing columns: {missing_columns}")
            
            # Create reviews table if it doesn't exist properly
            if st.button("Initialize Reviews Table"):
                try:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS reviews (
                            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            reviewer_id INTEGER NOT NULL,
                            reviewed_id INTEGER NOT NULL,
                            rating INTEGER NOT NULL,
                            comment TEXT,
                            created_at TEXT NOT NULL,
                            FOREIGN KEY (reviewer_id) REFERENCES users (user_id),
                            FOREIGN KEY (reviewed_id) REFERENCES users (user_id)
                        )
                    """)
                    conn.commit()
                    st.success("Reviews table created successfully! Please refresh the page.")
                    return
                except Exception as e:
                    st.error(f"Error creating reviews table: {str(e)}")
                    return
            return
            
    except Exception as e:
        st.error(f"Error checking reviews table: {str(e)}")
        return
    
    try:
        # Get reviews received
        cursor.execute("""
            SELECT r.*, u.name as reviewer_name, u.role as reviewer_role
            FROM reviews r
            JOIN users u ON r.reviewer_id = u.user_id
            WHERE r.reviewed_id = ?
            ORDER BY r.created_at DESC
        """, (user['user_id'],))
        
        reviews_received = cursor.fetchall()
        
        # Get reviews given
        cursor.execute("""
            SELECT r.*, u.name as reviewed_name, u.role as reviewed_role
            FROM reviews r
            JOIN users u ON r.reviewed_id = u.user_id
            WHERE r.reviewer_id = ?
            ORDER BY r.created_at DESC
        """, (user['user_id'],))
        
        reviews_given = cursor.fetchall()
        
        # Display reviews received
        st.header("Reviews Received")
        if not reviews_received:
            st.info("No reviews received yet")
        else:
            for review in reviews_received:
                with st.container():
                    st.markdown(f"""
                        ⭐ **{review['rating']}/5** from {review['reviewer_name']} ({review['reviewer_role']})
                        > {review['comment']}
                        
                        *{review['created_at'][:16]}*
                        ---
                    """)
        
        # Display reviews given
        st.header("Reviews Given")
        if not reviews_given:
            st.info("No reviews given yet")
        else:
            for review in reviews_given:
                with st.container():
                    st.markdown(f"""
                        ⭐ **{review['rating']}/5** for {review['reviewed_name']} ({review['reviewed_role']})
                        > {review['comment']}
                        
                        *{review['created_at'][:16]}*
                        ---
                    """)
        
        # Check application table structure for the query
        cursor.execute("PRAGMA table_info(applications)")
        app_columns = {col['name'] for col in cursor.fetchall()}
        
        # Determine field names based on schema
        job_poster_field = 'job_poster_id' if 'job_poster_id' in app_columns else 'poster_id'
        applicant_field = 'applicant_id' if 'applicant_id' in app_columns else 'user_id'
            
        # Add new review
        st.header("Add Review")
        
        # Get users who can be reviewed - dynamically build query based on schema
        query = f"""
            SELECT DISTINCT u.user_id, u.name, u.role
            FROM users u
            JOIN applications a ON 
                (a.{job_poster_field} = ? AND a.{applicant_field} = u.user_id) OR
                (a.{applicant_field} = ? AND a.{job_poster_field} = u.user_id)
            LEFT JOIN reviews r ON 
                r.reviewer_id = ? AND r.reviewed_id = u.user_id
            WHERE r.review_id IS NULL
            AND u.user_id != ?
        """
        
        try:
            cursor.execute(query, (user['user_id'], user['user_id'], user['user_id'], user['user_id']))
            users_to_review = cursor.fetchall()
        except Exception as e:
            st.error(f"Error finding users to review: {str(e)}")
            users_to_review = []
        
        if users_to_review:
            # Use a form to prevent session state issues
            with st.form("add_review_form", clear_on_submit=True):
                st.subheader("Write a Review")
                
                selected_user = st.selectbox(
                    "Select user to review",
                    options=[(u['user_id'], f"{u['name']} ({u['role']})") for u in users_to_review],
                    format_func=lambda x: x[1]
                )
                
                rating = st.slider("Rating", 1, 5, 5)
                comment = st.text_area("Comment", placeholder="Write your review here...")
                
                submitted = st.form_submit_button("Submit Review")
                
                if submitted:
                    if selected_user and comment:
                        try:
                            cursor.execute("""
                                INSERT INTO reviews (
                                    reviewer_id, reviewed_id, rating,
                                    comment, created_at
                                ) VALUES (?, ?, ?, ?, ?)
                            """, (
                                user['user_id'],
                                selected_user[0],
                                rating,
                                comment.strip(),
                                datetime.now().isoformat()
                            ))
                            
                            # Update user's average rating if avg_rating column exists
                            try:
                                cursor.execute("PRAGMA table_info(users)")
                                user_columns = {col['name'] for col in cursor.fetchall()}
                                
                                if 'avg_rating' in user_columns:
                                    cursor.execute("""
                                        UPDATE users 
                                        SET avg_rating = (
                                            SELECT AVG(rating) 
                                            FROM reviews 
                                            WHERE reviewed_id = ?
                                        )
                                        WHERE user_id = ?
                                    """, (selected_user[0], selected_user[0]))
                            except Exception as e:
                                if st.checkbox("Show debug info", value=False):
                                    st.error(f"Could not update avg_rating: {str(e)}")
                            
                            conn.commit()
                            st.success("Review submitted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error submitting review: {str(e)}")
                    else:
                        st.error("Please select a user and provide a comment")
        else:
            st.info("No users available to review. Complete a job with someone to be able to review them.")
            
    except Exception as e:
        st.error(f"Error loading reviews: {str(e)}")
    finally:
        conn.close() 