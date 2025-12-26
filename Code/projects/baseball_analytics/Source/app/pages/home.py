"""
Home Page - Free tier content
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.utils.app_helpers import get_db_engine, cached_db_query
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go


def show():
    st.title("⚾ Baseball Analytics Dashboard")
    st.markdown("---")
    
    # Hero section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2>Advanced Baseball Analytics & Predictions</h2>
            <p style='font-size: 1.2rem; color: #666;'>
                Get actionable insights using advanced archetype analysis and matchup predictions
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Today's games preview (free)
    st.markdown("### 📅 Today's Games")
    
    engine = get_db_engine()
    if engine:
        # Get today's date
        today = date.today().strftime('%Y-%m-%d')
        
        # Try to get games (you'll need to implement this based on your data source)
        st.info("⚡ Games for today will be displayed here. Premium members get detailed matchup analysis!")
        
        # Show teaser
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Games Today", "0", "Check Premium for Details")
        with col2:
            st.metric("Top Matchups", "🔒 Premium", "Unlock Predictions")
        with col3:
            st.metric("Win Probabilities", "🔒 Premium", "Advanced Analytics")
    
    st.markdown("---")
    
    # Standings preview (free)
    st.markdown("### 📈 Current Standings Preview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("American League")
        st.info("📊 Full standings available in Standings page")
        # Placeholder table
        al_data = {
            'Team': ['Yankees', 'Orioles', 'Rays', 'Blue Jays', 'Red Sox'],
            'W': [95, 93, 90, 85, 80],
            'L': [67, 69, 72, 77, 82],
            'GB': ['-', '2.0', '5.0', '10.0', '15.0']
        }
        st.dataframe(pd.DataFrame(al_data), use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("National League")
        st.info("📊 Full standings available in Standings page")
        # Placeholder table
        nl_data = {
            'Team': ['Dodgers', 'Braves', 'Phillies', 'Mets', 'Marlins'],
            'W': [100, 98, 92, 88, 82],
            'L': [62, 64, 70, 74, 80],
            'GB': ['-', '2.0', '8.0', '12.0', '18.0']
        }
        st.dataframe(pd.DataFrame(nl_data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Premium features teaser
    st.markdown("### ⭐ Premium Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='padding: 1.5rem; background-color: #f0f2f6; border-radius: 0.5rem; border-left: 4px solid #ffd700;'>
            <h4>🎯 Game Predictions</h4>
            <ul>
                <li>Win probabilities</li>
                <li>Expected statistics</li>
                <li>Matchup analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='padding: 1.5rem; background-color: #f0f2f6; border-radius: 0.5rem; border-left: 4px solid #ffd700;'>
            <h4>📊 Advanced Analytics</h4>
            <ul>
                <li>Best/worst matchups</li>
                <li>Player comparisons</li>
                <li>Historical data</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='padding: 1.5rem; background-color: #f0f2f6; border-radius: 0.5rem; border-left: 4px solid #ffd700;'>
            <h4>🔥 Daily Insights</h4>
            <ul>
                <li>Top hitters today</li>
                <li>Due for hits</li>
                <li>Cooling off alerts</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # CTA button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Upgrade to Premium - Unlock All Features", use_container_width=True, type="primary"):
            st.session_state.show_payment = True
            st.rerun()

