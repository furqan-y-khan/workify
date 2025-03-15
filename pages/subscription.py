import streamlit as st
from utils.stripe_manager import create_checkout_session
from utils.database import get_db
from datetime import datetime

def show_subscription():
    """Show subscription options and handle upgrades"""
    st.title("Upgrade to Pro")
    
    if 'user' not in st.session_state:
        st.error("Please log in to view subscription options")
        return
    
    user_role = st.session_state['user']['role']
    
    # Get current subscription status
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT plan_id, status, valid_until 
        FROM subscriptions 
        WHERE user_id = ? AND status = 'active'
        ORDER BY created_at DESC LIMIT 1
    """, (st.session_state['user']['user_id'],))
    subscription = cursor.fetchone()
    conn.close()
    
    if subscription:
        st.success(f"You are currently on the Pro plan until {subscription['valid_until'][:10]}")
        return
    
    # Add custom CSS for better styling
    st.markdown("""
        <style>
            .plan-card {
                background: white;
                border-radius: 8px;
                padding: 2rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            .plan-card h3 {
                color: #1a73e8;
                margin-bottom: 1rem;
            }
            .plan-card ul {
                list-style-type: none;
                padding: 0;
                margin-bottom: 2rem;
            }
            .plan-card li {
                margin: 0.5rem 0;
                padding-left: 1.5rem;
                position: relative;
            }
            .plan-card li:before {
                content: "✓";
                position: absolute;
                left: 0;
                color: #34A853;
            }
            .price {
                font-size: 2rem;
                color: #1a73e8;
                margin: 1rem 0;
            }
            .upgrade-btn {
                background-color: #1a73e8;
                color: white;
                padding: 0.8rem 2rem;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                width: 100%;
                margin-top: auto;
            }
            .upgrade-btn:hover {
                background-color: #1557b0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.write("### Choose the plan that's right for you")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="plan-card">
                <h3>Free Plan</h3>
                <ul>
        """, unsafe_allow_html=True)
        
        if user_role == "Job Seeker":
            st.markdown("""
                <li>1 job application per month</li>
                <li>Basic profile</li>
                <li>Basic search functionality</li>
                <li>Email notifications</li>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <li>1 job posting per month</li>
                <li>Basic company profile</li>
                <li>Standard listing visibility</li>
                <li>Basic applicant management</li>
            """, unsafe_allow_html=True)
        
        st.markdown("""
                </ul>
                <div class="price">$0/month</div>
                <p>Current Plan</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="plan-card">
                <h3>Pro Plan</h3>
                <ul>
        """, unsafe_allow_html=True)
        
        if user_role == "Job Seeker":
            st.markdown("""
                <li>Unlimited job applications</li>
                <li>Priority application visibility</li>
                <li>Advanced profile features</li>
                <li>Advanced search filters</li>
                <li>Early access to new jobs</li>
                <li>Priority support</li>
            """, unsafe_allow_html=True)
            price = "$9.99"
            plan_id = "job_seeker_pro"
        else:
            st.markdown("""
                <li>Unlimited job postings</li>
                <li>Featured job listings</li>
                <li>Advanced candidate filtering</li>
                <li>Detailed analytics dashboard</li>
                <li>Priority support</li>
                <li>Custom company page</li>
            """, unsafe_allow_html=True)
            price = "$29.99"
            plan_id = "job_poster_pro"
        
        st.markdown(f"""
                </ul>
                <div class="price">{price}/month</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Upgrade to Pro", key="upgrade_btn"):
            checkout_session = create_checkout_session(
                st.session_state['user']['user_id'],
                plan_id
            )
            if checkout_session:
                st.success("Successfully upgraded to Pro plan!")
                st.rerun()
    
    # Add FAQ section
    st.markdown("---")
    st.markdown("### Frequently Asked Questions")
    
    with st.expander("What's included in the Pro plan?"):
        st.write("""
            The Pro plan includes all features of the Free plan plus:
            - Priority visibility in search results
            - Advanced features specific to your role
            - Premium support
            - No monthly limits
        """)
    
    with st.expander("Can I cancel anytime?"):
        st.write("""
            Yes! You can cancel your Pro subscription at any time. 
            Your benefits will continue until the end of your billing period.
        """)
    
    with st.expander("How do I get support?"):
        st.write("""
            Pro plan members get priority support through:
            - Direct email support
            - Priority response times
            - Dedicated support channel
        """) 