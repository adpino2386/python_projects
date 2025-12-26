"""
Payment/Login Page - Stripe integration
"""

import streamlit as st
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.utils.stripe_helper import get_premium_price


def show():
    st.title("🔓 Login / Upgrade to Premium")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Premium Membership Benefits")
        
        benefits = [
            "🎯 **Game Predictions** - Win probabilities and expected statistics",
            "📊 **Advanced Analytics** - Detailed matchup analysis",
            "🔥 **Daily Insights** - Best/worst matchups of the day",
            "⚔️ **Head-to-Head Comparisons** - Compare any players",
            "📈 **Trend Analysis** - Players due for hits or cooling off",
            "💎 **Historical Matchups** - Past performance data",
            "🎲 **Game Simulations** - Monte Carlo predictions",
            "✅ **Start/Sit Recommendations** - Optimize your lineups"
        ]
        
        for benefit in benefits:
            st.markdown(f"- {benefit}")
        
        st.markdown("---")
        st.markdown(f"### 💰 Premium Price: {get_premium_price()}")
    
    with col2:
        st.markdown("### Quick Start")
        
        # Login/Register form
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            col_login, col_signup = st.columns(2)
            with col_login:
                login_button = st.form_submit_button("Login", use_container_width=True)
            with col_signup:
                signup_button = st.form_submit_button("Sign Up", use_container_width=True)
        
        st.markdown("---")
        
        # For MVP: Simplified authentication
        st.markdown("### 🚀 MVP Access")
        st.info("For MVP demo purposes, click below to access premium features")
        
        if st.button("🎫 Get Premium Access (Demo)", use_container_width=True, type="primary"):
            # In production, this would verify payment via Stripe
            # For MVP demo, we'll just set authenticated = True
            st.session_state.authenticated = True
            st.session_state.user_email = email if email else "demo@baseballanalytics.com"
            st.session_state.show_payment = False
            st.success("✅ Premium access granted!")
            st.rerun()
        
        st.markdown("---")
        st.caption("🔒 Secure payment processing via Stripe")
        st.caption("Cancel anytime • No hidden fees")


def show_premium_gate():
    """Show premium gate when user tries to access premium content"""
    st.warning("🔒 This feature requires Premium membership")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background-color: #fff3cd; border-radius: 0.5rem;'>
            <h3>Unlock Premium Features</h3>
            <p>Get access to advanced predictions, analytics, and insights</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Upgrade to Premium", use_container_width=True, type="primary"):
            st.session_state.show_payment = True
            st.rerun()

