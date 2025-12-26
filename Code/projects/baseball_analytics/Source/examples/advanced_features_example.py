"""
Advanced Features Examples
==========================

This script demonstrates the new advanced features added to the matchup predictor:
- Historical matchup data
- Expected statistics prediction
- Matchup confidence scoring
- Archetype compatibility analysis
- Team-level matchup analysis
- Bulk predictions
"""

import sys
import os
from pathlib import Path

# Add the Source directory to the path
source_dir = Path(__file__).parent.parent
sys.path.insert(0, str(source_dir))

from utils.connection_engine import create_connection_postgresql
from utils.matchup_predictor import (
    get_pitcher_archetype,
    get_hitter_archetypes,
    predict_game_outcome,
    predict_expected_statistics,
    calculate_matchup_confidence,
    get_historical_matchup,
    get_archetype_compatibility,
    analyze_team_matchup,
    predict_bulk_matchups,
    enhance_matchup_with_history,
    predict_individual_matchup
)
from dotenv import load_dotenv
import pandas as pd
engine = create_connection_postgresql() 

def example_historical_matchup():
    """Example: Get historical matchup data between pitcher and hitter"""
    print("=" * 70)
    print("FEATURE 1: Historical Matchup Data")
    print("=" * 70)
    
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    # Get a pitcher and hitter
    pitcher_df = get_pitcher_archetype(engine)
    hitter_df = get_hitter_archetypes(engine)
    
    if pitcher_df.empty or hitter_df.empty:
        print("Error: No data available")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    hitter = hitter_df.iloc[0].to_dict()
    
    pitcher_id = pitcher.get('pitcher')
    hitter_id = hitter.get('batter')
    
    print(f"\nChecking historical matchup:")
    print(f"  Pitcher: {pitcher['full_name']} (ID: {pitcher_id})")
    print(f"  Hitter: {hitter['full_name']} (ID: {hitter_id})")
    
    if pitcher_id and hitter_id:
        historical = get_historical_matchup(engine, pitcher_id, hitter_id, min_pitches=5)
        
        if historical:
            print(f"\n📊 Historical Matchup Data:")
            print(f"  Total Pitches: {historical['total_pitches']}")
            print(f"  Average wOBA: {historical['avg_woba']:.3f}")
            print(f"  Whiff Rate: {historical['whiff_rate']:.1f}%")
            print(f"  Hits: {historical['hits']}")
            print(f"  Home Runs: {historical['home_runs']}")
            print(f"  Strikeouts: {historical['strikeouts']}")
            print(f"  Walks: {historical['walks']}")
            print(f"  Batting Average: {historical['batting_avg']:.3f}")
            if historical['avg_exit_velocity']:
                print(f"  Avg Exit Velocity: {historical['avg_exit_velocity']:.1f} mph")
            print(f"  Barrels: {historical['barrels']}")
        else:
            print("\n  No historical matchup data available (insufficient pitches faced)")
    else:
        print("\n  Missing player IDs")


def example_expected_statistics():
    """Example: Predict expected statistics for a game"""
    print("\n" + "=" * 70)
    print("FEATURE 2: Expected Statistics Prediction")
    print("=" * 70)
    
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    pitcher_df = get_pitcher_archetype(engine)
    all_hitters = get_hitter_archetypes(engine)
    
    if pitcher_df.empty or len(all_hitters) < 9:
        print("Error: Insufficient data")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    lineup = all_hitters.sample(9)
    
    print(f"\nPitcher: {pitcher['full_name']}")
    print(f"Opposing Lineup: {len(lineup)} hitters")
    
    expected_stats = predict_expected_statistics(pitcher, lineup)
    
    print(f"\n📈 Expected Statistics (per 9 innings):")
    print(f"  Expected Runs Allowed: {expected_stats['expected_runs']}")
    print(f"  Expected Hits Allowed: {expected_stats['expected_hits']}")
    print(f"  Expected Strikeouts: {expected_stats['expected_strikeouts']}")
    print(f"  Expected Walks: {expected_stats['expected_walks']}")
    print(f"  Expected Home Runs: {expected_stats['expected_home_runs']}")
    print(f"  Expected WHIP: {expected_stats['expected_whip']}")
    print(f"  Expected ERA: {expected_stats['expected_era']}")
    print(f"  Matchup Adjustment: {expected_stats['matchup_adjustment']:+.2f}")


