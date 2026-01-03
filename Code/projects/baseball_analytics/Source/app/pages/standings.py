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

from app.utils.app_helpers import cached_db_query


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
    
    st.info("📊 Recent results. In production, this would query from your database or MLB API")
    
    # Placeholder recent results
    recent_games = {
        'Date': ['2024-12-25', '2024-12-25', '2024-12-25', '2024-12-24', '2024-12-24'],
        'Away Team': ['Yankees', 'Dodgers', 'Astros', 'Braves', 'Orioles'],
        'Away Score': [5, 3, 7, 4, 2],
        'Home Team': ['Red Sox', 'Giants', 'Mariners', 'Phillies', 'Rays'],
        'Home Score': [3, 1, 2, 6, 0],
        'Result': ['Yankees W', 'Dodgers W', 'Astros W', 'Phillies W', 'Orioles W']
    }
    
    st.dataframe(pd.DataFrame(recent_games), width='stretch', hide_index=True)


def get_division_standings_dfs():
    """Fetches MLB standings, abbreviates team names, and formats for mobile."""
    
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
