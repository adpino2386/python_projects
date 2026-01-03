"""
Dashboard Page - Overview and key metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.utils.app_helpers import get_db_engine, cached_db_query
from app.utils.matchup_predictor import get_pitcher_archetype, get_hitter_archetypes


def show():
    st.title("📊 Dashboard")
    st.markdown("---")
    
    engine = get_db_engine()
    if not engine:
        st.error("Database connection error")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    pitchers_df = get_pitcher_archetype(engine)
    hitters_df = get_hitter_archetypes(engine)
    
    with col1:
        st.metric("Total Pitchers", len(pitchers_df) if not pitchers_df.empty else 0)
    
    with col2:
        st.metric("Total Hitters", len(hitters_df) if not hitters_df.empty else 0)
    
    with col3:
        if not pitchers_df.empty:
            top_pitchers = len(pitchers_df[pitchers_df['overall_grade'].isin(['A+', 'A'])])
            st.metric("Elite Pitchers (A/A+)", top_pitchers)
        else:
            st.metric("Elite Pitchers", 0)
    
    with col4:
        if not hitters_df.empty:
            top_hitters = len(hitters_df[hitters_df['overall_grade'].isin(['A+', 'A'])])
            st.metric("Elite Hitters (A/A+)", top_hitters)
        else:
            st.metric("Elite Hitters", 0)
    
    st.markdown("---")
    
    # Grade distribution
    col1, col2 = st.columns(2)
    
    with col1:
        if not pitchers_df.empty:
            st.subheader("Pitcher Grade Distribution")
            grade_counts = pitchers_df['overall_grade'].value_counts().sort_index()
            fig = px.pie(
                values=grade_counts.values,
                names=grade_counts.index,
                title="Pitchers by Grade"
            )
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        if not hitters_df.empty:
            st.subheader("Hitter Grade Distribution")
            grade_counts = hitters_df['overall_grade'].value_counts().sort_index()
            fig = px.pie(
                values=grade_counts.values,
                names=grade_counts.index,
                title="Hitters by Grade"
            )
            st.plotly_chart(fig, width='stretch')
    
    # Top players
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Pitchers")
        if not pitchers_df.empty:
            top_pitchers = pitchers_df.head(10)[['full_name', 'overall_grade', 'pitcher_archetype_label']]
            top_pitchers.columns = ['Name', 'Grade', 'Archetype']
            st.dataframe(top_pitchers, width='stretch', hide_index=True)
        else:
            st.info("No pitcher data available")
    
    with col2:
        st.subheader("🏆 Top 10 Hitters")
        if not hitters_df.empty:
            top_hitters = hitters_df.head(10)[['full_name', 'overall_grade', 'hitter_archetype_label']]
            top_hitters.columns = ['Name', 'Grade', 'Archetype']
            st.dataframe(top_hitters, width='stretch', hide_index=True)
        else:
            st.info("No hitter data available")

