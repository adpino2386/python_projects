"""
Baseball Analytics MVP - Streamlit Web App
Main entry point for the application
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
app_dir = Path(__file__).parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.pages import home, dashboard, predictions, comparisons, standings, payment
from app.utils.app_helpers import init_session_state, check_authentication

# Page configuration
st.set_page_config(
    page_title="Baseball Analytics MVP",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .premium-badge {
        background-color: #ffd700;
        color: #000;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
        font-size: 0.75rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Sidebar navigation
with st.sidebar:
    st.markdown("### ⚾ Baseball Analytics")
    
    # User authentication status
    if st.session_state.get('authenticated'):
        st.success(f"✅ Premium Member")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    else:
        st.info("👤 Free Tier")
        if st.button("🔓 Login / Upgrade"):
            st.session_state.show_payment = True
    
    st.markdown("---")
    
    # Navigation
    pages = {
        "🏠 Home": "home",
        "📊 Dashboard": "dashboard",
        "🎯 Predictions": "predictions",
        "⚔️ Comparisons": "comparisons",
        "📈 Standings": "standings",
    }
    
    selected = st.radio("Navigate", list(pages.keys()))
    
    # Show payment page if needed, otherwise use selected navigation
    if st.session_state.get('show_payment', False):
        st.session_state.selected_page = "payment"
    else:
        st.session_state.selected_page = pages.get(selected, "home")
        # Reset show_payment if user navigates away
        if st.session_state.selected_page != "payment":
            st.session_state.show_payment = False

# Route to selected page
page_name = st.session_state.get('selected_page', 'home')

if page_name == "home":
    home.show()
elif page_name == "dashboard":
    dashboard.show()
elif page_name == "predictions":
    if check_authentication():
        predictions.show()
    else:
        payment.show_premium_gate()
elif page_name == "comparisons":
    if check_authentication():
        comparisons.show()
    else:
        payment.show_premium_gate()
elif page_name == "standings":
    standings.show()
elif page_name == "payment":
    payment.show()
else:
    # Default to home if page not found
    home.show()

