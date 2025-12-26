import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

from connection_engine import create_connection_postgresql

# 1. Setup Connection
load_dotenv()
engine = create_connection_postgresql() 

def get_pitcher_scouting_report(pitcher_name):
    query = text("""
    SELECT * FROM dim_pitcher_archetypes 
    WHERE full_name ILIKE :name
    LIMIT 1
    """)
    return pd.read_sql(query, engine, params={"name": f"%{pitcher_name}%"})

def get_opposing_lineup(team_code):
    # Note: In a real app, you'd pull the active roster. 
    # For now, we pull the top 9 hitters by plate appearances for that team.
    query = text("""
    SELECT h.* FROM dim_hitter_archetypes h
    JOIN dim_player p ON h.batter = p.key_mlbam
    WHERE p.team_id = :team
    ORDER BY h.total_pitches_faced DESC
    LIMIT 9
    """)
    return pd.read_sql(query, engine, params={"team": team_code})

def analyze_matchup(pitcher, hitter):
    """
    The 'Brain' of the engine. Compares Pitcher vs Hitter attributes.
    """
    notes = []
    advantage = "NEUTRAL"
    
    # 1. Power vs Power Check
    if pitcher['pitcher_archetype_label'] == 'Power Pitcher' and hitter['hitter_archetype_label'] in ['Elite Power Threat', 'Pull-Side Power Lead']:
        notes.append("💣 **HR RISK:** Power on Power. Avoid mistakes over plate.")
        
    # 2. Chase Logic
    if pitcher['stuff_grade'] >= 60 and hitter['chase_pct_raw'] > 30:
        notes.append("💎 **K OPPORTUNITY:** Hitter chases. Expand zone with 2 strikes.")
        advantage = "PITCHER"
        
    # 3. Platoon Logic (Simple version)
    if pitcher['hand'] != hitter['hand']:
        if hitter['neutrality_pct'] < 40:
             notes.append("⚠️ **PLATOON:** Hitter crushes opposite hand pitching.")

    # 4. Vertical Profile Logic (The most advanced part)
    # If Pitcher is a 'High Fastball' guy (High Whiff/High Velo) and Hitter is a 'Low Ball Golfer'
    # We can recommend staying UP in the zone.
    
    if not notes:
        notes.append("Standard approach.")
        
    return advantage, " | ".join(notes)

# --- MAIN EXECUTION ---
def run_game_plan(pitcher_name, opponent_team_id):
    print(f"\n⚾ GENERATING SCOUTING REPORT: {pitcher_name} vs. {opponent_team_id} ⚾")
    print("-" * 60)
    
    # 1. Get Pitcher
    pitcher_df = get_pitcher_scouting_report(pitcher_name)
    if pitcher_df.empty:
        print(f"❌ Pitcher '{pitcher_name}' not found.")
        return

    pitcher = pitcher_df.iloc[0]
    print(f"👤 PITCHER: {pitcher['full_name']} ({pitcher['hand']})")
    print(f"   Archetype: {pitcher['pitcher_archetype_label']}")
    #print(f"   Arsenal: {pitcher['pitch_mix_summary']}")
    print(f"   Grade: {pitcher['overall_grade']}")
    print("-" * 60)
    
    # 2. Get Lineup
    lineup_df = get_opposing_lineup(opponent_team_id)
    if lineup_df.empty:
        print(f"❌ No hitters found for team '{opponent_team_id}'.")
        return

    # 3. Iterate through Lineup
    print(f"{'HITTER':<25} | {'ARCHETYPE':<25} | {'PLAN / NOTES'}")
    print("-" * 100)
    
    for index, hitter in lineup_df.iterrows():
        adv, notes = analyze_matchup(pitcher, hitter)
        
        # Simple formatting for readability
        prefix = "🔴" if "RISK" in notes else "🟢" if "OPPORTUNITY" in notes else "⚪"
        
        print(f"{prefix} {hitter['full_name']:<22} | {hitter['hitter_archetype_label']:<25} | {notes}")

if __name__ == "__main__":
    # USER INPUTS: CHANGE THESE TO TEST
    target_pitcher = "Tarik Skubal"  # Try partial names like 'Wheeler', 'Cole', 'Strider'
    opponent_team = "PHI"       # Use Team Abbreviation (NYY, BOS, LAD, PHI, etc.)
    
    run_game_plan(target_pitcher, opponent_team)