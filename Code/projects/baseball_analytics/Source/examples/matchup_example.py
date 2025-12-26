"""
Example Usage of Matchup Predictor
==================================

This script demonstrates how to use the matchup prediction module to analyze
pitcher vs hitter matchups and predict game outcomes.
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
    analyze_matchup_summary,
    predict_lineup_performance
)
from dotenv import load_dotenv
import pandas as pd


def example_individual_matchup():
    """Example: Analyze a single pitcher vs a single hitter"""
    print("=" * 60)
    print("EXAMPLE 1: Individual Pitcher vs Hitter Matchup")
    print("=" * 60)
    
    # Create database connection
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    # Get a specific pitcher
    pitcher_df = get_pitcher_archetype(engine, pitcher_name="Gerrit Cole")
    if pitcher_df.empty:
        print("Pitcher not found. Using first available pitcher.")
        pitcher_df = get_pitcher_archetype(engine)
    
    pitcher = pitcher_df.iloc[0].to_dict()
    print(f"\nPitcher: {pitcher['full_name']}")
    print(f"  Archetype: {pitcher.get('pitcher_archetype_label', 'N/A')}")
    print(f"  Grade: {pitcher.get('overall_grade', 'N/A')}")
    print(f"  Attack Profile: {pitcher.get('attack_profile', 'N/A')}")
    
    # Get a specific hitter
    hitter_df = get_hitter_archetypes(engine, hitter_names=["Mike Trout"])
    if hitter_df.empty:
        print("\nHitter not found. Using first available hitter.")
        hitter_df = get_hitter_archetypes(engine)
    
    hitter = hitter_df.iloc[0].to_dict()
    print(f"\nHitter: {hitter['full_name']}")
    print(f"  Archetype: {hitter.get('hitter_archetype_label', 'N/A')}")
    print(f"  Grade: {hitter.get('overall_grade', 'N/A')}")
    print(f"  Vertical Profile: {hitter.get('vertical_profile', 'N/A')}")
    
    # Analyze matchup
    from utils.matchup_predictor import predict_individual_matchup
    matchup = predict_individual_matchup(pitcher, hitter)
    
    print(f"\n--- MATCHUP ANALYSIS ---")
    print(f"Tactical Edge Score: {matchup['edge_score']:+.2f} (positive = pitcher advantage)")
    print(f"Talent Gap: {matchup['talent_gap']:+.2f}")
    print(f"Combined Score: {matchup['combined_score']:+.2f}")
    print(f"Hitter Advantage: {matchup['hitter_advantage']}")
    
    if matchup['reasons']:
        print(f"\nKey Factors:")
        for reason in matchup['reasons'][:5]:  # Show top 5 reasons
            print(f"  - {reason}")


def example_lineup_analysis():
    """Example: Analyze a pitcher against an entire 9-man lineup"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Pitcher vs 9-Man Lineup Analysis")
    print("=" * 60)
    
    # Create database connection
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    # Get a pitcher
    pitcher_df = get_pitcher_archetype(engine, pitcher_name="Spencer Strider")
    if pitcher_df.empty:
        print("Pitcher not found. Using first available pitcher.")
        pitcher_df = get_pitcher_archetype(engine)
    
    pitcher = pitcher_df.iloc[0].to_dict()
    print(f"\nPitcher: {pitcher['full_name']} ({pitcher.get('hand', 'N/A')}HP)")
    print(f"  Grade: {pitcher.get('overall_grade', 'N/A')}")
    print(f"  Archetype: {pitcher.get('pitcher_archetype_label', 'N/A')}")
    
    # Get 9 hitters (in a real scenario, you'd filter by team)
    all_hitters = get_hitter_archetypes(engine)
    
    if len(all_hitters) < 9:
        print(f"Error: Not enough hitters in database ({len(all_hitters)} found)")
        return
    
    # Sample 9 hitters (in production, you'd use actual lineup)
    lineup = all_hitters.sample(9)
    
    print(f"\nOpposing Lineup ({len(lineup)} hitters):")
    for i, (_, hitter) in enumerate(lineup.iterrows(), 1):
        print(f"  {i}. {hitter['full_name']} ({hitter.get('hand', 'N/A')}HB) - {hitter.get('overall_grade', 'N/A')}")
    
    # Analyze lineup performance
    lineup_analysis = predict_lineup_performance(pitcher, lineup)
    
    print(f"\n--- LINEUP MATCHUP ANALYSIS ---")
    print("\nSorted by Hitter Advantage (best hitter matchups first):")
    for i, (_, row) in enumerate(lineup_analysis.iterrows(), 1):
        advantage = "HITTER" if row['hitter_advantage'] else "PITCHER"
        print(f"{i}. {row['hitter_name']}: {advantage} advantage (Score: {row['combined_score']:+.2f})")