def example_confidence_scoring():
    """Example: Calculate confidence scores for matchup predictions"""
    print("\n" + "=" * 70)
    print("FEATURE 3: Matchup Confidence Scoring")
    print("=" * 70)
    
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    pitcher_df = get_pitcher_archetype(engine)
    hitter_df = get_hitter_archetypes(engine)
    
    if pitcher_df.empty or hitter_df.empty:
        print("Error: No data available")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    hitter = hitter_df.iloc[0].to_dict()
    
    confidence = calculate_matchup_confidence(pitcher, hitter)
    
    print(f"\nPitcher: {pitcher['full_name']}")
    print(f"  Total Pitches: {pitcher.get('total_pitches', 'N/A')}")
    print(f"  Data Quality: {pitcher.get('data_confidence', 'N/A')}")
    
    print(f"\nHitter: {hitter['full_name']}")
    print(f"  Total Pitches Faced: {hitter.get('total_pitches_faced', 'N/A')}")
    print(f"  Data Quality: {hitter.get('data_confidence', 'N/A')}")
    
    print(f"\n🎯 Matchup Confidence Score: {confidence:.1f}/100")
    
    if confidence >= 80:
        print("  Confidence Level: HIGH - Very reliable prediction")
    elif confidence >= 60:
        print("  Confidence Level: MEDIUM - Reliable prediction")
    else:
        print("  Confidence Level: LOW - Use with caution")


def example_archetype_compatibility():
    """Example: Analyze archetype compatibility"""
    print("\n" + "=" * 70)
    print("FEATURE 4: Archetype Compatibility Analysis")
    print("=" * 70)
    
    pitcher_df = get_pitcher_archetype(engine)
    hitter_df = get_hitter_archetypes(engine)
    
    if pitcher_df.empty or hitter_df.empty:
        print("Error: No data available")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    hitter = hitter_df.iloc[0].to_dict()
    
    pitcher_arch = pitcher.get('pitcher_archetype_label', 'Unknown')
    hitter_arch = hitter.get('hitter_archetype_label', 'Unknown')
    
    print(f"\nPitcher Archetype: {pitcher_arch}")
    print(f"Hitter Archetype: {hitter_arch}")
    
    compatibility = get_archetype_compatibility(pitcher_arch, hitter_arch)
    
    print(f"\n🔗 Compatibility Analysis:")
    print(f"  Compatibility Score: {compatibility['score']:+.2f}")
    print(f"  Reason: {compatibility['reason']}")
    
    if compatibility['score'] > 0:
        print("  → Pitcher has advantage based on archetype matchup")
    elif compatibility['score'] < 0:
        print("  → Hitter has advantage based on archetype matchup")
    else:
        print("  → Neutral archetype matchup")


