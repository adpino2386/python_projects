"""
Predictions Page - Premium content
Shows game predictions, best/worst matchups, due for hits, cooling off
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import date, timedelta
import statsapi
import pandas as pd
import pytz
from datetime import datetime

app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.utils.app_helpers import get_db_engine, cached_db_query
from utils.matchup_predictor import (
    get_pitcher_archetype, get_hitter_archetypes,
    predict_game_outcome, predict_expected_statistics,
    predict_lineup_performance, get_start_sit_recommendations,
    get_recent_form, adjust_for_recent_form
)


def show():
    st.title("🎯 Game Predictions & Matchups")
    st.markdown("---")
    
    # Tabs for different prediction views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Today's Games",
        "🔥 Best Matchups",
        "❄️ Worst Matchups",
        "🎲 Due for Hits",
        "📉 Cooling Off"
    ])
    
    engine = get_db_engine()
    if not engine:
        st.error("Database connection error")
        return
    
    with tab1:
        show_todays_games(engine)
    
    with tab2:
        show_best_matchups(engine)
    
    with tab3:
        show_worst_matchups(engine)
    
    with tab4:
        show_due_for_hits(engine)
    
    with tab5:
        show_cooling_off(engine)


def show_todays_games(engine):
    """Show today's game predictions"""
    st.subheader("📅 Today's Game Predictions")
    
    # Get all pitchers
    pitchers_df = get_pitcher_archetype(engine)
    
    if pitchers_df.empty:
        st.info("No pitcher data available. Please update your database.")
        return
    
    # For demo, show top 5 pitchers as "today's games"
    st.info("📊 Showing sample game predictions. In production, this would pull from MLB schedule API.")
    
    selected_pitchers = pitchers_df.head(5)
    
    predictions_data = []
    
    for idx, pitcher_row in selected_pitchers.iterrows():
        pitcher = pitcher_row.to_dict()
        
        # Get a sample lineup
        all_hitters = get_hitter_archetypes(engine)
        if len(all_hitters) < 9:
            continue
        
        lineup = all_hitters.sample(9)
        
        try:
            prediction = predict_game_outcome(pitcher, lineup)
            expected = predict_expected_statistics(pitcher, lineup)
            
            predictions_data.append({
                'Pitcher': pitcher['full_name'],
                'Win Prob': prediction['win_probability'],
                'Advantage': prediction['pitcher_advantage'],
                'Exp Runs': expected['expected_runs'],
                'Exp K': expected['expected_strikeouts'],
                'Exp WHIP': expected['expected_whip']
            })
        except Exception as e:
            st.error(f"Error predicting for {pitcher['full_name']}: {e}")
            continue
    
    if predictions_data:
        pred_df = pd.DataFrame(predictions_data)
        
        # Display metrics
        cols = st.columns(5)
        for i, (_, row) in enumerate(pred_df.iterrows()):
            if i < 5:
                with cols[i]:
                    st.metric(
                        row['Pitcher'],
                        f"{row['Win Prob']:.1f}%",
                        f"{row['Advantage']:+.2f}"
                    )
        
        st.markdown("### Detailed Predictions")
        st.dataframe(pred_df, width='stretch', hide_index=True)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                pred_df, x='Pitcher', y='Win Prob',
                title="Win Probability by Pitcher",
                color='Win Prob',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            fig = px.scatter(
                pred_df, x='Exp Runs', y='Exp K',
                size='Win Prob', hover_name='Pitcher',
                title="Expected Runs vs Strikeouts",
                labels={'Exp Runs': 'Expected Runs Allowed', 'Exp K': 'Expected Strikeouts'}
            )
            st.plotly_chart(fig, width='stretch')


