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
    
    # al_east = {
    #     'Team': ['Yankees', 'Orioles', 'Rays', 'Blue Jays', 'Red Sox'],
    #     'W': [95, 93, 90, 85, 80],
    #     'L': [67, 69, 72, 77, 82],
    #     'PCT': [.586, .574, .556, .525, .494],
    #     'GB': ['-', '2.0', '5.0', '10.0', '15.0']
    # }
    
    # al_central = {
    #     'Team': ['Guardians', 'Twins', 'Royals', 'Tigers', 'White Sox'],
    #     'W': [92, 88, 82, 78, 75],
    #     'L': [70, 74, 80, 84, 87],
    #     'PCT': [.568, .543, .506, .481, .463],
    #     'GB': ['-', '4.0', '10.0', '14.0', '17.0']
    # }
    
    # al_west = {
    #     'Team': ['Astros', 'Mariners', 'Rangers', 'Angels', 'Athletics'],
    #     'W': [94, 91, 86, 81, 68],
    #     'L': [68, 71, 76, 81, 94],
    #     'PCT': [.580, .562, .531, .500, .420],
    #     'GB': ['-', '3.0', '8.0', '13.0', '26.0']
    # }
    
    col1, col2, col3 = st.columns(3)
    
    # Call the function to display each division
    all_standings = get_division_standings_dfs()
    
    with col1:
        st.markdown("#### AL East")
        #st.dataframe(pd.DataFrame(al_east), width='stretch', hide_index=True)
        st.dataframe(all_standings['American League East'], width='content', hide_index=True)
    
    with col2:
        st.markdown("#### AL Central")
        # st.dataframe(pd.DataFrame(al_central), width='stretch', hide_index=True)
        st.dataframe(all_standings['American League Central'], width='content', hide_index=True)
    
    with col3:
        st.markdown("#### AL West")
        # st.dataframe(pd.DataFrame(al_west), width='stretch', hide_index=True)
        st.dataframe(all_standings['American League West'], width='content', hide_index=True)


def show_nl_standings():
    """Show National League standings"""
    st.subheader("National League Standings")
    
    st.info("📊 Standings data. In production, this would query from your database or MLB API")
    
    # nl_east = {
    #     'Team': ['Braves', 'Phillies', 'Mets', 'Marlins', 'Nationals'],
    #     'W': [98, 92, 88, 82, 76],
    #     'L': [64, 70, 74, 80, 86],
    #     'PCT': [.605, .568, .543, .506, .469],
    #     'GB': ['-', '6.0', '10.0', '16.0', '22.0']
    # }
    
    # nl_central = {
    #     'Team': ['Brewers', 'Cubs', 'Reds', 'Cardinals', 'Pirates'],
    #     'W': [91, 87, 83, 79, 74],
    #     'L': [71, 75, 79, 83, 88],
    #     'PCT': [.562, .537, .512, .488, .457],
    #     'GB': ['-', '4.0', '8.0', '12.0', '17.0']
    # }
    
    # nl_west = {
    #     'Team': ['Dodgers', 'Padres', 'Giants', 'Diamondbacks', 'Rockies'],
    #     'W': [100, 92, 87, 82, 70],
    #     'L': [62, 70, 75, 80, 92],
    #     'PCT': [.617, .568, .537, .506, .432],
    #     'GB': ['-', '8.0', '13.0', '18.0', '30.0']
    # }
    
    col1, col2, col3 = st.columns(3)
    
    # Call the function to display each division
    all_standings = get_division_standings_dfs()
    
    with col1:
        st.markdown("#### NL East")
        # st.dataframe(pd.DataFrame(nl_east), width='stretch', hide_index=True)
        st.dataframe(all_standings['National League East'], width='content', hide_index=True)
    
    with col2:
        st.markdown("#### NL Central")
        # st.dataframe(pd.DataFrame(nl_central), width='stretch', hide_index=True)
        st.dataframe(all_standings['National League Central'], width='content', hide_index=True)
    
    with col3:
        st.markdown("#### NL West")
        # st.dataframe(pd.DataFrame(nl_west), width='stretch', hide_index=True)
        st.dataframe(all_standings['National League West'], width='content', hide_index=True)


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
    """get division standings as DataFrames and return as a dictionary

    Returns:
        dictionary: Dictionary of DataFrames for each division
    """
    # leagueId 103 is AL, 104 is NL. Using both gets the whole league.
    standings_raw = statsapi.standings_data(leagueId="103,104")
    
    # This dictionary will hold { "Division Name": DataFrame }
    division_dict = {}

    for division_id in standings_raw:
        div_name = standings_raw[division_id]['div_name']
        teams_list = standings_raw[division_id]['teams']
        
        # Convert the list of team dicts directly to a DataFrame
        df = pd.DataFrame(teams_list)
        
        # Optional: Reorder or filter columns to keep it clean
        # TODO Calculate more columns like W%
        # cols = ['name', 'w', 'l', 'gb', 'div_rank', 'wc_gb', 'wc_rank', 'league_rank']
        cols = ['name', 'w', 'l', 'gb', 'wc_gb', 'wc_rank', 'league_rank']
        df = df[cols]
        
        # Rename columns for clarity
        df.rename(columns={
            'name': 'Team',
            'w': 'W',
            'l': 'L',
            'gb': 'GB',
            'wc_gb': 'WC GB',
            'wc_rank': 'WC Rank',
            'league_rank': 'League Rank'
        }, inplace=True)

        # Set the Division Name as the key in the dictionary
        division_dict[div_name] = df
        
    return division_dict

