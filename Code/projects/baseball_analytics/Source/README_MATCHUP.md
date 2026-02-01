# Matchup Prediction Module

This module provides a comprehensive system for analyzing pitcher vs hitter matchups and predicting game outcomes based on player archetypes.

## Overview

The matchup prediction system uses the archetype data from `dim_pitcher_archetypes` and `dim_hitter_archetypes` tables to:
1. Analyze individual pitcher vs hitter matchups
2. Evaluate how a pitcher matches up against an entire 9-man lineup
3. Predict game win probabilities
4. Identify which hitters have the best/worst matchups against a specific pitcher

## Key Features

### Matchup Factors Analyzed

1. **Path Geometry**: Pitcher attack profile (e.g., "NORTH-SOUTH (High Rise)") vs Hitter vertical profile (e.g., "HIGH-BALL HUNTER")
2. **Skill Clash**: Pitcher matchup role (e.g., "DOMINANT ACE") vs Hitter two-strike identity (e.g., "ELITE SPOILER")
3. **Platoon Logic**: Handedness matchups and neutrality percentages
4. **Pitch Type Matchups**: Pitcher's primary arsenal (fastball/breaking/offspeed) vs hitter's strengths/weaknesses

### Core Functions

- `calculate_matchup_edge()`: Calculates tactical edge score for pitcher vs hitter
- `predict_individual_matchup()`: Full analysis of a single matchup
- `predict_lineup_performance()`: Analyzes all 9 hitters in a lineup
- `predict_game_outcome()`: Predicts win probability and provides detailed analysis
- `get_pitcher_archetype()`: Loads pitcher data from database
- `get_hitter_archetypes()`: Loads hitter data from database
- `analyze_matchup_summary()`: Generates human-readable summary

## Quick Start

```python
from utils.connection_engine import create_connection_postgresql
from utils.matchup_predictor import (
    get_pitcher_archetype,
    get_hitter_archetypes,
    predict_game_outcome,
    analyze_matchup_summary
)
from dotenv import load_dotenv

# Connect to database
load_dotenv(dotenv_path="utils/.env")
engine = create_connection_postgresql()

# Get pitcher
pitcher_df = get_pitcher_archetype(engine, pitcher_name="Gerrit Cole")
pitcher = pitcher_df.iloc[0].to_dict()

# Get lineup (9 hitters)
hitter_df = get_hitter_archetypes(engine, hitter_names=[
    "Mike Trout", "Aaron Judge", "Vladimir Guerrero Jr.",
    # ... 6 more hitters
])
lineup = hitter_df.head(9)

# Predict game outcome
prediction = predict_game_outcome(pitcher, lineup)

print(f"Win Probability: {prediction['win_probability']}%")
print(f"Pitcher Advantage: {prediction['pitcher_advantage']}")

# Get summary
summary = analyze_matchup_summary(pitcher, lineup)
print(summary)
```

## Example Usage

See `examples/matchup_example.py` for detailed examples including:
- Individual matchup analysis
- Lineup analysis
- Game outcome prediction
- Finding best hitter matchups vs a pitcher

Run the examples:
```bash
cd Code/projects/baseball_analytics/Source
python examples/matchup_example.py
```

## Understanding the Scores

### Edge Score
- **Positive values**: Favor the pitcher (tactical advantage)
- **Negative values**: Favor the hitter
- Range: Typically -5 to +5

### Combined Score
- Combines tactical edge and talent gap
- Formula: `(talent_gap * 1.5) + edge_score`
- Used to determine overall matchup advantage

### Win Probability
- Converted from average combined score using sigmoid function
- 0 advantage = 50% win probability
- +2 advantage ≈ 65% win probability
- -2 advantage ≈ 35% win probability

## Integration with Web App

This module is designed to be the backend foundation for a web application. Suggested integration:

1. **API Endpoints** (Flask/FastAPI):
   - `/api/matchup/pitcher/{pitcher_id}/lineup/{lineup_ids}`: Get matchup analysis
   - `/api/matchup/pitcher/{pitcher_id}/predict`: Predict game outcome
   - `/api/matchup/best-hitters/{pitcher_id}`: Find best hitter matchups

2. **Data Format**:
   - Functions return dictionaries/DataFrames that can be easily serialized to JSON
   - Use `analyze_matchup_summary()` for human-readable text output

3. **Caching**:
   - Consider caching archetype data (doesn't change frequently)
   - Cache matchup calculations for performance

## Future Enhancements

Potential improvements for the web app:
- Historical matchup data integration
- Team-level aggregation
- Daily game predictions for all MLB games
- Advanced metrics (expected runs, strikeout probability, etc.)
- Machine learning model integration for win probability refinement

