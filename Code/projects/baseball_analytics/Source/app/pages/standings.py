"""
Standings Page - Free content
League standings
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import statsapi

app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.utils.app_helpers import cached_db_query, sidebar_settings
from app.utils.constants import get_team_abbr
from pages.predictions import format_to_local_time


def show():
    st.title("📈 League Standings & Recent Results")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["American League", "National League", "Recent Results"])
    
    with tab1:
        show_al_standings()
    
    with tab2:
        show_nl_standings()
    
    with tab3:
        show_recent_results()


def show_al_standings():
    """Show American League standings"""
    st.subheader("American League Standings")
    
    # Placeholder data - in production, query from database
    # st.info("📊 Standings data. In production, this would query from my database or MLB API")
    
    col1, col2, col3 = st.columns(3)
    
    # Call the function to display each division
    all_standings = get_division_standings_dfs()
    
    with col1:
        st.markdown("#### AL East")
        #st.dataframe(pd.DataFrame(al_east), width='stretch', hide_index=True)
        st.dataframe(all_standings['American League East'], width='stretch', hide_index=True)
    
    with col2:
        st.markdown("#### AL Central")
        # st.dataframe(pd.DataFrame(al_central), width='stretch', hide_index=True)
        st.dataframe(all_standings['American League Central'], width='stretch', hide_index=True)
    
    with col3:
        st.markdown("#### AL West")
        # st.dataframe(pd.DataFrame(al_west), width='stretch', hide_index=True)
        st.dataframe(all_standings['American League West'], width='stretch', hide_index=True)


def show_nl_standings():
    """Show National League standings"""
    st.subheader("National League Standings")
    
    #st.info("📊 Standings data. In production, this would query from your database or MLB API")
    
    col1, col2, col3 = st.columns(3)
    
    # Call the function to display each division
    all_standings = get_division_standings_dfs()
    
    with col1:
        st.markdown("#### NL East")
        # st.dataframe(pd.DataFrame(nl_east), width='stretch', hide_index=True)
        st.dataframe(all_standings['National League East'], width='stretch', hide_index=True)
    
    with col2:
        st.markdown("#### NL Central")
        # st.dataframe(pd.DataFrame(nl_central), width='stretch', hide_index=True)
        st.dataframe(all_standings['National League Central'], width='stretch', hide_index=True)
    
    with col3:
        st.markdown("#### NL West")
        # st.dataframe(pd.DataFrame(nl_west), width='stretch', hide_index=True)
        st.dataframe(all_standings['National League West'], width='stretch', hide_index=True)


def show_recent_results():
    """Show recent game results"""
    st.subheader("📊 Recent Game Results")
    
    #st.info("📊 Recent results. In production, this would query from your database or MLB API")
    
    # Placeholder recent results
    df_results_yesterday = get_game_results('2025-06-14')
    df_results_today     = get_game_results('2025-06-15')
    
    if not df_results_today.empty:
        # Apply the styling
        # .apply() looks at the DataFrame row by row (axis=1)
        styled_df = df_results_today.style.apply(highlight_winner, axis=1)
        
        st.subheader("Today's Results")
        st.dataframe(styled_df, width='stretch', hide_index=True)
    else:
        st.info("No games are scheduled for today.")
        
    if not df_results_yesterday.empty:
        # Apply the styling
        # .apply() looks at the DataFrame row by row (axis=1)
        styled_df = df_results_yesterday.style.apply(highlight_winner, axis=1)

        st.subheader("Yesterday's Results")
        st.dataframe(styled_df, width='stretch', hide_index=True)
    else:
        st.info("No games were played yesterday.")


def get_division_standings_dfs():
    """Fetches MLB standings, abbreviates team names, and formats for mobile."""
    
    TEAM_ABBR = get_team_abbr()

    # leagueId 103 is AL, 104 is NL
    # standings_raw = statsapi.standings_data(leagueId="103,104") #This should be dynamic based on current season
    standings_raw = statsapi.standings_data(leagueId="103,104", season=2025)
    division_dict = {}

    for division_id in standings_raw:
        div_name = standings_raw[division_id]['div_name']
        teams_list = standings_raw[division_id]['teams']
        
        df = pd.DataFrame(teams_list)
        
        # Abbreviate names to save horizontal space
        df['name'] = df['name'].map(TEAM_ABBR).fillna(df['name'])
        
        # Calculate PCT and format as .XXX (MLB Style)
        df['W%'] = df['w'] / (df['w'] + df['l']).replace(0, 1)
        df['W%'] = df['W%'].apply(lambda x: '{:.3f}'.format(x).lstrip('0'))
        # cols = ['name', 'w', 'l', 'gb', 'div_rank', 'wc_gb', 'wc_rank', 'league_rank']
        
        # Map raw fields to clean display names
        cols_map = {
            'name': 'TEAM',
            'w': 'W',
            'l': 'L',
            'W%': 'PCT',
            'gb': 'GB',
            'wc_gb': 'WCGB',
            'league_rank': 'LG RNK'
        }
        
        df = df[list(cols_map.keys())].rename(columns=cols_map)
        division_dict[div_name] = df
        
    return division_dict


def get_league_standings(league_id):
    """Fetches American/National League standings as a single DataFrame ordered by Rank."""
    
    TEAM_ABBR = get_team_abbr()

    # Fetch data only for the specified league
    standings_raw = statsapi.standings_data(leagueId=league_id, season=2025)
    
    # Combine all teams from all divisions into one list
    all_teams = []
    for division_id in standings_raw:
        all_teams.extend(standings_raw[division_id]['teams'])
    
    # Create the single DataFrame
    df = pd.DataFrame(all_teams)
    
    # 1. Abbreviate names
    df['name'] = df['name'].map(TEAM_ABBR).fillna(df['name'])
    
    # 2. Calculate PCT (Standard MLB format)
    df['W%'] = df['w'] / (df['w'] + df['l']).replace(0, 1)
    df['W%_sort'] = df['W%'] # Keep a numeric version for sorting
    df['W%'] = df['W%'].apply(lambda x: '{:.3f}'.format(x).lstrip('0'))
    
    # 3. Map and Rename
    cols_map = {
        'name': 'TEAM',
        'w': 'W',
        'l': 'L',
        'W%': 'PCT',
        # 'gb': 'GB',
        'wc_gb': 'WCGB',
        'league_rank': 'LG RNK'
    }
    
    # Convert 'league_rank' to numeric to ensure correct sorting (1 before 10)
    df['league_rank'] = pd.to_numeric(df['league_rank'])
    
    # Sort by League Rank
    df = df.sort_values(by='league_rank', ascending=True)
    
    # Final filter and rename
    df = df[list(cols_map.keys())].rename(columns=cols_map)
    
    df = df.head(5)  # Return top 5 teams in the league
    
    # Drop the temporary sorting column
    df = df.drop(columns=['LG RNK'])
    
    return df

def get_game_results(date_str, user_tz='US/Eastern'):
    """Get the latest results

    Args:
        date_str (_type_): _description_

    Returns:
        _type_: _description_
    """

    # Get team abbreviations
    TEAM_ABBR = get_team_abbr()
    
    # Fetch games for the specific date
    schedule = statsapi.schedule(date= date_str)
    
    if not schedule:
        return pd.DataFrame()

    results_list = []
    for game in schedule:
        # We only want games that are finished or in progress
        status = game.get("status", "")
        raw_time = game.get("game_datetime")
        
        # 1. Determine what to show in the "Status/Time" column
        if status == "In Progress":
            display_status = "LIVE"
        elif status == "Warmup":
            display_status = "Warmup"
        elif status == "Scheduled":
            display_status = format_to_local_time(raw_time, user_tz)
        elif "Final" in status:
            display_status = "Final"
        else:
            display_status = status # Fallback (Delayed, Postponed, etc.)
        
        # Extract Scores
        home_score = int(game.get("home_score", 0))
        away_score = int(game.get("away_score", 0))

        # Extract names and apply abbreviations
        home_full = game.get("home_name")
        away_full = game.get("away_name")
        
        # Extract Winning/Losing Pitchers (only available if game is Final)
        winning_pitcher = game.get("winning_pitcher", "N/A")
        losing_pitcher  = game.get("losing_pitcher", "N/A")

        results_list.append({
            # "Status": status,
            "Status": display_status,
            "Away": TEAM_ABBR.get(away_full, away_full),
            "R": away_score,
            "Home": TEAM_ABBR.get(home_full, home_full),
            "R ": home_score, # Space added to differentiate column name
            "Winner": winning_pitcher,
            "Loser": losing_pitcher,
            "Park": game.get("venue_name")
        })
    
    return pd.DataFrame(results_list)

def highlight_winner(row):
    # Default style (no background)
    style_away = ''
    style_home = ''
    
    # winning_style = 'background-color: #FFFFFF; color: #000000; font-weight: bold; border-radius: 4px;'
    winning_style = 'border-left: 5px solid #FFFFFF; font-weight: bold; color: #FFFFFF; padding-left: 5px;'
    
    # Highlight logic - only if the game is Final
    if "Final" in row['Status']:
        if row['R'] > row['R ']:
            style_away = winning_style
        elif row['R '] > row['R']:
            style_home = winning_style
            
    return [None, style_away, None, style_home, None, None, None, None] # None for columns we don't style
