"""
Daily Game Predictions
======================

This script demonstrates how to use the matchup predictor to predict outcomes
for all games on a given day. This is the foundation for a daily predictions feature.

Note: This example uses sample data. In production, you would integrate with
a schedule API or database table containing game schedules.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date

# Add the Source directory to the path
source_dir = Path(__file__).parent.parent
sys.path.insert(0, str(source_dir))

from utils.connection_engine import create_connection_postgresql
from utils.matchup_predictor import (
    get_pitcher_archetype,
    get_hitter_archetypes,
    predict_game_outcome,
    analyze_matchup_summary
)
from dotenv import load_dotenv
import pandas as pd


def predict_daily_games(prediction_date: date = None, sample_size: int = 5):
    """
    Predict outcomes for all games on a given date.
    
    This is a template function. In production, you would:
    1. Query a schedule API/database to get games for the date
    2. Get starting pitchers for each game
    3. Get lineups for each team
    4. Run predictions for each matchup
    
    Args:
        prediction_date: Date to predict games for (defaults to today)
        sample_size: Number of sample matchups to generate (for demo purposes)
    
    Returns:
        List of prediction dictionaries
    """
    if prediction_date is None:
        prediction_date = date.today()
    
    print(f"\n{'=' * 70}")
    print(f"DAILY GAME PREDICTIONS - {prediction_date.strftime('%B %d, %Y')}")
    print(f"{'=' * 70}\n")
    
    # Create database connection
    load_dotenv(dotenv_path="utils/.env")
    engine = create_connection_postgresql()
    
    # Get all available pitchers
    all_pitchers = get_pitcher_archetype(engine)
    if all_pitchers.empty:
        print("Error: No pitchers found in database")
        return []
    
    # Get all available hitters
    all_hitters = get_hitter_archetypes(engine)
    if len(all_hitters) < 9:
        print(f"Error: Not enough hitters in database ({len(all_hitters)} found)")
        return []
    
    print(f"Loaded {len(all_pitchers)} pitchers and {len(all_hitters)} hitters from database\n")
    
    predictions = []
    
    # Generate sample matchups (in production, this would come from schedule)
    for i in range(min(sample_size, len(all_pitchers))):
        pitcher = all_pitchers.iloc[i].to_dict()
        
        # Sample a lineup (in production, use actual team lineups)
        lineup = all_hitters.sample(9).reset_index(drop=True)
        
        print(f"{'─' * 70}")
        print(f"GAME {i + 1}: {pitcher['full_name']} vs Opposing Lineup")
        print(f"{'─' * 70}")
        
        try:
            # Predict game outcome
            prediction = predict_game_outcome(pitcher, lineup)
            
            # Store prediction
            game_prediction = {
                'date': prediction_date,
                'pitcher_name': pitcher['full_name'],
                'pitcher_team': 'TBD',  # Would come from schedule data
                'opponent_team': 'TBD',  # Would come from schedule data
                'win_probability': prediction['win_probability'],
                'pitcher_advantage': prediction['pitcher_advantage'],
                'top_threats': [t['name'] for t in prediction['top_threats']],
                'easy_outs': [e['name'] for e in prediction['easy_outs']],
                'full_prediction': prediction  # Store full details
            }
            predictions.append(game_prediction)
            
            # Print summary
            print(f"Win Probability: {prediction['win_probability']}%")
            print(f"Overall Advantage: {prediction['pitcher_advantage']:+.2f}")
            
            if prediction['top_threats']:
                print(f"\nTop Hitting Threats:")
                for threat in prediction['top_threats']:
                    print(f"  • {threat['name']} ({threat['grade']})")
            
            if prediction['easy_outs']:
                print(f"\nPitcher Advantage Matchups:")
                for out in reversed(prediction['easy_outs']):
                    print(f"  • {out['name']} ({out['grade']})")
            
            print()
            
        except Exception as e:
            print(f"Error predicting game {i + 1}: {e}\n")
            continue
    
    return predictions


def generate_daily_report(predictions: list):
    """
    Generate a summary report of all daily predictions.
    
    Args:
        predictions: List of prediction dictionaries
    """
    if not predictions:
        print("No predictions to report.")
        return
    
    print(f"\n{'=' * 70}")
    print("DAILY PREDICTIONS SUMMARY")
    print(f"{'=' * 70}\n")
    
    # Sort by win probability (highest first)
    sorted_predictions = sorted(predictions, key=lambda x: x['win_probability'], reverse=True)
    
    print(f"{'Pitcher':<25} {'Win Prob':<12} {'Advantage':<12}")
    print(f"{'-' * 70}")
    
    for pred in sorted_predictions:
        print(f"{pred['pitcher_name']:<25} {pred['win_probability']:>6.1f}%     {pred['pitcher_advantage']:>+8.2f}")
    
    # Statistics
    avg_win_prob = sum(p['win_probability'] for p in predictions) / len(predictions)
    favorite_count = sum(1 for p in predictions if p['win_probability'] > 50)
    
    print(f"\n{'─' * 70}")
    print(f"Total Games: {len(predictions)}")
    print(f"Average Win Probability: {avg_win_prob:.1f}%")
    print(f"Favorites (Win Prob > 50%): {favorite_count}/{len(predictions)}")
    print(f"{'=' * 70}\n")


def export_predictions_to_json(predictions: list, filename: str = None):
    """
    Export predictions to JSON format (useful for web app API).
    
    Args:
        predictions: List of prediction dictionaries
        filename: Output filename (optional)
    """
    import json
    
    if filename is None:
        filename = f"predictions_{datetime.now().strftime('%Y%m%d')}.json"
    
    # Convert to JSON-serializable format (remove DataFrame objects)
    export_data = []
    for pred in predictions:
        export_pred = {
            'date': pred['date'].isoformat() if isinstance(pred['date'], date) else str(pred['date']),
            'pitcher_name': pred['pitcher_name'],
            'pitcher_team': pred['pitcher_team'],
            'opponent_team': pred['opponent_team'],
            'win_probability': pred['win_probability'],
            'pitcher_advantage': pred['pitcher_advantage'],
            'top_threats': pred['top_threats'],
            'easy_outs': pred['easy_outs']
        }
        export_data.append(export_pred)
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Predictions exported to {filename}")
    return filename


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DAILY GAME PREDICTIONS DEMO")
    print("=" * 70)
    print("\nNote: This is a demo using sample data.")
    print("In production, you would integrate with a schedule API/database.\n")
    
    try:
        # Predict games for today (or use a specific date)
        # predictions = predict_daily_games(date(2024, 7, 15), sample_size=5)
        predictions = predict_daily_games(sample_size=5)
        
        # Generate summary report
        if predictions:
            generate_daily_report(predictions)
            
            # Optional: Export to JSON
            # export_predictions_to_json(predictions)
        
        print("\n" + "=" * 70)
        print("Daily predictions completed!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\nError running daily predictions: {e}")
        import traceback
        traceback.print_exc()