def show_best_matchups(engine):
    """Show best hitter matchups of the day"""
    st.subheader("🔥 Best Hitter Matchups Today")
    st.info("Hitters with the best chance to get hits based on matchup analysis")
    
    # Get pitchers for today (sample)
    pitchers_df = get_pitcher_archetype(engine)
    all_hitters = get_hitter_archetypes(engine)
    
    if pitchers_df.empty or all_hitters.empty:
        st.info("No data available")
        return
    
    best_matchups = []
    
    # Analyze top 10 pitchers vs all hitters
    for _, pitcher_row in pitchers_df.head(10).iterrows():
        pitcher = pitcher_row.to_dict()
        
        # Get top hitter matchups vs this pitcher
        lineup_analysis = predict_lineup_performance(pitcher, all_hitters.head(50))
        
        # Get top 3 best hitter matchups (lowest combined_score)
        top_matchups = lineup_analysis.head(3)
        
        for _, matchup in top_matchups.iterrows():
            if matchup['hitter_advantage']:
                best_matchups.append({
                    'Hitter': matchup['hitter_name'],
                    'Hitter Grade': matchup['hitter_grade'],
                    'Pitcher': pitcher['full_name'],
                    'Pitcher Grade': pitcher.get('overall_grade', 'C'),
                    'Matchup Score': matchup['combined_score'],
                    'Advantage': 'HITTER'
                })
    
    if best_matchups:
        best_df = pd.DataFrame(best_matchups)
        best_df = best_df.sort_values('Matchup Score', ascending=True).head(20)
        best_df['Matchup Score'] = best_df['Matchup Score'].round(2)
        
        st.dataframe(best_df, width='stretch', hide_index=True)
        
        # Chart
        fig = px.bar(
            best_df.head(15), x='Hitter', y='Matchup Score',
            color='Matchup Score',
            title="Top 15 Best Hitter Matchups",
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No matchups found")


def show_worst_matchups(engine):
    """Show worst hitter matchups (pitcher advantage)"""
    st.subheader("❄️ Worst Matchups (Pitcher Advantage)")
    st.info("Pitchers with the best chance to dominate today")
    
    pitchers_df = get_pitcher_archetype(engine)
    all_hitters = get_hitter_archetypes(engine)
    
    if pitchers_df.empty or len(all_hitters) < 9:
        st.info("No data available")
        return
    
    pitcher_performance = []
    
    for _, pitcher_row in pitchers_df.head(20).iterrows():
        pitcher = pitcher_row.to_dict()
        
        # Get a sample lineup
        lineup = all_hitters.sample(9)
        
        try:
            prediction = predict_game_outcome(pitcher, lineup)
            expected = predict_expected_statistics(pitcher, lineup)
            
            pitcher_performance.append({
                'Pitcher': pitcher['full_name'],
                'Grade': pitcher.get('overall_grade', 'C'),
                'Win Probability': prediction['win_probability'],
                'Advantage': prediction['pitcher_advantage'],
                'Exp Runs': expected['expected_runs'],
                'Exp Strikeouts': expected['expected_strikeouts']
            })
        except:
            continue
    
    if pitcher_performance:
        perf_df = pd.DataFrame(pitcher_performance)
        perf_df = perf_df.sort_values('Win Probability', ascending=False).head(15)
        
        st.dataframe(perf_df, width='stretch', hide_index=True)
        
        # Chart
        fig = px.bar(
            perf_df, x='Pitcher', y='Win Probability',
            color='Win Probability',
            title="Top Pitcher Advantages (Highest Win Probability)",
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')


def show_due_for_hits(engine):
    """Show players due for hits (bad luck)"""
    st.subheader("🎲 Players Due for Hits (Bad Luck)")
    st.info("Players with high tools but low results - likely to improve")
    
    # Query luck scores
    query = """
    SELECT 
        CONCAT(p.first_name_chadwick, ' ', p.last_name_chadwick) AS full_name,
        l.luck_score,
        l.luck_confidence,
        l.at_bats
    FROM fact_player_luck_summary l
    JOIN dim_player p ON l.batter = p.key_mlbam
    WHERE l.luck_score > 0.1
        AND l.luck_confidence > 0.3
    ORDER BY l.luck_score DESC
    LIMIT 20
    """
    
    df = cached_db_query(query)
    
    if df is not None and not df.empty:
        df.columns = ['Player', 'Luck Score', 'Confidence', 'At Bats']
        df['Luck Score'] = df['Luck Score'].round(3)
        df['Confidence'] = (df['Confidence'] * 100).round(1)
        
        st.dataframe(df, width='stretch', hide_index=True)
        
        # Chart
        fig = px.bar(
            df, x='Player', y='Luck Score',
            color='Confidence',
            title="Players Due for Hits (Higher = More Unlucky)",
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No luck score data available. Please run luck score calculations.")


def show_cooling_off(engine):
    """Show players likely to cool off (overperforming)"""
    st.subheader("📉 Players Likely to Cool Off")
    st.info("Players hitting above expected results - regression likely")
    
    # Query luck scores (negative = lucky/overperforming)
    query = """
    SELECT 
        CONCAT(p.first_name_chadwick, ' ', p.last_name_chadwick) AS full_name,
        l.luck_score,
        l.luck_confidence,
        l.at_bats
    FROM fact_player_luck_summary l
    JOIN dim_player p ON l.batter = p.key_mlbam
    WHERE l.luck_score < -0.1
        AND l.luck_confidence > 0.3
    ORDER BY l.luck_score ASC
    LIMIT 20
    """
    
    df = cached_db_query(query)
    
    if df is not None and not df.empty:
        df.columns = ['Player', 'Luck Score', 'Confidence', 'At Bats']
        df['Luck Score'] = df['Luck Score'].round(3)
        df['Confidence'] = (df['Confidence'] * 100).round(1)
        df['Luck Score'] = df['Luck Score'].abs()  # Make positive for display
        
        st.dataframe(df, width='stretch', hide_index=True)
        
        # Chart
        fig = px.bar(
            df, x='Player', y='Luck Score',
            color='Confidence',
            title="Players Likely to Cool Off (Higher = More Overperforming)",
            color_continuous_scale='Oranges'
        )
        fig.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No luck score data available. Please run luck score calculations.")



# Team abbreviations to keep the table mobile-friendly
TEAM_ABBR = {
    'Arizona Diamondbacks': 'ARI', 'Atlanta Braves': 'ATL', 'Baltimore Orioles': 'BAL',
    'Boston Red Sox': 'BOS', 'Chicago White Sox': 'CWS', 'Chicago Cubs': 'CHC',
    'Cincinnati Reds': 'CIN', 'Cleveland Guardians': 'CLE', 'Colorado Rockies': 'COL',
    'Detroit Tigers': 'DET', 'Houston Astros': 'HOU', 'Kansas City Royals': 'KC',
    'Los Angeles Angels': 'LAA', 'Los Angeles Dodgers': 'LAD', 'Miami Marlins': 'MIA',
    'Milwaukee Brewers': 'MIL', 'Minnesota Twins': 'MIN', 'New York Mets': 'NYM',
    'New York Yankees': 'NYY', 'Athletics': 'ATH', 'Philadelphia Phillies': 'PHI',
    'Pittsburgh Pirates': 'PIT', 'San Diego Padres': 'SD', 'San Francisco Giants': 'SF',
    'Seattle Mariners': 'SEA', 'St. Louis Cardinals': 'STL', 'Tampa Bay Rays': 'TB',
    'Texas Rangers': 'TEX', 'Toronto Blue Jays': 'TOR', 'Washington Nationals': 'WSH'
}


def format_to_local_time(utc_str, local_tz_str='US/Eastern'):
    """Helper to convert ISO UTC string to 12-hour local time."""
    if not utc_str:
        return "TBD"
    try:
        # Parse UTC string (e.g., 2025-06-15T18:10:00Z)
        utc_dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
        local_tz = pytz.timezone(local_tz_str)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime('%I:%M %p')
    except Exception:
        return "TBD"


def get_daily_starters(date_str, user_tz='US/Eastern'):
    # 1. Fetch all games for the specified date
    schedule = statsapi.schedule(date= date_str)
    
    if not schedule:
        return pd.DataFrame() # Return empty if no games
        
    games_list = []
    
    for game in schedule:
        # Convert UTC to Local Time using our helper
        raw_time = game.get("game_datetime")
        #print(f"DEBUG: Game between {game.get('home_name')} and {game.get('away_name')} has time: {raw_time}")
        local_time = format_to_local_time(raw_time, user_tz)

        # Extract names and apply abbreviations
        home_full = game.get("home_name")
        away_full = game.get("away_name")

        game_data = {
            "Time": local_time,
            "Away": TEAM_ABBR.get(away_full, away_full),
            "Home": TEAM_ABBR.get(home_full, home_full),
            "Away Pitcher": game.get("away_probable_pitcher", "TBD"),
            "Home Pitcher": game.get("home_probable_pitcher", "TBD"),
            "Away Score": game.get("away_score", 0),
            "Home Score": game.get("home_score", 0),
            "Status": game.get("status"),
            "Venue": game.get("venue_name"),
            "game_id": game.get("game_id") # Keeping ID for background lookups
        }
        games_list.append(game_data)
    
    # 2. Convert to DataFrame
    df = pd.DataFrame(games_list)
    
    return df