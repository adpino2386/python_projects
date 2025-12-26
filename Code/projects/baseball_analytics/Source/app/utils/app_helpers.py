"""
Helper functions for the Streamlit app
"""

import streamlit as st
from sqlalchemy.engine import Engine
import sys
from pathlib import Path
import os

# Add source directory to path
app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from utils.connection_engine import create_connection_postgresql
from dotenv import load_dotenv

# Load environment variables
env_path = source_dir / "utils" / ".env"
load_dotenv(dotenv_path=str(env_path))


def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'show_payment' not in st.session_state:
        st.session_state.show_payment = False
    if 'db_engine' not in st.session_state:
        st.session_state.db_engine = None


def get_db_engine() -> Engine:
    """Get or create database engine"""
    if st.session_state.db_engine is None:
        try:
            st.session_state.db_engine = create_connection_postgresql()
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None
    return st.session_state.db_engine


@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_db_query(query: str, params: dict = None):
    """Cache database queries"""
    engine = get_db_engine()
    if engine is None:
        return None
    
    import pandas as pd
    from sqlalchemy import text
    
    try:
        if params:
            df = pd.read_sql(text(query), engine, params=params)
        else:
            df = pd.read_sql(text(query), engine)
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return None


def check_authentication() -> bool:
    """Check if user is authenticated (paid member)"""
    return st.session_state.get('authenticated', False)


def require_authentication():
    """Decorator to require authentication"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authentication():
                st.session_state.show_payment = True
                st.rerun()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def format_percentage(value: float) -> str:
    """Format a float as percentage"""
    return f"{value:.1f}%"


def format_decimal(value: float, decimals: int = 2) -> str:
    """Format a float with specified decimals"""
    return f"{value:.{decimals}f}"

