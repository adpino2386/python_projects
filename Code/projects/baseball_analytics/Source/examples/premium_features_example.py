"""
Premium Features Examples
=========================

This script demonstrates the premium features added to the matchup predictor:
- Lineup optimization
- Recent form adjustments
- Pitcher comparisons
- Situational analysis
- Game simulation
- Start/sit recommendations
- Visualization data preparation
- Matchup value calculations
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
    optimize_lineup_order,
    get_recent_form,
    adjust_for_recent_form,
    compare_pitchers_vs_lineup,
    analyze_situational_matchup,
    simulate_game,
    get_start_sit_recommendations,
    prepare_visualization_data,
    calculate_matchup_value
)
from dotenv import load_dotenv
import pandas as pd


def example_lineup_optimization():
    """Example: Optimize batting order based on matchups"""
    print("=" * 70)
    print("FEATURE 8: Lineup Optimization")
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
    print(f"\nOriginal Lineup Order:")
    for i, (_, hitter) in enumerate(lineup.iterrows(), 1):
        print(f"  {i}. {hitter['full_name']} ({hitter.get('overall_grade', 'C')})")
    
    # Optimize lineup
    optimized = optimize_lineup_order(pitcher, lineup)
    
    print(f"\n📋 Optimized Lineup Order:")
    for _, row in optimized.iterrows():
        advantage = "HITTER" if row['hitter_advantage'] else "PITCHER"
        print(f"  {int(row['suggested_order'])}. {row['hitter_name']} ({row['hitter_grade']})")
        print(f"     Score: {row['combined_score']:+.2f} ({advantage} advantage)")
        print(f"     {row['order_reason']}")


def example_recent_form():
    """Example: Adjust predictions based on recent form"""
    print("\n" + "=" * 70)
    print("FEATURE 9: Recent Form Adjustments")
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
    
    # Get base prediction
    base_prediction = predict_game_outcome(pitcher, lineup)
    
    print(f"\nBase Prediction:")
    print(f"  Win Probability: {base_prediction['win_probability']}%")
    print(f"  Pitcher Advantage: {base_prediction['pitcher_advantage']:+.2f}")
    
    # Get recent form
    pitcher_id = pitcher.get('pitcher')
    pitcher_form = None
    if pitcher_id:
        pitcher_form = get_recent_form(engine, pitcher_id, 'pitcher', days=30)
    
    hitter_forms = []
    for _, hitter in lineup.iterrows():
        hitter_id = hitter.get('batter')
        if hitter_id:
            form = get_recent_form(engine, hitter_id, 'hitter', days=30)
            hitter_forms.append(form)
        else:
            hitter_forms.append(None)
    
    # Adjust for form
    if pitcher_form or any(hitter_forms):
        adjusted = adjust_for_recent_form(base_prediction, pitcher_form, hitter_forms)
        
        print(f"\n📊 Form-Adjusted Prediction:")
        print(f"  Original Win Probability: {adjusted['original_win_probability']}%")
        print(f"  Adjusted Win Probability: {adjusted['adjusted_win_probability']}%")
        print(f"  Change: {adjusted['adjusted_win_probability'] - adjusted['original_win_probability']:+.1f}%")
        
        if adjusted.get('form_adjustments'):
            print(f"\n  Form Adjustments:")
            for adj in adjusted['form_adjustments']:
                print(f"    - {adj}")
    else:
        print("\n  No recent form data available")


def example_pitcher_comparison():
    """Example: Compare multiple pitchers vs same lineup"""
    print("\n" + "=" * 70)
    print("FEATURE 10: Pitcher Comparison")
    print("=" * 70)
    
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    all_pitchers = get_pitcher_archetype(engine)
    all_hitters = get_hitter_archetypes(engine)
    
    if len(all_pitchers) < 3 or len(all_hitters) < 9:
        print("Error: Insufficient data")
        return
    
    # Get 3 pitchers to compare
    pitcher_ids = all_pitchers.head(3)['pitcher'].tolist()
    lineup = all_hitters.sample(9)
    
    print(f"\nComparing {len(pitcher_ids)} pitchers vs same lineup:")
    for _, hitter in lineup.iterrows():
        print(f"  - {hitter['full_name']}")
    
    # Compare
    comparison = compare_pitchers_vs_lineup(engine, pitcher_ids, lineup)
    
    if not comparison.empty:
        print(f"\n🏆 Pitcher Comparison Results:")
        print(f"\n{'Pitcher':<25} {'Win Prob':<12} {'Exp Runs':<12} {'Exp K':<10} {'Confidence':<12}")
        print("-" * 80)
        for _, row in comparison.iterrows():
            print(f"{row['pitcher_name']:<25} {row['win_probability']:>6.1f}%     "
                  f"{row['expected_runs']:>6.2f}      {row['expected_strikeouts']:>6.1f}    "
                  f"{row['confidence']:>6.1f}%")


def example_situational_analysis():
    """Example: Analyze matchups in specific situations"""
    print("\n" + "=" * 70)
    print("FEATURE 11: Situational Matchup Analysis")
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
    
    print(f"\nPitcher: {pitcher['full_name']}")
    print(f"Hitter: {hitter['full_name']}")
    
    # Analyze different situations
    situations = ['all', 'clutch', 'two_strikes']
    
    for situation in situations:
        analysis = analyze_situational_matchup(pitcher, hitter, situation)
        
        print(f"\n📊 {situation.upper().replace('_', ' ')} Situation:")
        print(f"  Base Score: {analysis['base_matchup']['combined_score']:+.2f}")
        print(f"  Situational Score: {analysis['situational_score']:+.2f}")
        print(f"  Total Adjustment: {analysis['total_adjustment']:+.2f}")
        
        if analysis['situational_adjustments']:
            for sit_type, adj_data in analysis['situational_adjustments'].items():
                print(f"    {sit_type}: {adj_data['adjustment']:+.2f} - {adj_data['reason']}")


def example_game_simulation():
    """Example: Monte Carlo simulation of game outcomes"""
    print("\n" + "=" * 70)
    print("FEATURE 12: Game Simulation")
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
    
    print(f"\nSimulating game:")
    print(f"  Pitcher: {pitcher['full_name']}")
    print(f"  Opposing Lineup: {len(lineup)} hitters")
    print(f"  Simulations: 1000")
    
    simulation = simulate_game(pitcher, lineup, n_simulations=1000)
    
    print(f"\n🎲 Simulation Results:")
    print(f"  Simulated Win Probability: {simulation['simulated_win_probability']}%")
    print(f"  Base Win Probability: {simulation['base_win_probability']}%")
    print(f"  Average Runs Allowed: {simulation['avg_runs_allowed']}")
    print(f"  Average Strikeouts: {simulation['avg_strikeouts']}")
    print(f"\n  Runs Allowed Distribution:")
    dist = simulation['runs_allowed_distribution']
    print(f"    Min: {dist['min']}, Max: {dist['max']}")
    print(f"    Median: {dist['median']}")
    print(f"    25th-75th Percentile: {dist['p25']}-{dist['p75']}")


def example_start_sit_recommendations():
    """Example: Get start/sit recommendations"""
    print("\n" + "=" * 70)
    print("FEATURE 13: Start/Sit Recommendations")
    print("=" * 70)
    
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    pitcher_df = get_pitcher_archetype(engine)
    all_hitters = get_hitter_archetypes(engine)
    
    if pitcher_df.empty or len(all_hitters) < 12:
        print("Error: Need at least 12 hitters for recommendations")
        return
    
    pitcher = pitcher_df.iloc[0].to_dict()
    available_hitters = all_hitters.sample(12)  # More than 9
    
    print(f"\nPitcher: {pitcher['full_name']}")
    print(f"Available Hitters: {len(available_hitters)}")
    print(f"Lineup Size: 9")
    
    recommendations = get_start_sit_recommendations(pitcher, available_hitters, lineup_size=9)
    
    print(f"\n✅ START (Top Matchups):")
    for i, hitter in enumerate(recommendations['start'][:5], 1):  # Show top 5
        advantage = "HITTER" if hitter['hitter_advantage'] else "PITCHER"
        print(f"  {i}. {hitter['hitter_name']} ({hitter['hitter_grade']})")
        print(f"     Score: {hitter['combined_score']:+.2f} ({advantage} advantage)")
    
    print(f"\n❌ SIT (Worst Matchups):")
    for i, hitter in enumerate(recommendations['sit'][:3], 1):  # Show bottom 3
        advantage = "HITTER" if hitter['hitter_advantage'] else "PITCHER"
        print(f"  {i}. {hitter['hitter_name']} ({hitter['hitter_grade']})")
        print(f"     Score: {hitter['combined_score']:+.2f} ({advantage} advantage)")


def example_visualization_data():
    """Example: Prepare data for visualization"""
    print("\n" + "=" * 70)
    print("FEATURE 14: Visualization Data Preparation")
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
    
    prediction = predict_game_outcome(pitcher, lineup)
    viz_data = prepare_visualization_data(prediction)
    
    print(f"\n📊 Visualization Data Prepared:")
    print(f"  Win Probability: {viz_data['win_probability']}%")
    print(f"  Pitcher Advantage: {viz_data['pitcher_advantage']:+.2f}")
    print(f"\n  Matchup Scores:")
    for i, (hitter, score) in enumerate(zip(viz_data['matchup_scores']['hitters'][:5], 
                                            viz_data['matchup_scores']['scores'][:5]), 1):
        print(f"    {i}. {hitter}: {score:+.2f}")
    print(f"\n  Grade Distribution: {viz_data['grade_distribution']['grades']}")
    print(f"\n  Top Threats: {', '.join(viz_data['threat_analysis']['top_threats'][:3])}")


def example_matchup_value():
    """Example: Calculate matchup value for DFS/betting"""
    print("\n" + "=" * 70)
    print("FEATURE 15: Matchup Value Calculation")
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
    
    print(f"\nPitcher: {pitcher['full_name']}")
    print(f"Hitter: {hitter['full_name']}")
    
    # Calculate value without context
    value = calculate_matchup_value(pitcher, hitter)
    
    print(f"\n💰 Matchup Value:")
    print(f"  Hitter Value: {value['hitter_value']}/100")
    print(f"  Pitcher Value: {value['pitcher_value']}/100")
    print(f"  Matchup Quality: {value['matchup_quality']}")
    print(f"  Recommendation: {value['recommendation']}")
    
    # Calculate with context (e.g., DFS salary)
    context = {
        'hitter_salary': 3500,
        'avg_salary': 4500
    }
    value_with_context = calculate_matchup_value(pitcher, hitter, context)
    
    print(f"\n  With Context (Salary):")
    print(f"    Recommendation: {value_with_context['recommendation']}")
    if value_with_context.get('value_play'):
        print(f"    ⭐ VALUE PLAY DETECTED!")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PREMIUM MATCHUP PREDICTION FEATURES")
    print("=" * 70)
    
    try:
        example_lineup_optimization()
        example_recent_form()
        example_pitcher_comparison()
        example_situational_analysis()
        example_game_simulation()
        example_start_sit_recommendations()
        example_visualization_data()
        example_matchup_value()
        
        print("\n" + "=" * 70)
        print("All premium feature examples completed!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()

