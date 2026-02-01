"""
Home Page - Free tier content
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import statsapi
import pandas as pd
import pytz
from datetime import datetime

app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.utils.app_helpers import get_db_engine, cached_db_query, sidebar_settings
from app.pages.standings import get_league_standings
from app.pages.predictions import get_daily_starters, format_to_local_time, display_starter_card
from app.utils.constants import get_team_abbr
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import datetime


def show():
    st.title("⚾ Baseball Analytics Dashboard")
    st.markdown("---")
    
    # Use the helper function to set up sidebar
    # user_tz = sidebar_settings()
        
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
    
    # Team abbreviations to keep the table mobile-friendly
    TEAM_ABBR = get_team_abbr()
    
    if engine:
        # Get today's date string
        #today_str = datetime.now().strftime('%m/%d/%Y')
        # Try to get games (you'll need to implement this based on your data source)
        #st.info("⚡ Games for today will be displayed here. Premium members get detailed matchup analysis!")   
        #df_todays_games = get_daily_starters('6/15/2025', user_tz) # Example date         
        #df_games = get_daily_starters(date_str, user_tz='US/Eastern')

        # 1. Setup Auto-Refresh (updates every 60 seconds)
        st_autorefresh(interval=60 * 1000, key="datarefresh")

        # 2. Automatically get today's date logic
        today_obj = datetime.date.today()
        display_date = today_obj.strftime("%a, %b %d").upper()
        date_str = today_obj.strftime('%Y-%m-%d')

        st.markdown(f"### {display_date}")

        # 3. Fetch your DataFrame
        #df_games = get_daily_starters(date_str)
        df_games = get_daily_starters('6/15/2025') # Example date
        
        if not df_games.empty:
            cols = st.columns(4)
            for i in range(len(df_games)):
                with cols[i % 4]:
                    display_starter_card(df_games.iloc[i], TEAM_ABBR)
        else:
            st.info("No games scheduled for today.")
        
        # Show teaser
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Games Today", len(df_games), "Check Premium for Details")
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
        al_df = get_league_standings(103)
        st.dataframe(al_df, width='stretch', hide_index=True)
    
    with col2:
        st.subheader("National League")
        st.info("📊 Full standings available in Standings page")
        # Placeholder table
        nl_df = get_league_standings(104)
        st.dataframe(nl_df, width='stretch', hide_index=True)
    
    st.markdown("---")
    
    # Premium features teaser
    st.markdown("### ⭐ Premium Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='padding: 1.5rem; background-color: #1B1B1E; border-radius: 0.5rem; border-left: 4px solid #ffd700;'>
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
        <div style='padding: 1.5rem; background-color: #1B1B1E; border-radius: 0.5rem; border-left: 4px solid #ffd700;'>
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
        <div style='padding: 1.5rem; background-color: #1B1B1E; border-radius: 0.5rem; border-left: 4px solid #ffd700;'>
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
        if st.button("🚀 Upgrade to Premium - Unlock All Features", type="primary"):
            st.session_state.show_payment = True
            st.rerun()

