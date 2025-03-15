import streamlit as st
from datetime import datetime, timedelta
from utils.database import get_db

def create_checkout_session(user_id, plan_id):
    """Create a simulated checkout session for testing"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Check if user already has an active subscription
            cursor.execute("""
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND status = 'active'
                AND valid_until > ?
            """, (user_id, datetime.now().isoformat()))
            
            existing_sub = cursor.fetchone()
            if existing_sub:
                st.warning("You already have an active subscription")
                return None
            
            # Calculate valid_until date (30 days from now)
            valid_until = (datetime.now() + timedelta(days=30)).isoformat()
            now = datetime.now().isoformat()
            
            # Create new subscription
            cursor.execute("""
                INSERT INTO subscriptions (
                    user_id, plan_id, status, 
                    created_at, updated_at, valid_until
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                plan_id,
                'active',
                now,
                now,
                valid_until
            ))
            
            conn.commit()
            return {"url": "?page=subscription&status=success"}
            
        except Exception as e:
            conn.rollback()
            st.error(f"Error creating subscription: {str(e)}")
            return None
            
        finally:
            conn.close()
            
    except Exception as e:
        st.error(f"Error in checkout process: {str(e)}")
        return None

def handle_webhook(payload, sig_header):
    """Handle Stripe webhooks"""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, st.secrets["stripe"]["webhook_secret"]
        )
        
        if event.type == 'checkout.session.completed':
            session = event.data.object
            user_id = session.metadata.get('user_id')
            plan = session.metadata.get('plan')
            subscription_id = session.subscription
            
            # Update user's subscription in database
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO subscriptions (
                        user_id, plan_id, stripe_subscription_id, 
                        status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id, plan, subscription_id, 'active',
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
            finally:
                conn.close()
                
        elif event.type == 'customer.subscription.updated':
            subscription = event.data.object
            # Update subscription status in database
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE subscriptions 
                    SET status = ?, updated_at = ?
                    WHERE stripe_subscription_id = ?
                """, (
                    subscription.status,
                    datetime.now().isoformat(),
                    subscription.id
                ))
                conn.commit()
            finally:
                conn.close()
                
    except Exception as e:
        st.error(f"Error handling webhook: {str(e)}")
        return False
    return True

def show_pricing_page():
    """Show pricing plans"""
    st.title("Subscription Plans")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Basic Plan")
        st.write("Perfect for small businesses")
        st.write(f"${StripeManager.PLANS['basic']['price']}/month")
        for feature in StripeManager.PLANS['basic']['features']:
            st.write(f"✓ {feature}")
        if st.button("Select Basic Plan"):
            if 'user' not in st.session_state:
                st.warning("Please log in first")
            checkout_url = create_checkout_session(
                st.session_state['user']['user_id'], 'basic'
            )
            if checkout_url:
                st.markdown(f"[Proceed to Checkout]({checkout_url})")
    
    with col2:
        st.subheader("Professional Plan")
        st.write("For growing businesses")
        st.write(f"${StripeManager.PLANS['pro']['price']}/month")
        for feature in StripeManager.PLANS['pro']['features']:
            st.write(f"✓ {feature}")
        if st.button("Select Pro Plan"):
            if 'user' not in st.session_state:
                st.warning("Please log in first")
            checkout_url = create_checkout_session(
                st.session_state['user']['user_id'], 'pro'
            )
            if checkout_url:
                st.markdown(f"[Proceed to Checkout]({checkout_url})")

def show_admin_subscription_management():
    """Show subscription management interface for admin"""
    st.title("Subscription Management")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT s.*, u.name, u.email, u.role
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            ORDER BY s.created_at DESC
        """)
        subscriptions = cursor.fetchall()
        
        if subscriptions:
            for sub in subscriptions:
                with st.expander(f"{sub['name']} - {sub['plan_id']} Plan"):
                    st.write(f"Email: {sub['email']}")
                    st.write(f"Status: {sub['status']}")
                    st.write(f"Created: {sub['created_at'][:10]}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Cancel Subscription", 
                                   key=f"cancel_{sub['stripe_subscription_id']}"):
                            try:
                                stripe.Subscription.delete(
                                    sub['stripe_subscription_id']
                                )
                                cursor.execute("""
                                    UPDATE subscriptions 
                                    SET status = 'cancelled', 
                                        updated_at = ?
                                    WHERE stripe_subscription_id = ?
                                """, (
                                    datetime.now().isoformat(),
                                    sub['stripe_subscription_id']
                                ))
                                conn.commit()
                                st.success("Subscription cancelled successfully")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error cancelling subscription: {str(e)}")
        else:
            st.info("No subscriptions found")
            
    finally:
        conn.close() 