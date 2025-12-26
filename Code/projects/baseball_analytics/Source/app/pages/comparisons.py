"""
Comparisons Page - Premium content
Head-to-head comparisons, player comparisons
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.utils.app_helpers import get_db_engine
from utils.matchup_predictor import (
    get_pitcher_archetype, get_hitter_archetypes,
    compare_pitchers_vs_lineup, predict_individual_matchup
)


def show():
    st.title("⚔️ Player Comparisons")
    st.markdown("---")
    
    engine = get_db_engine()
    if not engine:
        st.error("Database connection error")
        return
    
    tab1, tab2, tab3 = st.tabs([
        "🔀 Head-to-Head",
        "📊 Pitcher Comparison",
        "👥 Hitter Comparison"
    ])
    
    with tab1:
        show_head_to_head(engine)
    
    with tab2:
        show_pitcher_comparison(engine)
    
    with tab3:
        show_hitter_comparison(engine)


def show_head_to_head(engine):
    """Show head-to-head matchup comparison"""
    st.subheader("🔀 Pitcher vs Hitter Head-to-Head")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pitchers_df = get_pitcher_archetype(engine)
        if pitchers_df.empty:
            st.error("No pitcher data available")
            return
        
        pitcher_names = pitchers_df['full_name'].tolist()
        selected_pitcher_name = st.selectbox("Select Pitcher", pitcher_names)
        selected_pitcher = pitchers_df[pitchers_df['full_name'] == selected_pitcher_name].iloc[0].to_dict()
    
    with col2:
        hitters_df = get_hitter_archetypes(engine)
        if hitters_df.empty:
            st.error("No hitter data available")
            return
        
        hitter_names = hitters_df['full_name'].tolist()
        selected_hitter_name = st.selectbox("Select Hitter", hitter_names)
        selected_hitter = hitters_df[hitters_df['full_name'] == selected_hitter_name].iloc[0].to_dict()
    
    if st.button("Analyze Matchup"):
        matchup = predict_individual_matchup(selected_pitcher, selected_hitter)
        
        st.markdown("### Matchup Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Edge Score", f"{matchup['edge_score']:+.2f}", 
                     "Positive = Pitcher Advantage")
        
        with col2:
            st.metric("Talent Gap", f"{matchup['talent_gap']:+.2f}",
                     "Positive = Pitcher Advantage")
        
        with col3:
            st.metric("Combined Score", f"{matchup['combined_score']:+.2f}",
                     "Negative = Hitter Advantage")
        
        with col4:
            advantage = "HITTER" if matchup['hitter_advantage'] else "PITCHER"
            st.metric("Advantage", advantage)
        
        st.markdown("### Key Factors")
        if matchup['reasons']:
            for reason in matchup['reasons'][:5]:
                st.info(f"• {reason}")
        else:
            st.info("No specific matchup factors identified")
        
        # Visual
        fig = px.bar(
            x=['Edge Score', 'Talent Gap', 'Combined'],
            y=[matchup['edge_score'], matchup['talent_gap'], matchup['combined_score']],
            title="Matchup Score Breakdown",
            labels={'x': 'Score Type', 'y': 'Value'}
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, width='stretch')


def show_pitcher_comparison(engine):
    """Compare multiple pitchers"""
    st.subheader("📊 Compare Pitchers")
    
    pitchers_df = get_pitcher_archetype(engine)
    if pitchers_df.empty:
        st.error("No pitcher data available")
        return
    
    selected_pitchers = st.multiselect(
        "Select Pitchers to Compare (max 5)",
        pitchers_df['full_name'].tolist(),
        max_selections=5
    )
    
    if len(selected_pitchers) >= 2:
        if st.button("Compare Pitchers"):
            pitcher_ids = pitchers_df[pitchers_df['full_name'].isin(selected_pitchers)]['pitcher'].tolist()
            
            # Get a sample lineup for comparison
            hitters_df = get_hitter_archetypes(engine)
            if len(hitters_df) >= 9:
                lineup = hitters_df.sample(9)
                
                comparison = compare_pitchers_vs_lineup(engine, pitcher_ids, lineup)
                
                if not comparison.empty:
                    st.dataframe(comparison, width='stretch', hide_index=True)
                    
                    # Visual comparison
                    fig = px.bar(
                        comparison, x='pitcher_name', y='win_probability',
                        color='win_probability',
                        title="Win Probability Comparison",
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, width='stretch')
    else:
        st.info("Select at least 2 pitchers to compare")


def show_hitter_comparison(engine):
    """Compare hitters"""
    st.subheader("👥 Compare Hitters")
    
    hitters_df = get_hitter_archetypes(engine)
    if hitters_df.empty:
        st.error("No hitter data available")
        return
    
    selected_hitters = st.multiselect(
        "Select Hitters to Compare (max 5)",
        hitters_df['full_name'].tolist(),
        max_selections=5
    )
    
    if len(selected_hitters) >= 2:
        selected_data = hitters_df[hitters_df['full_name'].isin(selected_hitters)]
        
        comparison_cols = ['full_name', 'overall_grade', 'power_score', 'discipline_score']
        available_cols = [col for col in comparison_cols if col in selected_data.columns]
        
        if available_cols:
            comparison_df = selected_data[available_cols].copy()
            comparison_df.columns = [col.replace('_', ' ').title() for col in comparison_df.columns]
            st.dataframe(comparison_df, width='stretch', hide_index=True)
    else:
        st.info("Select at least 2 hitters to compare")

