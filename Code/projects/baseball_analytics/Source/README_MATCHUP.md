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

## Advanced Features

The module now includes several advanced features:

### 1. Historical Matchup Data
```python
from utils.matchup_predictor import get_historical_matchup

historical = get_historical_matchup(engine, pitcher_id, hitter_id)
# Returns: wOBA, whiff rate, hits, HRs, strikeouts, etc.
```

### 2. Expected Statistics Prediction
```python
from utils.matchup_predictor import predict_expected_statistics

expected = predict_expected_statistics(pitcher, lineup)
# Returns: expected runs, hits, strikeouts, WHIP, ERA, etc.
```

### 3. Matchup Confidence Scoring
```python
from utils.matchup_predictor import calculate_matchup_confidence

confidence = calculate_matchup_confidence(pitcher, hitter)
# Returns: 0-100 confidence score based on data quality and sample size
```

### 4. Archetype Compatibility Analysis
```python
from utils.matchup_predictor import get_archetype_compatibility

compatibility = get_archetype_compatibility(pitcher_archetype, hitter_archetype)
# Returns: compatibility score and reasoning
```

### 5. Team-Level Matchup Analysis
```python
from utils.matchup_predictor import analyze_team_matchup

team_analysis = analyze_team_matchup(pitcher, opposing_lineup, own_lineup)
# Returns: Full team analysis including lineup quality comparisons
```

### 6. Bulk Predictions
```python
from utils.matchup_predictor import predict_bulk_matchups

matchups = [
    {'pitcher_name': 'Gerrit Cole', 'hitter_names': [...]},
    # ... more matchups
]
results = predict_bulk_matchups(engine, matchups)
```

### 7. Enhanced Matchups with History
```python
from utils.matchup_predictor import enhance_matchup_with_history

matchup = predict_individual_matchup(pitcher, hitter)
enhanced = enhance_matchup_with_history(engine, pitcher, hitter, matchup)
# Adjusts prediction based on actual historical performance
```

See `examples/advanced_features_example.py` for detailed usage examples of all advanced features.

### 8. Lineup Optimization
```python
from utils.matchup_predictor import optimize_lineup_order

optimized = optimize_lineup_order(pitcher, lineup)
# Returns: Suggested batting order (1-9) based on matchup strengths
```

### 9. Recent Form Adjustments
```python
from utils.matchup_predictor import get_recent_form, adjust_for_recent_form

pitcher_form = get_recent_form(engine, pitcher_id, 'pitcher', days=30)
adjusted = adjust_for_recent_form(prediction, pitcher_form, hitter_forms)
# Adjusts predictions based on recent performance
```

### 10. Pitcher Comparison
```python
from utils.matchup_predictor import compare_pitchers_vs_lineup

comparison = compare_pitchers_vs_lineup(engine, [pitcher_id1, pitcher_id2], lineup)
# Compare multiple pitchers against the same lineup
```

### 11. Situational Analysis
```python
from utils.matchup_predictor import analyze_situational_matchup

analysis = analyze_situational_matchup(pitcher, hitter, situation='clutch')
# Analyze matchups in specific game situations (clutch, two-strikes, etc.)
```

### 12. Game Simulation
```python
from utils.matchup_predictor import simulate_game

simulation = simulate_game(pitcher, lineup, n_simulations=1000)
# Monte Carlo simulation of game outcomes
```

### 13. Start/Sit Recommendations
```python
from utils.matchup_predictor import get_start_sit_recommendations

recommendations = get_start_sit_recommendations(pitcher, available_hitters, lineup_size=9)
# Recommend which hitters to start or sit
```

### 14. Visualization Data
```python
from utils.matchup_predictor import prepare_visualization_data

viz_data = prepare_visualization_data(prediction)
# Prepare data formatted for charts and visualizations
```

### 15. Matchup Value Calculation
```python
from utils.matchup_predictor import calculate_matchup_value

value = calculate_matchup_value(pitcher, hitter, context={'hitter_salary': 3500})
# Calculate matchup value for DFS, betting, etc.
```

See `examples/premium_features_example.py` for detailed usage examples of all premium features.

## Future Enhancements

Potential improvements for the web app:
- Park factor adjustments
- Weather condition integration
- Lineup optimization suggestions
- Machine learning model integration for win probability refinement
- Real-time game tracking and live prediction updates

