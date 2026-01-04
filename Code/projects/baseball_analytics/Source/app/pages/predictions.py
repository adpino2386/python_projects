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
from app.utils.matchup_predictor import (
    get_pitcher_archetype, get_hitter_archetypes,
    predict_game_outcome, predict_expected_statistics,
    predict_lineup_performance, predict_game_score, get_start_sit_recommendations,
    get_recent_form, adjust_for_recent_form
)
from app.utils.park_factors import (
    get_park_factor, get_weather_factor, TEAM_STADIUMS, WEATHER_FACTORS
)
from app.utils.constants import get_team_abbr


def show():
    st.title("🎯 Game Predictions & Matchups")
    st.markdown("---")
    
    # Tabs for different prediction views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📅 Today's Games",
        "🔥 Best Matchups",
        "❄️ Worst Matchups",
        "🎲 Due for Hits",
        "📉 Cooling Off",
        "⚾ Game Score Prediction"
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
    
    with tab6:
        show_game_score_prediction(engine)


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


def show_game_score_prediction(engine):
    """Show game score prediction (high/low scoring games)"""
    st.subheader("⚾ Game Score Prediction (High/Low Scoring)")
    st.info("Predict if games will be high-scoring (>8 runs) or low-scoring (≤8 runs) based on matchups, park factors, and weather")
    
    pitchers_df = get_pitcher_archetype(engine)
    all_hitters = get_hitter_archetypes(engine)
    
    if pitchers_df.empty or len(all_hitters) < 9:
        st.info("No data available")
        return
    
    # Get sample games for prediction
    st.markdown("### Select Game Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Select pitcher
        pitcher_names = pitchers_df['full_name'].tolist()
        selected_pitcher_name = st.selectbox("Select Starting Pitcher", pitcher_names)
        selected_pitcher = pitchers_df[pitchers_df['full_name'] == selected_pitcher_name].iloc[0].to_dict()
    
    with col2:
        # Select opponent lineup (sample)
        st.markdown("**Opponent Lineup:** (Sample)")
        lineup = all_hitters.sample(9)
        st.info(f"Selected {len(lineup)} hitters from database")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Park selection
        stadium_options = list(TEAM_STADIUMS.values()) + ["Neutral Park (1.0)"]
        selected_stadium = st.selectbox("Ballpark/Stadium", stadium_options)
        
        if selected_stadium == "Neutral Park (1.0)":
            park_factors = get_park_factor()
        else:
            park_factors = get_park_factor(stadium_name=selected_stadium)
        
        park_factor = park_factors['park_factor']
        
        st.info(f"**Park Factor:** {park_factor:.3f}\n\n"
                f"{'Hitter-friendly' if park_factor > 1.0 else 'Pitcher-friendly' if park_factor < 1.0 else 'Neutral'} park")
    
    with col2:
        # Weather selection
        weather_options = list(WEATHER_FACTORS.keys())
        weather_labels = [f"{key.replace('_', ' ').title()} - {WEATHER_FACTORS[key]['description']}" 
                         for key in weather_options]
        selected_weather_idx = st.selectbox("Weather Conditions", range(len(weather_options)), 
                                            format_func=lambda x: weather_labels[x])
        selected_weather = weather_options[selected_weather_idx]
        
        weather_factors = get_weather_factor(selected_weather)
        weather_multiplier = weather_factors['park_factor_multiplier']
        
        st.info(f"**Weather Factor:** {weather_multiplier:.3f}\n\n"
                f"{weather_factors['description']}")
    
    with col3:
        # Optional: Opponent pitcher
        st.markdown("**Opponent Pitcher (Optional)**")
        include_opponent = st.checkbox("Include opponent pitcher", value=False)
        
        opponent_pitcher = None
        if include_opponent:
            opp_pitcher_names = [p for p in pitcher_names if p != selected_pitcher_name]
            if opp_pitcher_names:
                selected_opp_pitcher_name = st.selectbox("Opponent Pitcher", opp_pitcher_names, 
                                                         key="opponent_pitcher")
                opponent_pitcher = pitchers_df[pitchers_df['full_name'] == selected_opp_pitcher_name].iloc[0].to_dict()
    
    st.markdown("---")
    
    # Predict game score
    if st.button("🎯 Predict Game Score", type="primary"):
        prediction = predict_game_score(
            selected_pitcher, 
            lineup,
            park_factor=park_factor,
            weather_factor=weather_multiplier,
            opponent_pitcher=opponent_pitcher
        )
        
        st.markdown("### Prediction Results")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            score_color = "🟢" if prediction['is_high_scoring'] else "🔵"
            st.metric(
                "Score Category",
                f"{score_color} {prediction['score_category']}",
                f"Threshold: {prediction['threshold']} runs"
            )
        
        with col2:
            st.metric(
                "Total Expected Runs",
                f"{prediction['total_expected_runs']:.2f}",
                f"Confidence: {prediction['confidence']}"
            )
        
        with col3:
            st.metric(
                "Pitcher Expected Runs Allowed",
                f"{prediction['pitcher_expected_runs_allowed']:.2f}",
                "Adjusted for park & weather"
            )
        
        with col4:
            st.metric(
                "Combined Adjustment",
                f"{prediction['combined_adjustment']:.3f}",
                f"Park: {prediction['park_factor']:.2f} × Weather: {prediction['weather_factor']:.2f}"
            )
        
        st.markdown("---")
        
        # Detailed breakdown
        st.markdown("### Detailed Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Factors Breakdown")
            factors_df = pd.DataFrame({
                'Factor': ['Park Factor', 'Weather Factor', 'Combined Adjustment'],
                'Value': [prediction['park_factor'], prediction['weather_factor'], prediction['combined_adjustment']],
                'Impact': [
                    'Hitter-friendly' if prediction['park_factor'] > 1.0 else 'Pitcher-friendly' if prediction['park_factor'] < 1.0 else 'Neutral',
                    weather_factors['description'],
                    'Hitter-friendly' if prediction['combined_adjustment'] > 1.0 else 'Pitcher-friendly' if prediction['combined_adjustment'] < 1.0 else 'Neutral'
                ]
            })
            st.dataframe(factors_df, width='stretch', hide_index=True)
        
        with col2:
            st.markdown("#### Prediction Summary")
            
            if prediction['is_high_scoring']:
                st.success(f"✅ **HIGH-SCORING GAME PREDICTED**\n\n"
                          f"Expected total runs: **{prediction['total_expected_runs']:.2f}**\n\n"
                          f"This game is predicted to exceed 8 total runs. Factors contributing:\n"
                          f"- {selected_stadium} is a {'hitter-friendly' if park_factor > 1.0 else 'neutral' if park_factor == 1.0 else 'pitcher-friendly'} park\n"
                          f"- Weather: {weather_factors['description']}\n"
                          f"- Matchup quality and park/weather adjustments favor offense")
            else:
                st.info(f"🔵 **LOW-SCORING GAME PREDICTED**\n\n"
                       f"Expected total runs: **{prediction['total_expected_runs']:.2f}**\n\n"
                       f"This game is predicted to have 8 or fewer total runs. Factors contributing:\n"
                       f"- {selected_stadium} is a {'pitcher-friendly' if park_factor < 1.0 else 'neutral' if park_factor == 1.0 else 'hitter-friendly'} park\n"
                       f"- Weather: {weather_factors['description']}\n"
                       f"- Matchup quality and park/weather adjustments favor pitching/defense")
        
        # Visual
        st.markdown("---")
        st.markdown("### Visualization")
        
        fig = go.Figure()
        
        # Add threshold line
        fig.add_hline(y=8.0, line_dash="dash", line_color="gray", 
                     annotation_text="High/Low Threshold (8 runs)")
        
        # Add predicted total runs
        color = 'red' if prediction['is_high_scoring'] else 'blue'
        fig.add_trace(go.Bar(
            x=['Predicted Total Runs'],
            y=[prediction['total_expected_runs']],
            marker_color=color,
            text=[f"{prediction['total_expected_runs']:.2f}"],
            textposition='auto',
            name='Predicted Runs'
        ))
        
        fig.update_layout(
            title="Game Score Prediction",
            yaxis_title="Total Runs",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Matchup details
        st.markdown("---")
        st.markdown("### Matchup Details")
        
        matchup_info = predict_game_outcome(selected_pitcher, lineup)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Pitcher:** {selected_pitcher['full_name']}")
            st.markdown(f"- Grade: {selected_pitcher.get('overall_grade', 'N/A')}")
            st.markdown(f"- Archetype: {selected_pitcher.get('pitcher_archetype_label', 'N/A')}")
            st.markdown(f"- Win Probability vs Opponent: {matchup_info['win_probability']}%")
        
        with col2:
            st.markdown(f"**Opponent Lineup:**")
            grade_counts = lineup['overall_grade'].value_counts().to_dict()
            st.markdown(f"- Grade Distribution: {grade_counts}")
            if matchup_info.get('top_threats'):
                st.markdown(f"- Top Threat: {matchup_info['top_threats'][0]['name']}")
            else:
                st.markdown("- Top Threat: N/A")


# Team abbreviations to keep the table mobile-friendly
TEAM_ABBR = get_team_abbr()


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