def example_team_matchup():
    """Example: Analyze full team matchup"""
    print("\n" + "=" * 70)
    print("FEATURE 5: Team-Level Matchup Analysis")
    print("=" * 70)
    
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    pitcher_df = get_pitcher_archetype(engine)
    all_hitters = get_hitter_archetypes(engine)
    
    if pitcher_df.empty or len(all_hitters) < 18:
        print("Error: Insufficient data")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    opposing_lineup = all_hitters.sample(9).reset_index(drop=True)
    own_lineup = all_hitters.sample(9).reset_index(drop=True)
    
    print(f"\nStarting Pitcher: {pitcher['full_name']}")
    print(f"Opposing Lineup: {len(opposing_lineup)} hitters")
    print(f"Own Lineup: {len(own_lineup)} hitters")
    
    team_analysis = analyze_team_matchup(pitcher, opposing_lineup, own_lineup)
    
    print(f"\n🏟️  Team Matchup Analysis:")
    print(f"\nPitching Side:")
    print(f"  Win Probability: {team_analysis['pitcher_analysis']['win_probability']}%")
    print(f"  Pitcher Advantage: {team_analysis['pitcher_analysis']['pitcher_advantage']:+.2f}")
    print(f"  Expected Runs Allowed: {team_analysis['pitcher_analysis']['expected_runs_allowed']}")
    print(f"  Expected Strikeouts: {team_analysis['pitcher_analysis']['expected_strikeouts']}")
    
    if 'team_analysis' in team_analysis:
        print(f"\nFull Team Analysis:")
        print(f"  Own Lineup Quality: {team_analysis['team_analysis']['own_lineup_quality']:.2f}")
        print(f"  Opposing Lineup Quality: {team_analysis['team_analysis']['opposing_lineup_quality']:.2f}")
        print(f"  Lineup Advantage: {team_analysis['team_analysis']['lineup_advantage']:+.2f}")
        print(f"  Overall Team Advantage: {team_analysis['team_analysis']['overall_team_advantage']:+.2f}")


def example_bulk_predictions():
    """Example: Predict multiple matchups efficiently"""
    print("\n" + "=" * 70)
    print("FEATURE 6: Bulk Matchup Predictions")
    print("=" * 70)
    
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    # Get multiple pitchers and hitters
    all_pitchers = get_pitcher_archetype(engine)
    all_hitters = get_hitter_archetypes(engine)
    
    if len(all_pitchers) < 3 or len(all_hitters) < 27:
        print("Error: Insufficient data for bulk predictions")
        return
    
    # Create sample matchups
    matchups = []
    for i in range(min(3, len(all_pitchers))):
        pitcher = all_pitchers.iloc[i]
        lineup = all_hitters.sample(9)
        
        matchups.append({
            'pitcher_name': pitcher['full_name'],
            'hitter_names': lineup['full_name'].tolist()
        })
    
    print(f"\nPredicting {len(matchups)} matchups...")
    
    results = predict_bulk_matchups(engine, matchups)
    
    if not results.empty:
        print(f"\n📊 Bulk Prediction Results:")
        print(results.to_string(index=False))
    else:
        print("\nNo results generated")


def example_enhanced_matchup():
    """Example: Enhanced matchup with historical data"""
    print("\n" + "=" * 70)
    print("FEATURE 7: Enhanced Matchup with History")
    print("=" * 70)
    
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    pitcher_df = get_pitcher_archetype(engine)
    hitter_df = get_hitter_archetypes(engine)
    
    if pitcher_df.empty or hitter_df.empty:
        print("Error: No data available")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    hitter = hitter_df.iloc[0].to_dict()
    
    # Get base matchup
    matchup = predict_individual_matchup(pitcher, hitter)
    
    print(f"\nBase Matchup Prediction:")
    print(f"  {pitcher['full_name']} vs {hitter['full_name']}")
    print(f"  Combined Score: {matchup['combined_score']:+.2f}")
    print(f"  Hitter Advantage: {matchup['hitter_advantage']}")
    
    # Enhance with historical data
    enhanced = enhance_matchup_with_history(engine, pitcher, hitter, matchup)
    
    if enhanced.get('has_history'):
        print(f"\n📜 Enhanced with Historical Data:")
        print(f"  Historical Adjustment: {enhanced['historical_adjustment']:+.2f}")
        print(f"  Enhanced Score: {enhanced['enhanced_score']:+.2f}")
        print(f"  Historical wOBA: {enhanced['historical_data']['avg_woba']:.3f}")
        print(f"  Historical ABs: {enhanced['historical_data']['total_pitches']}")
    else:
        print(f"\n  No historical data available for enhancement")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ADVANCED MATCHUP PREDICTION FEATURES")
    print("=" * 70)
    
    try:
        example_historical_matchup()
        example_expected_statistics()
        example_confidence_scoring()
        example_archetype_compatibility()
        example_team_matchup()
        example_bulk_predictions()
        example_enhanced_matchup()
        
        print("\n" + "=" * 70)
        print("All advanced feature examples completed!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()

