"""
Stripe payment integration helper
Note: This is a simplified version. In production, you should use Stripe's
server-side API with webhooks for secure payment processing.
"""

import streamlit as st
import stripe
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add source directory to path
app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

env_path = source_dir / "utils" / ".env"
load_dotenv(dotenv_path=str(env_path))

# Initialize Stripe (use test keys for development)
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_your_key_here')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_test_your_key_here')

# For MVP, we'll use a simplified approach
# In production, implement proper Stripe Checkout or Payment Links


def create_checkout_session(email: str, price_id: str = "price_premium_monthly"):
    """
    Create a Stripe checkout session
    In production, this should be done server-side
    """
    try:
        stripe.api_key = STRIPE_SECRET_KEY
        
        checkout_session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=st.get_option('server.baseUrlPath') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=st.get_option('server.baseUrlPath') + '?canceled=true',
        )
        
        return checkout_session.url
    except Exception as e:
        st.error(f"Payment error: {e}")
        return None


def verify_payment(session_id: str) -> bool:
    """
    Verify a payment session
    In production, use webhooks for secure verification
    """
    try:
        stripe.api_key = STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            return True
        return False
    except Exception as e:
        st.error(f"Verification error: {e}")
        return False


def get_premium_price() -> str:
    """Get the premium subscription price"""
    # This should come from your Stripe dashboard
    return "$9.99/month"