def example_game_prediction():
    """Example: Predict game outcome based on pitcher vs lineup"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Game Outcome Prediction")
    print("=" * 60)
    
    # Create database connection
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    # Get a pitcher
    pitcher_df = get_pitcher_archetype(engine)
    if pitcher_df.empty:
        print("Error: No pitchers found in database")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    
    # Get 9 hitters for lineup
    all_hitters = get_hitter_archetypes(engine)
    if len(all_hitters) < 9:
        print(f"Error: Not enough hitters in database ({len(all_hitters)} found)")
        return
    
    lineup = all_hitters.sample(9)
    
    # Predict game outcome
    prediction = predict_game_outcome(pitcher, lineup)
    
    # Generate and print summary
    summary = analyze_matchup_summary(pitcher, lineup)
    print(summary)
    
    # Show detailed lineup analysis
    print("\n--- DETAILED LINEUP BREAKDOWN ---")
    for i, (_, row) in enumerate(prediction['lineup_analysis'].iterrows(), 1):
        print(f"\n{i}. {row['hitter_name']} ({row['hitter_grade']})")
        print(f"   Combined Score: {row['combined_score']:+.2f}")
        print(f"   Tactical Edge: {row['edge_score']:+.2f}")
        print(f"   Talent Gap: {row['talent_gap']:+.2f}")
        if row['reasons']:
            print(f"   Key Factors: {' | '.join(row['reasons'][:3])}")


def example_find_best_matchups():
    """Example: Find hitters who match up best against a specific pitcher"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Find Best Hitter Matchups vs Pitcher")
    print("=" * 60)
    
    # Create database connection
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    # Get a pitcher
    pitcher_df = get_pitcher_archetype(engine)
    if pitcher_df.empty:
        print("Error: No pitchers found in database")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    print(f"\nAnalyzing matchups vs: {pitcher['full_name']}")
    print(f"  Grade: {pitcher.get('overall_grade', 'N/A')}")
    print(f"  Attack Profile: {pitcher.get('attack_profile', 'N/A')}")
    
    # Get all hitters
    all_hitters = get_hitter_archetypes(engine)
    print(f"\nAnalyzing {len(all_hitters)} hitters...")
    
    # Analyze all matchups
    all_matchups = predict_lineup_performance(pitcher, all_hitters)
    
    # Get top 10 best hitter matchups (lowest combined_score = best for hitter)
    top_matchups = all_matchups.head(10)
    
    print(f"\n--- TOP 10 BEST HITTER MATCHUPS vs {pitcher['full_name']} ---")
    for i, (_, row) in enumerate(top_matchups.iterrows(), 1):
        print(f"{i}. {row['hitter_name']} ({row['hitter_grade']})")
        print(f"   Advantage Score: {row['combined_score']:+.2f} (negative = hitter advantage)")
        if row['reasons']:
            print(f"   Key Factors: {' | '.join(row['reasons'][:2])}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BASEBALL MATCHUP PREDICTION EXAMPLES")
    print("=" * 60)
    
    try:
        # Run examples
        example_individual_matchup()
        example_lineup_analysis()
        example_game_prediction()
        example_find_best_matchups()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()

