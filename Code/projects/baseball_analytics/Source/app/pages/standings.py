"""
Standings Page - Free content
League standings
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import statsapi
import datetime

app_dir = Path(__file__).parent.parent
source_dir = app_dir.parent
sys.path.insert(0, str(source_dir))

from app.utils.app_helpers import cached_db_query, sidebar_settings
from app.utils.constants import get_team_abbr
from pages.predictions import format_to_local_time

# Pulse animation for red dot
st.markdown("""
<style>
@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 75, 75, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
}
.red-dot {
    background: #ff4b4b;
    border-radius: 50%;
    height: 10px;
    width: 10px;
    display: inline-block;
    margin-right: 5px;
    animation: pulse 2s infinite;
}
</style>
""", unsafe_allow_html=True)

def show():  
    st.title("Recent Results & League Standings")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["Recent Results", "AL Standings", "NL Standings"])
    
    with tab1:
        show_recent_results()        
    
    with tab2:
        show_al_standings()
    
    with tab3:
        show_nl_standings()


def show_al_standings():
    """Show American League standings"""
    st.subheader("American League Standings")
    
    # Placeholder data - in production, query from database
    # st.info("Standings data. In production, this would query from my database or MLB API")
    
    col1, col2, col3 = st.columns(3)
    
    # Call the function to display each division
    all_standings = get_division_standings_dfs()
    
    with col1:
        st.markdown("#### AL East")
        st.dataframe(all_standings['American League East'], width='stretch', hide_index=True)
    
    with col2:
        st.markdown("#### AL Central")
        st.dataframe(all_standings['American League Central'], width='stretch', hide_index=True)
    
    with col3: 
        st.markdown("#### AL West")
        st.dataframe(all_standings['American League West'], width='stretch', hide_index=True)


def show_nl_standings():
    """Show National League standings"""
    st.subheader("National League Standings")  
    
    #st.info("Standings data. In production, this would query from your database or MLB API")
    
    col1, col2, col3 = st.columns(3)
    
    # Call the function to display each division
    all_standings = get_division_standings_dfs()
    
    with col1:
        st.markdown("#### NL East")
        st.dataframe(all_standings['National League East'], width='stretch', hide_index=True)
    
    with col2:
        st.markdown("#### NL Central")
        st.dataframe(all_standings['National League Central'], width='stretch', hide_index=True)
    
    with col3:
        st.markdown("#### NL West")
        st.dataframe(all_standings['National League West'], width='stretch', hide_index=True)


def show_recent_results():
    """Show recent game results"""
    #st.subheader("Recent Game Results")
    
    TEAM_ABBR = get_team_abbr() 
    
    #st.info("Recent results. In production, this would query from your database or MLB API")
        
    # Use the cached function to get today's results
    @st.cache_data(ttl=60)
    def get_hydrated_games(date_str):
        # We ask for 'linescore' and 'team' hydration explicitly
        params = {'date': date_str, 'sportId': 1, 'hydrate': 'team,linescore,decisions'}
        data = statsapi.get('schedule', params)
        if not data.get('dates'):
            return []
        return data['dates'][0].get('games', [])
    
    # Date Picker at the top
    selected_date = st.date_input("Select Date", 
                                datetime.date.today(), 
                                format="YYYY-MM-DD",
                                width= 150)
    
    date_str = selected_date.strftime('%Y-%m-%d')
    
    # Call the hydrated games function and assign to variable games
    games = get_hydrated_games(date_str)

    st.header(f"Scoreboard: {selected_date.strftime('%B %d, %Y')}")

    # Grid logic: 4 columns
    if games:
        cols = st.columns(4)
        for i, game in enumerate(games):
            with cols[i % 4]:
                display_game_card(game, TEAM_ABBR)
    else:
        st.info("No games found for this date.")


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


def display_game_card(game, TEAM_ABBR):
    # --- DATA EXTRACTION ---
    game_id = game.get('gamePk') # Needed for the highlight link
    linescore = game.get('linescore', {})
    away_stats = linescore.get('teams', {}).get('away', {})
    home_stats = linescore.get('teams', {}).get('home', {})
    
    status_raw = game.get('status', {}).get('detailedState', '').upper()
    venue = game.get('venue', {}).get('name', 'N/A')

    # Team Info & Logos
    away_team = game.get('teams', {}).get('away', {})
    home_team = game.get('teams', {}).get('home', {})
    a_id = away_team['team']['id']
    h_id = home_team['team']['id']
    a_logo = f"https://www.mlbstatic.com/team-logos/{a_id}.svg"
    h_logo = f"https://www.mlbstatic.com/team-logos/{h_id}.svg"
    
    # --- PITCHER DATA ---
    decisions = game.get('decisions', {})
    win_p = decisions.get('winner', {}).get('fullName')
    lose_p = decisions.get('loser', {}).get('fullName')
    save_p = decisions.get('save', {}).get('fullName')

    # Pulse Logic
    is_live = status_raw in ["IN PROGRESS", "LIVE", "WARMUP"]
    live_indicator = '<span class="red-dot"></span>' if is_live else ""

    with st.container(border=True):
        # Header for R-H-E
        cols_h = st.columns([0.6, 3.4, 1, 1, 1])
        cols_h[2].caption("R")
        cols_h[3].caption("H")
        cols_h[4].caption("E")
        
        # --- AWAY ROW ---
        row_a = st.columns([0.6, 3.4, 1, 1, 1])
        with row_a[0]: st.image(a_logo)
        with row_a[1]:
            a_full = away_team['team']['name']
            a_rec = away_team.get('leagueRecord', {})
            st.markdown(f"**{TEAM_ABBR.get(a_full, a_full)}** <span style='color:gray; font-size:0.8em;'>{a_rec.get('wins', 0)}-{a_rec.get('losses', 0)}</span>", unsafe_allow_html=True)
        row_a[2].markdown(f"**{away_stats.get('runs', 0)}**")
        row_a[3].markdown(f"{away_stats.get('hits', 0)}")
        row_a[4].markdown(f"{away_stats.get('errors', 0)}")

        # --- HOME ROW ---
        row_h = st.columns([0.6, 3.4, 1, 1, 1])
        with row_h[0]: st.image(h_logo)
        with row_h[1]:
            h_full = home_team['team']['name']
            h_rec = home_team.get('leagueRecord', {})
            st.markdown(f"**{TEAM_ABBR.get(h_full, h_full)}** <span style='color:gray; font-size:0.8em;'>{h_rec.get('wins', 0)}-{h_rec.get('losses', 0)}</span>", unsafe_allow_html=True)
        row_h[2].markdown(f"**{home_stats.get('runs', 0)}**")
        row_h[3].markdown(f"{home_stats.get('hits', 0)}")
        row_h[4].markdown(f"{home_stats.get('errors', 0)}")
        
        st.divider()
        # st.markdown(f"{live_indicator} **{status_raw}** @ {venue}", unsafe_allow_html=True)
        st.markdown(f"{live_indicator} **{status_raw}**", unsafe_allow_html=True)

        # --- PITCHERS SECTION ---
        if win_p or lose_p:
            pitcher_html = "<div style='font-size:0.85em; color:#cccccc; padding-top:5px;'>"
            if win_p: pitcher_html += f"<b>W:</b> {win_p} &nbsp;&nbsp;"
            if lose_p: pitcher_html += f"<b>L:</b> {lose_p} &nbsp;&nbsp;"
            if save_p: pitcher_html += f"<b>S:</b> {save_p}"
            pitcher_html += "</div>"
            st.markdown(pitcher_html, unsafe_allow_html=True)

        # --- GAME SUMMARY & HIGHLIGHTS ---
        with st.expander("Game Summary"):
            st.write(f"**Venue:** {venue}")
            if status_raw == "FINAL":
                # Link to MLB.com Highlights
                highlight_url = f"https://www.mlb.com/gameday/{game_id}/final/video"
                st.markdown(f"📺 [Watch Game Highlights]({highlight_url})")
            elif is_live:
                live_url = f"https://www.mlb.com/gameday/{game_id}"
                st.markdown(f"📺 [Follow Live on Gameday]({live_url})")
            else:
                st.write("Highlights will be available after the game concludes.")