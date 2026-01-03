"""
Matchup Prediction Module
========================

This module provides functions to analyze pitcher vs hitter matchups and predict
game outcomes based on player archetypes and performance metrics.

Main Functions:
- calculate_matchup_edge: Analyzes individual hitter vs pitcher matchup
- predict_lineup_performance: Analyzes entire lineup vs pitcher
- predict_game_outcome: Predicts win probability for pitcher's team
- get_archetypes_from_db: Loads archetype data from database
"""

import pandas as pd
import numpy as np
from sqlalchemy.engine import Engine
from sqlalchemy import text
from typing import Dict, List, Tuple, Optional


# Matchup Matrix: Defines tactical advantages/disadvantages
# Positive values favor the pitcher, negative values favor the hitter
MATCHUP_MATRIX = {
    "path_geometry": {
        # Pitcher attack profile vs Hitter vertical profile
        ("NORTH-SOUTH (High Rise)", "LOW-BALL GOLFER"): 1.5,  # Pitcher advantage
        ("NORTH-SOUTH (High Rise)", "HIGH-BALL HUNTER"): -1.5,  # Hitter advantage
        ("EAST-WEST (Heavy Run)", "DOWNWARD (Groundball)"): 2.0,  # Strong pitcher advantage
        ("EAST-WEST (Heavy Run)", "LEVEL (Line Drive)"): -1.0,  # Hitter advantage
        ("DECEPTIVE (Tunneling)", "UPPERCUT (Flyball)"): 1.0,  # Pitcher advantage
        ("LATERAL (Sweeper/Slide)", "ALL-ZONE THREAT"): 0.5,  # Slight pitcher advantage
    },
    "skill_clash": {
        # Pitcher matchup role vs Hitter two-strike identity
        ("DOMINANT ACE", "FREE SWINGER"): 2.0,  # Strong pitcher advantage
        ("PITCH TO CONTACT SURGEON", "ELITE SPOILER"): -2.5,  # Strong hitter advantage
        ("POWER ARMS (High Risk)", "FREE SWINGER"): 1.5,  # Pitcher advantage
        ("ROTATION STABILIZER", "STANDARD"): 0.5,  # Slight pitcher advantage
        ("POWER ARMS (High Risk)", "ELITE SPOILER"): -1.0,  # Hitter advantage
    },
    "pitch_type": {
        # Based on pitcher's primary arsenal vs hitter's weakness
        # This is handled dynamically based on woba_vs_hard/break/offspeed
    }
}


def calculate_matchup_edge(pitcher: Dict, hitter: Dict) -> Tuple[float, List[str]]:
    """
    Calculate the tactical edge score for a pitcher vs hitter matchup.
    
    Positive scores favor the pitcher, negative scores favor the hitter.
    
    Args:
        pitcher: Dictionary containing pitcher archetype data (from dim_pitcher_archetypes)
        hitter: Dictionary containing hitter archetype data (from dim_hitter_archetypes)
    
    Returns:
        Tuple of (edge_score, reasons_list)
        - edge_score: Float representing the tactical advantage (-5 to +5 range typically)
        - reasons_list: List of strings explaining the matchup factors
    """
    edge_score = 0.0
    reasons = []
    
    # 1. GEOMETRY CHECK: Pitcher attack profile vs Hitter vertical profile
    pitcher_profile = pitcher.get('attack_profile', '')
    hitter_profile = hitter.get('vertical_profile', '')
    
    if pitcher_profile and hitter_profile:
        geo_key = (pitcher_profile, hitter_profile)
        if geo_key in MATCHUP_MATRIX["path_geometry"]:
            score = MATCHUP_MATRIX["path_geometry"][geo_key]
            edge_score += score
            reasons.append(f"Geometry ({pitcher_profile} vs {hitter_profile}): {score:+.1f}")
    
    # 2. SKILL CLASH CHECK: Pitcher role vs Hitter two-strike identity
    pitcher_role = pitcher.get('matchup_role', '')
    hitter_identity = hitter.get('two_strike_identity', '')
    
    if pitcher_role and hitter_identity:
        skill_key = (pitcher_role, hitter_identity)
        if skill_key in MATCHUP_MATRIX["skill_clash"]:
            score = MATCHUP_MATRIX["skill_clash"][skill_key]
            edge_score += score
            reasons.append(f"Skill Clash ({pitcher_role} vs {hitter_identity}): {score:+.1f}")
    
    # 3. PLATOON LOGIC: Using neutrality percentages
    pitcher_neutrality = pitcher.get('neutrality_pct', 50.0) or 50.0
    hitter_neutrality = hitter.get('neutrality_pct', 50.0) or 50.0  # Use percentile for consistency
    
    # If pitcher is matchup-proof (high neutrality), they gain edge
    if pitcher_neutrality > 75:
        edge_score += 1.0
        reasons.append(f"Pitcher Matchup-Proof (Neutrality: {pitcher_neutrality:.1f}%): +1.0")
    
    # Platoon split exploitation: same-handed matchup with weak hitter splits
    pitcher_hand = pitcher.get('hand', '')
    hitter_hand = hitter.get('hand', '')
    
    # If hitter has low neutrality (strong platoon splits) AND same-handed matchup, pitcher gains edge
    if hitter_neutrality < 40 and pitcher_hand == hitter_hand and pitcher_hand:
        edge_score += 1.5
        reasons.append(f"Platoon Advantage ({pitcher_hand}HP vs {hitter_hand}HB, Neutrality: {hitter_neutrality:.1f}%): +1.5")
    
    # 4. PITCH TYPE MATCHUPS: Analyze pitcher arsenal vs hitter weaknesses
    # Get pitcher's primary pitch types (based on usage percentages)
    ffour_usage = pitcher.get('ffour_usage', 0) or 0
    bb_usage = pitcher.get('bb_usage', 0) or 0
    offspeed_usage = pitcher.get('offspeed_usage', 0) or 0
    
    # Get hitter's wOBA vs different pitch types (as percentiles)
    hitter_woba_hard_pct = hitter.get('woba_hard_pct', 50.0) or 50.0
    hitter_woba_break_pct = hitter.get('woba_break_pct', 50.0) or 50.0
    hitter_woba_offspeed_pct = hitter.get('woba_offspeed_pct', 50.0) or 50.0
    
    # Calculate pitch type advantage
    # If pitcher throws mostly fastballs and hitter is weak vs hard, pitcher gains edge
    if ffour_usage > 40 and hitter_woba_hard_pct < 30:
        edge_score += 0.8
        reasons.append(f"Fastball vs Weakness (FF Usage: {ffour_usage:.1f}%, Hitter wOBA vs Hard: {hitter_woba_hard_pct:.1f}%ile): +0.8")
    elif ffour_usage > 40 and hitter_woba_hard_pct > 70:
        edge_score -= 0.8
        reasons.append(f"Fastball vs Strength (FF Usage: {ffour_usage:.1f}%, Hitter wOBA vs Hard: {hitter_woba_hard_pct:.1f}%ile): -0.8")
    
    if bb_usage > 30 and hitter_woba_break_pct < 30:
        edge_score += 0.8
        reasons.append(f"Breaking Ball vs Weakness (BB Usage: {bb_usage:.1f}%, Hitter wOBA vs Break: {hitter_woba_break_pct:.1f}%ile): +0.8")
    elif bb_usage > 30 and hitter_woba_break_pct > 70:
        edge_score -= 0.8
        reasons.append(f"Breaking Ball vs Strength (BB Usage: {bb_usage:.1f}%, Hitter wOBA vs Break: {hitter_woba_break_pct:.1f}%ile): -0.8")
    
    if offspeed_usage > 25 and hitter_woba_offspeed_pct < 30:
        edge_score += 0.8
        reasons.append(f"Offspeed vs Weakness (Offspeed Usage: {offspeed_usage:.1f}%, Hitter wOBA vs Offspeed: {hitter_woba_offspeed_pct:.1f}%ile): +0.8")
    elif offspeed_usage > 25 and hitter_woba_offspeed_pct > 70:
        edge_score -= 0.8
        reasons.append(f"Offspeed vs Strength (Offspeed Usage: {offspeed_usage:.1f}%, Hitter wOBA vs Offspeed: {hitter_woba_offspeed_pct:.1f}%ile): -0.8")
    
    return edge_score, reasons


def calculate_talent_gap(pitcher: Dict, hitter: Dict) -> float:
    """
    Calculate the talent gap between pitcher and hitter based on overall grades.
    
    Args:
        pitcher: Pitcher archetype data
        hitter: Hitter archetype data
    
    Returns:
        Float representing talent gap (positive = pitcher advantage)
    """
    grade_map = {'A+': 5, 'A': 4, 'B': 3, 'C': 2, 'D/F': 1}
    
    pitcher_grade = pitcher.get('overall_grade', 'C')
    hitter_grade = hitter.get('overall_grade', 'C')
    
    pitcher_quality = grade_map.get(pitcher_grade, 3)
    hitter_quality = grade_map.get(hitter_grade, 3)
    
    return pitcher_quality - hitter_quality


def predict_individual_matchup(pitcher: Dict, hitter: Dict) -> Dict:
    """
    Predict the outcome of an individual pitcher vs hitter matchup.
    
    Args:
        pitcher: Pitcher archetype data
        hitter: Hitter archetype data
    
    Returns:
        Dictionary containing:
        - edge_score: Tactical edge score
        - talent_gap: Talent gap score
        - combined_score: Combined matchup score
        - hitter_advantage: Boolean indicating if hitter has advantage
        - reasons: List of matchup factors
    """
    edge_score, reasons = calculate_matchup_edge(pitcher, hitter)
    talent_gap = calculate_talent_gap(pitcher, hitter)
    
    # Combine tactical edge and talent gap (talent weighted 1.5x)
    combined_score = (talent_gap * 1.5) + edge_score
    
    # Determine advantage (negative combined_score favors hitter)
    hitter_advantage = combined_score < 0
    
    return {
        'edge_score': edge_score,
        'talent_gap': talent_gap,
        'combined_score': combined_score,
        'hitter_advantage': hitter_advantage,
        'reasons': reasons,
        'hitter_name': hitter.get('full_name', 'Unknown'),
        'hitter_grade': hitter.get('overall_grade', 'C'),
        'pitcher_name': pitcher.get('full_name', 'Unknown'),
        'pitcher_grade': pitcher.get('overall_grade', 'C')
    }


def predict_lineup_performance(pitcher: Dict, lineup_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze how each hitter in a lineup matches up against a pitcher.
    
    Args:
        pitcher: Pitcher archetype data (single row as dict)
        lineup_df: DataFrame containing hitter archetype data (9 hitters)
    
    Returns:
        DataFrame with matchup analysis for each hitter, sorted by hitter advantage
    """
    matchup_results = []
    
    for _, hitter in lineup_df.iterrows():
        matchup = predict_individual_matchup(pitcher, hitter.to_dict())
        matchup_results.append(matchup)
    
    results_df = pd.DataFrame(matchup_results)
    
    # Sort by combined_score (ascending = best hitter matchups first)
    results_df = results_df.sort_values('combined_score', ascending=True)
    
    return results_df


def predict_game_outcome(pitcher: Dict, lineup_df: pd.DataFrame) -> Dict:
    """
    Predict the win probability for the pitcher's team based on lineup matchups.
    
    Args:
        pitcher: Pitcher archetype data
        lineup_df: DataFrame containing 9 hitter archetypes
    
    Returns:
        Dictionary containing:
        - win_probability: Win probability percentage (0-100)
        - pitcher_advantage: Overall advantage score
        - lineup_analysis: DataFrame with individual matchups
        - top_threats: List of hitters with best matchups vs pitcher
        - easy_outs: List of hitters with worst matchups vs pitcher
    """
    if len(lineup_df) != 9:
        raise ValueError(f"Lineup must contain exactly 9 hitters, got {len(lineup_df)}")
    
    lineup_analysis = predict_lineup_performance(pitcher, lineup_df)
    
    # Calculate average advantage across lineup
    avg_advantage = lineup_analysis['combined_score'].mean()
    
    # Convert to win probability using sigmoid function
    # 0 advantage = 50% win prob, +2 advantage ≈ 65% win prob, -2 advantage ≈ 35% win prob
    win_prob = 100 / (1 + np.exp(-0.3 * avg_advantage))
    
    # Get top threats (hitters with negative combined_score = hitter advantage)
    top_threats = lineup_analysis[lineup_analysis['hitter_advantage']].head(3)
    top_threats_list = [
        {
            'name': row['hitter_name'],
            'grade': row['hitter_grade'],
            'score': row['combined_score'],
            'reasons': row['reasons']
        }
        for _, row in top_threats.iterrows()
    ]
    
    # Get easy outs (hitters with positive combined_score = pitcher advantage)
    easy_outs = lineup_analysis[~lineup_analysis['hitter_advantage']].tail(3)
    easy_outs_list = [
        {
            'name': row['hitter_name'],
            'grade': row['hitter_grade'],
            'score': row['combined_score'],
            'reasons': row['reasons']
        }
        for _, row in easy_outs.iterrows()
    ]
    
    return {
        'win_probability': round(win_prob, 1),
        'pitcher_advantage': round(avg_advantage, 2),
        'lineup_analysis': lineup_analysis,
        'top_threats': top_threats_list,
        'easy_outs': easy_outs_list,
        'pitcher_name': pitcher.get('full_name', 'Unknown')
    }


def get_pitcher_archetype(engine: Engine, pitcher_name: Optional[str] = None, 
                          pitcher_id: Optional[int] = None) -> pd.DataFrame:
    """
    Get pitcher archetype data from database.
    
    Args:
        engine: SQLAlchemy engine
        pitcher_name: Pitcher name to search for (optional)
        pitcher_id: Pitcher MLBAM ID (optional)
    
    Returns:
        DataFrame with pitcher archetype data
    """
    if pitcher_id:
        query = text("SELECT * FROM dim_pitcher_archetypes WHERE pitcher = :pitcher_id")
        df = pd.read_sql(query, engine, params={'pitcher_id': pitcher_id})
    elif pitcher_name:
        query = text("SELECT * FROM dim_pitcher_archetypes WHERE full_name ILIKE :name")
        df = pd.read_sql(query, engine, params={'name': f'%{pitcher_name}%'})
    else:
        query = text("SELECT * FROM dim_pitcher_archetypes")
        df = pd.read_sql(query, engine)
    
    return df


def get_hitter_archetypes(engine: Engine, hitter_names: Optional[List[str]] = None,
                          hitter_ids: Optional[List[int]] = None,
                          team: Optional[str] = None) -> pd.DataFrame:
    """
    Get hitter archetype data from database.
    
    Args:
        engine: SQLAlchemy engine
        hitter_names: List of hitter names to search for (optional)
        hitter_ids: List of hitter MLBAM IDs (optional)
        team: Team abbreviation to filter by (optional, requires team data in DB)
    
    Returns:
        DataFrame with hitter archetype data
    """
    if hitter_ids:
        placeholders = ','.join([f':id{i}' for i in range(len(hitter_ids))])
        query = text(f"SELECT * FROM dim_hitter_archetypes WHERE batter IN ({placeholders})")
        params = {f'id{i}': hid for i, hid in enumerate(hitter_ids)}
        df = pd.read_sql(query, engine, params=params)
    elif hitter_names:
        # Use ILIKE for case-insensitive matching
        conditions = ' OR '.join([f"full_name ILIKE :name{i}" for i in range(len(hitter_names))])
        query = text(f"SELECT * FROM dim_hitter_archetypes WHERE {conditions}")
        params = {f'name{i}': f'%{name}%' for i, name in enumerate(hitter_names)}
        df = pd.read_sql(query, engine, params=params)
    else:
        query = text("SELECT * FROM dim_hitter_archetypes")
        df = pd.read_sql(query, engine)
    
    return df


def analyze_matchup_summary(pitcher: Dict, lineup_df: pd.DataFrame) -> str:
    """
    Generate a human-readable summary of the matchup analysis.
    
    Args:
        pitcher: Pitcher archetype data
        lineup_df: DataFrame with 9 hitter archetypes
    
    Returns:
        Formatted string summary
    """
    prediction = predict_game_outcome(pitcher, lineup_df)
    
    summary = f"--- 📊 MATCHUP ANALYSIS: {prediction['pitcher_name']} vs Opposing Lineup ---\n"
    summary += f"Projected Win Probability: {prediction['win_probability']}%\n"
    summary += f"Overall Advantage Score: {prediction['pitcher_advantage']:+.2f}\n\n"
    
    if prediction['top_threats']:
        summary += "🔥 TOP HITTING THREATS:\n"
        for threat in prediction['top_threats']:
            summary += f"  ⚠️ {threat['name']} ({threat['grade']}): Score {threat['score']:+.2f}\n"
            if threat['reasons']:
                summary += f"     Factors: {' | '.join(threat['reasons'][:3])}\n"
        summary += "\n"
    
    if prediction['easy_outs']:
        summary += "✅ PITCHER ADVANTAGE MATCHUPS:\n"
        for out in reversed(prediction['easy_outs']):  # Reverse to show best pitcher advantage first
            summary += f"  💎 {out['name']} ({out['grade']}): Score {out['score']:+.2f}\n"
            if out['reasons']:
                summary += f"     Factors: {' | '.join(out['reasons'][:3])}\n"
    
    return summary


# ============================================================================
# NEW FEATURES
# ============================================================================

def get_historical_matchup(engine: Engine, pitcher_id: int, hitter_id: int, 
                        min_pitches: int = 10) -> Optional[Dict]:
    """
    Get historical matchup data between a specific pitcher and hitter.
    
    Args:
        engine: SQLAlchemy engine
        pitcher_id: Pitcher MLBAM ID
        hitter_id: Hitter MLBAM ID
        min_pitches: Minimum number of pitches required to return data
    
    Returns:
        Dictionary with historical matchup stats, or None if insufficient data
    """
    query = text("""
        SELECT 
            COUNT(*) as total_pitches,
            COUNT(CASE WHEN type = 'X' THEN 1 END) as balls_in_play,
            AVG(woba_value) as avg_woba,
            SUM(CASE WHEN description IN ('swinging_strike', 'swinging_strike_blocked') THEN 1 ELSE 0 END)::float / 
                NULLIF(COUNT(CASE WHEN description IN ('swinging_strike', 'foul', 'hit_into_play', 'swinging_strike_blocked') THEN 1 END), 0) as whiff_rate,
            SUM(CASE WHEN events IN ('single', 'double', 'triple', 'home_run') THEN 1 ELSE 0 END) as hits,
            SUM(CASE WHEN events = 'home_run' THEN 1 ELSE 0 END) as home_runs,
            SUM(CASE WHEN events = 'strikeout' THEN 1 ELSE 0 END) as strikeouts,
            SUM(CASE WHEN events = 'walk' THEN 1 ELSE 0 END) as walks,
            AVG(launch_speed) as avg_exit_velocity,
            AVG(launch_angle) as avg_launch_angle,
            SUM(CASE WHEN launch_speed_angle = 6 THEN 1 ELSE 0 END) as barrels
        FROM fact_statcast_pitches
        WHERE pitcher = :pitcher_id AND batter = :hitter_id
    """)
    
    df = pd.read_sql(query, engine, params={'pitcher_id': pitcher_id, 'hitter_id': hitter_id})
    
    if df.empty or df.iloc[0]['total_pitches'] < min_pitches:
        return None
    
    row = df.iloc[0]
    
    # Calculate batting average (simplified - would need more detailed event data)
    at_bats = row['total_pitches'] - row['walks'] if row['walks'] else row['total_pitches']
    batting_avg = row['hits'] / at_bats if at_bats > 0 else 0
    
    return {
        'total_pitches': int(row['total_pitches']),
        'balls_in_play': int(row['balls_in_play']),
        'avg_woba': float(row['avg_woba']) if row['avg_woba'] else 0.0,
        'whiff_rate': float(row['whiff_rate']) * 100 if row['whiff_rate'] else 0.0,
        'hits': int(row['hits']) if row['hits'] else 0,
        'home_runs': int(row['home_runs']) if row['home_runs'] else 0,
        'strikeouts': int(row['strikeouts']) if row['strikeouts'] else 0,
        'walks': int(row['walks']) if row['walks'] else 0,
        'batting_avg': batting_avg,
        'avg_exit_velocity': float(row['avg_exit_velocity']) if row['avg_exit_velocity'] else None,
        'avg_launch_angle': float(row['avg_launch_angle']) if row['avg_launch_angle'] else None,
        'barrels': int(row['barrels']) if row['barrels'] else 0
    }


def predict_expected_statistics(pitcher: Dict, lineup_df: pd.DataFrame) -> Dict:
    """
    Predict expected statistics for a pitcher vs lineup matchup.
    
    Args:
        pitcher: Pitcher archetype data
        lineup_df: DataFrame with 9 hitter archetypes
    
    Returns:
        Dictionary with expected statistics
    """
    lineup_analysis = predict_lineup_performance(pitcher, lineup_df)
    
    # Base league averages (per 9 innings)
    league_avg_runs = 4.5
    league_avg_hits = 8.5
    league_avg_strikeouts = 8.5
    league_avg_walks = 3.0
    league_avg_home_runs = 1.2
    
    # Calculate lineup quality (average hitter grade)
    grade_map = {'A+': 5, 'A': 4, 'B': 3, 'C': 2, 'D/F': 1}
    lineup_quality = lineup_df['overall_grade'].map(lambda x: grade_map.get(x, 3)).mean()
    
    # Calculate pitcher quality
    pitcher_quality = grade_map.get(pitcher.get('overall_grade', 'C'), 3)
    
    # Calculate average matchup score (negative = hitter advantage)
    avg_matchup_score = lineup_analysis['combined_score'].mean()
    
    # Adjust expected stats based on matchup
    # Negative matchup score (hitter advantage) increases expected runs
    # Positive matchup score (pitcher advantage) decreases expected runs
    matchup_factor = -avg_matchup_score * 0.15  # Scale factor
    
    # Quality gap factor
    quality_gap = pitcher_quality - lineup_quality
    quality_factor = -quality_gap * 0.2
    
    # Combined adjustment
    total_adjustment = matchup_factor + quality_factor
    
    # Calculate expected statistics
    expected_runs = max(0, league_avg_runs + total_adjustment)
    expected_hits = max(0, league_avg_hits + (total_adjustment * 1.5))
    expected_strikeouts = max(0, league_avg_strikeouts - (total_adjustment * 1.2))
    expected_walks = max(0, league_avg_walks + (total_adjustment * 0.3))
    expected_home_runs = max(0, league_avg_home_runs + (total_adjustment * 0.4))
    
    # Calculate expected WHIP (Walks + Hits per Inning Pitched)
    expected_whip = (expected_walks + expected_hits) / 9.0
    
    # Calculate expected ERA (simplified)
    expected_era = expected_runs * 9.0 / 9.0  # Assuming 9 innings
    
    return {
        'expected_runs': round(expected_runs, 2),
        'expected_hits': round(expected_hits, 1),
        'expected_strikeouts': round(expected_strikeouts, 1),
        'expected_walks': round(expected_walks, 1),
        'expected_home_runs': round(expected_home_runs, 2),
        'expected_whip': round(expected_whip, 2),
        'expected_era': round(expected_era, 2),
        'matchup_adjustment': round(total_adjustment, 2)
    }


def calculate_matchup_confidence(pitcher: Dict, hitter: Dict) -> float:
    """
    Calculate confidence score for a matchup prediction (0-100).
    
    Higher confidence = more reliable prediction based on:
    - Sample sizes (more data = higher confidence)
    - Data quality (verified vs provisional)
    - Archetype clarity (clear archetypes = higher confidence)
    
    Args:
        pitcher: Pitcher archetype data
        hitter: Hitter archetype data
    
    Returns:
        Confidence score (0-100)
    """
    confidence = 50.0  # Base confidence
    
    # Sample size factor
    pitcher_pitches = pitcher.get('total_pitches', 0) or 0
    hitter_pitches = hitter.get('total_pitches_faced', 0) or 0
    
    if pitcher_pitches > 1500:
        confidence += 15
    elif pitcher_pitches > 600:
        confidence += 10
    elif pitcher_pitches < 300:
        confidence -= 10
    
    if hitter_pitches > 1500:
        confidence += 15
    elif hitter_pitches > 600:
        confidence += 10
    elif hitter_pitches < 300:
        confidence -= 10
    
    # Data quality factor
    pitcher_confidence = pitcher.get('data_confidence', '')
    hitter_confidence = hitter.get('data_confidence', '')
    
    if 'VERIFIED' in str(pitcher_confidence):
        confidence += 10
    elif 'PROVISIONAL' in str(pitcher_confidence):
        confidence -= 5
    
    if 'VERIFIED' in str(hitter_confidence):
        confidence += 10
    elif 'PROVISIONAL' in str(hitter_confidence):
        confidence -= 5
    
    # Archetype clarity (if archetype is well-defined, higher confidence)
    if pitcher.get('pitcher_archetype_label') and hitter.get('hitter_archetype_label'):
        confidence += 5
    
    return max(0, min(100, confidence))


def get_archetype_compatibility(pitcher_archetype: str, hitter_archetype: str) -> Dict:
    """
    Get detailed compatibility analysis between pitcher and hitter archetypes.
    
    Args:
        pitcher_archetype: Pitcher archetype label
        hitter_archetype: Hitter archetype label
    
    Returns:
        Dictionary with compatibility analysis
    """
    # Archetype compatibility matrix (can be expanded)
    compatibility_rules = {
        # Pitcher archetype -> Hitter archetype -> compatibility score
        ("High-Octane Power Arm", "Discipline Specialist"): {
            'score': -1.5,  # Hitter advantage (discipline beats power)
            'reason': "Disciplined hitters can wait out power pitchers"
        },
        ("High-Octane Power Arm", "Aggressive Free-Swinger"): {
            'score': 2.0,  # Pitcher advantage
            'reason': "Power arms dominate free swingers"
        },
        ("Elite Contact Manager", "Contact-Oriented Pest"): {
            'score': -1.0,  # Hitter advantage
            'reason': "Contact hitters can spoil contact managers"
        },
        ("Elite Contact Manager", "Modern Three-True-Outcome"): {
            'score': 1.5,  # Pitcher advantage
            'reason': "Contact managers suppress power hitters"
        },
        ("Vertical Specialist", "LOW-BALL GOLFER"): {
            'score': 2.0,  # Pitcher advantage
            'reason': "Vertical specialists dominate low-ball hitters"
        },
        ("Vertical Specialist", "HIGH-BALL HUNTER"): {
            'score': -1.5,  # Hitter advantage
            'reason': "High-ball hitters can handle vertical pitches"
        }
    }
    
    key = (pitcher_archetype, hitter_archetype)
    
    if key in compatibility_rules:
        return compatibility_rules[key]
    else:
        return {
            'score': 0.0,
            'reason': "No specific compatibility data available"
        }


def analyze_team_matchup(pitcher: Dict, opposing_lineup_df: pd.DataFrame, 
                        own_lineup_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Analyze team-level matchup including both pitching and hitting sides.
    
    Args:
        pitcher: Starting pitcher archetype data
        opposing_lineup_df: Opposing team's lineup (9 hitters)
        own_lineup_df: Own team's lineup (optional, for full team analysis)
    
    Returns:
        Dictionary with team-level matchup analysis
    """
    # Analyze pitcher vs opposing lineup
    pitcher_prediction = predict_game_outcome(pitcher, opposing_lineup_df)
    expected_stats = predict_expected_statistics(pitcher, opposing_lineup_df)
    
    result = {
        'pitcher_analysis': {
            'win_probability': pitcher_prediction['win_probability'],
            'pitcher_advantage': pitcher_prediction['pitcher_advantage'],
            'expected_runs_allowed': expected_stats['expected_runs'],
            'expected_strikeouts': expected_stats['expected_strikeouts']
        },
        'opposing_lineup_strength': {
            'average_grade': opposing_lineup_df['overall_grade'].value_counts().to_dict(),
            'top_threats': pitcher_prediction['top_threats'],
            'weak_spots': pitcher_prediction['easy_outs']
        }
    }
    
    # If own lineup provided, analyze full team matchup
    if own_lineup_df is not None and len(own_lineup_df) == 9:
        # Calculate own lineup strength
        grade_map = {'A+': 5, 'A': 4, 'B': 3, 'C': 2, 'D/F': 1}
        own_lineup_quality = own_lineup_df['overall_grade'].map(lambda x: grade_map.get(x, 3)).mean()
        opposing_lineup_quality = opposing_lineup_df['overall_grade'].map(lambda x: grade_map.get(x, 3)).mean()
        
        result['team_analysis'] = {
            'own_lineup_quality': round(own_lineup_quality, 2),
            'opposing_lineup_quality': round(opposing_lineup_quality, 2),
            'lineup_advantage': round(own_lineup_quality - opposing_lineup_quality, 2),
            'overall_team_advantage': round(
                pitcher_prediction['pitcher_advantage'] + (own_lineup_quality - opposing_lineup_quality) * 0.5,
                2
            )
        }
    
    return result


def predict_bulk_matchups(engine: Engine, matchups: List[Dict]) -> pd.DataFrame:
    """
    Efficiently predict multiple pitcher vs lineup matchups.
    
    Args:
        engine: SQLAlchemy engine
        matchups: List of dictionaries, each containing:
            - 'pitcher_id' or 'pitcher_name': Pitcher identifier
            - 'hitter_ids' or 'hitter_names': List of 9 hitter identifiers
    
    Returns:
        DataFrame with predictions for all matchups
    """
    results = []
    
    for matchup in matchups:
        try:
            # Get pitcher
            if 'pitcher_id' in matchup:
                pitcher_df = get_pitcher_archetype(engine, pitcher_id=matchup['pitcher_id'])
            else:
                pitcher_df = get_pitcher_archetype(engine, pitcher_name=matchup['pitcher_name'])
            
            if pitcher_df.empty:
                continue
            
            pitcher = pitcher_df.iloc[0].to_dict()
            
            # Get lineup
            if 'hitter_ids' in matchup:
                lineup_df = get_hitter_archetypes(engine, hitter_ids=matchup['hitter_ids'])
            else:
                lineup_df = get_hitter_archetypes(engine, hitter_names=matchup['hitter_names'])
            
            if len(lineup_df) != 9:
                continue
            
            # Predict
            prediction = predict_game_outcome(pitcher, lineup_df)
            expected_stats = predict_expected_statistics(pitcher, lineup_df)
            
            results.append({
                'pitcher_name': pitcher['full_name'],
                'win_probability': prediction['win_probability'],
                'pitcher_advantage': prediction['pitcher_advantage'],
                'expected_runs': expected_stats['expected_runs'],
                'expected_strikeouts': expected_stats['expected_strikeouts'],
                'expected_whip': expected_stats['expected_whip']
            })
            
        except Exception as e:
            print(f"Error processing matchup: {e}")
            continue
    
    return pd.DataFrame(results)


def enhance_matchup_with_history(engine: Engine, pitcher: Dict, hitter: Dict, 
                                matchup_result: Dict) -> Dict:
    """
    Enhance a matchup prediction with historical data if available.
    
    Args:
        engine: SQLAlchemy engine
        pitcher: Pitcher archetype data
        hitter: Hitter archetype data
        matchup_result: Result from predict_individual_matchup()
    
    Returns:
        Enhanced matchup dictionary with historical data
    """
    pitcher_id = pitcher.get('pitcher')
    hitter_id = hitter.get('batter')
    
    if pitcher_id and hitter_id:
        historical = get_historical_matchup(engine, pitcher_id, hitter_id)
        
        if historical:
            # Adjust prediction based on historical performance
            historical_woba = historical['avg_woba']
            league_avg_woba = 0.320
            
            # If historical wOBA significantly differs from archetype prediction, adjust
            woba_difference = historical_woba - league_avg_woba
            
            # Add historical adjustment to combined score
            historical_adjustment = woba_difference * 2.0  # Scale factor
            enhanced_score = matchup_result['combined_score'] + historical_adjustment
            
            matchup_result['historical_data'] = historical
            matchup_result['enhanced_score'] = round(enhanced_score, 2)
            matchup_result['historical_adjustment'] = round(historical_adjustment, 2)
            matchup_result['has_history'] = True
        else:
            matchup_result['has_history'] = False
            matchup_result['historical_data'] = None
    else:
        matchup_result['has_history'] = False
        matchup_result['historical_data'] = None
    
    return matchup_result


# ============================================================================
# ADDITIONAL ADVANCED FEATURES
# ============================================================================

def optimize_lineup_order(pitcher: Dict, lineup_df: pd.DataFrame) -> pd.DataFrame:
    """
    Suggest optimal batting order based on matchup analysis.
    
    Strategy:
    - Best matchups (hitter advantage) should bat early (1-3)
    - Average matchups in middle (4-6)
    - Worst matchups (pitcher advantage) should bat later (7-9)
    - Consider alternating handedness for platoon advantages
    
    Args:
        pitcher: Pitcher archetype data
        lineup_df: DataFrame with 9 hitter archetypes
    
    Returns:
        DataFrame with suggested batting order (1-9)
    """
    if len(lineup_df) != 9:
        raise ValueError(f"Lineup must contain exactly 9 hitters, got {len(lineup_df)}")
    
    # Analyze all matchups
    lineup_analysis = predict_lineup_performance(pitcher, lineup_df)
    
    # Create order suggestions
    lineup_analysis['suggested_order'] = 0
    lineup_analysis['order_reason'] = ''
    
    # Sort by combined_score (ascending = best hitter matchups first)
    sorted_lineup = lineup_analysis.sort_values('combined_score', ascending=True).reset_index(drop=True)
    
    # Assign batting order positions
    # Positions 1-3: Best matchups (hitter advantage)
    # Positions 4-6: Middle matchups
    # Positions 7-9: Worst matchups (pitcher advantage)
    
    for idx, row in sorted_lineup.iterrows():
        if idx < 3:
            suggested_order = idx + 1
            reason = "Top of order - Strong matchup advantage"
        elif idx < 6:
            suggested_order = idx + 1
            reason = "Middle of order - Neutral matchup"
        else:
            suggested_order = idx + 1
            reason = "Bottom of order - Pitcher advantage"
        
        lineup_analysis.loc[lineup_analysis['hitter_name'] == row['hitter_name'], 'suggested_order'] = suggested_order
        lineup_analysis.loc[lineup_analysis['hitter_name'] == row['hitter_name'], 'order_reason'] = reason
    
    # Reorder by suggested order
    optimized_lineup = lineup_analysis.sort_values('suggested_order').reset_index(drop=True)
    
    return optimized_lineup[['suggested_order', 'hitter_name', 'hitter_grade', 'combined_score', 
                            'hitter_advantage', 'order_reason']]


def get_recent_form(engine: Engine, player_id: int, player_type: str = 'hitter', 
                days: int = 30) -> Optional[Dict]:
    """
    Get recent performance form for a player (last N days).
    
    Args:
        engine: SQLAlchemy engine
        player_id: Player MLBAM ID
        player_type: 'hitter' or 'pitcher'
        days: Number of days to look back
    
    Returns:
        Dictionary with recent form statistics
    """
    from datetime import date, timedelta
    
    cutoff_date = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    if player_type == 'hitter':
        query = text("""
            SELECT 
                COUNT(*) as total_pitches,
                AVG(woba_value) as avg_woba,
                AVG(launch_speed) as avg_exit_velocity,
                SUM(CASE WHEN events IN ('single', 'double', 'triple', 'home_run') THEN 1 ELSE 0 END) as hits,
                SUM(CASE WHEN events = 'home_run' THEN 1 ELSE 0 END) as home_runs,
                SUM(CASE WHEN events = 'strikeout' THEN 1 ELSE 0 END) as strikeouts,
                SUM(CASE WHEN launch_speed_angle = 6 THEN 1 ELSE 0 END) as barrels
            FROM fact_statcast_pitches
            WHERE batter = :player_id 
                AND game_date >= :cutoff_date
        """)
    else:  # pitcher
        query = text("""
            SELECT 
                COUNT(*) as total_pitches,
                AVG(estimated_woba_using_speedangle) as avg_xwoba,
                SUM(CASE WHEN description IN ('swinging_strike', 'swinging_strike_blocked') THEN 1 ELSE 0 END)::float / 
                    NULLIF(COUNT(CASE WHEN description IN ('swinging_strike', 'foul', 'hit_into_play', 'swinging_strike_blocked') THEN 1 END), 0) as whiff_rate,
                SUM(CASE WHEN events IN ('single', 'double', 'triple', 'home_run') THEN 1 ELSE 0 END) as hits_allowed,
                SUM(CASE WHEN events = 'strikeout' THEN 1 ELSE 0 END) as strikeouts
            FROM fact_statcast_pitches
            WHERE pitcher = :player_id 
                AND game_date >= :cutoff_date
        """)
    
    df = pd.read_sql(query, engine, params={'player_id': player_id, 'cutoff_date': cutoff_date})
    
    if df.empty or df.iloc[0]['total_pitches'] < 20:
        return None
    
    row = df.iloc[0]
    
    if player_type == 'hitter':
        return {
            'total_pitches': int(row['total_pitches']),
            'avg_woba': float(row['avg_woba']) if row['avg_woba'] else 0.0,
            'avg_exit_velocity': float(row['avg_exit_velocity']) if row['avg_exit_velocity'] else None,
            'hits': int(row['hits']) if row['hits'] else 0,
            'home_runs': int(row['home_runs']) if row['home_runs'] else 0,
            'strikeouts': int(row['strikeouts']) if row['strikeouts'] else 0,
            'barrels': int(row['barrels']) if row['barrels'] else 0,
            'days': days
        }
    else:
        return {
            'total_pitches': int(row['total_pitches']),
            'avg_xwoba': float(row['avg_xwoba']) if row['avg_xwoba'] else 0.0,
            'whiff_rate': float(row['whiff_rate']) * 100 if row['whiff_rate'] else 0.0,
            'hits_allowed': int(row['hits_allowed']) if row['hits_allowed'] else 0,
            'strikeouts': int(row['strikeouts']) if row['strikeouts'] else 0,
            'days': days
        }


def adjust_for_recent_form(prediction: Dict, pitcher_form: Optional[Dict] = None,
                        hitter_forms: Optional[List[Dict]] = None) -> Dict:
    """
    Adjust matchup prediction based on recent form.
    
    Args:
        prediction: Result from predict_game_outcome()
        pitcher_form: Recent form data for pitcher (from get_recent_form)
        hitter_forms: List of recent form data for each hitter
    
    Returns:
        Adjusted prediction dictionary
    """
    adjusted_prediction = prediction.copy()
    adjustments = []
    
    # Adjust for pitcher form
    if pitcher_form:
        league_avg_xwoba = 0.320
        pitcher_xwoba = pitcher_form.get('avg_xwoba', league_avg_xwoba)
        
        # If pitcher performing worse than league average, favor hitters
        if pitcher_xwoba > league_avg_xwoba + 0.020:  # 20 points worse
            adjustment = -0.5
            adjustments.append(f"Pitcher cold form: +{abs(adjustment):.1f} to hitters")
        elif pitcher_xwoba < league_avg_xwoba - 0.020:  # 20 points better
            adjustment = 0.5
            adjustments.append(f"Pitcher hot form: +{abs(adjustment):.1f} to pitcher")
        else:
            adjustment = 0.0
        
        adjusted_prediction['pitcher_advantage'] += adjustment
    
    # Adjust for hitter forms
    if hitter_forms and len(hitter_forms) == 9:
        league_avg_woba = 0.320
        lineup_adjustment = 0.0
        
        for i, hitter_form in enumerate(hitter_forms):
            if hitter_form:
                hitter_woba = hitter_form.get('avg_woba', league_avg_woba)
                
                # If hitter hot, favor them; if cold, favor pitcher
                if hitter_woba > league_avg_woba + 0.030:
                    lineup_adjustment -= 0.1  # Hot hitter
                elif hitter_woba < league_avg_woba - 0.030:
                    lineup_adjustment += 0.1  # Cold hitter
        
        if lineup_adjustment != 0:
            adjusted_prediction['pitcher_advantage'] += lineup_adjustment
            adjustments.append(f"Lineup form adjustment: {lineup_adjustment:+.2f}")
    
    # Recalculate win probability with adjustments
    avg_advantage = adjusted_prediction['pitcher_advantage']
    adjusted_win_prob = 100 / (1 + np.exp(-0.3 * avg_advantage))
    
    adjusted_prediction['adjusted_win_probability'] = round(adjusted_win_prob, 1)
    adjusted_prediction['original_win_probability'] = prediction['win_probability']
    adjusted_prediction['form_adjustments'] = adjustments
    
    return adjusted_prediction


def compare_pitchers_vs_lineup(engine: Engine, pitcher_ids: List[int], 
                            lineup_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare multiple pitchers against the same lineup.
    
    Args:
        engine: SQLAlchemy engine
        pitcher_ids: List of pitcher MLBAM IDs to compare
        lineup_df: DataFrame with 9 hitter archetypes
    
    Returns:
        DataFrame comparing all pitchers
    """
    results = []
    
    for pitcher_id in pitcher_ids:
        pitcher_df = get_pitcher_archetype(engine, pitcher_id=pitcher_id)
        
        if pitcher_df.empty:
            continue
        
        pitcher = pitcher_df.iloc[0].to_dict()
        
        # Get predictions
        prediction = predict_game_outcome(pitcher, lineup_df)
        expected_stats = predict_expected_statistics(pitcher, lineup_df)
        confidence = calculate_matchup_confidence(pitcher, lineup_df.iloc[0].to_dict())
        
        results.append({
            'pitcher_name': pitcher['full_name'],
            'pitcher_id': pitcher_id,
            'grade': pitcher.get('overall_grade', 'C'),
            'archetype': pitcher.get('pitcher_archetype_label', 'Unknown'),
            'win_probability': prediction['win_probability'],
            'pitcher_advantage': prediction['pitcher_advantage'],
            'expected_runs': expected_stats['expected_runs'],
            'expected_strikeouts': expected_stats['expected_strikeouts'],
            'expected_whip': expected_stats['expected_whip'],
            'confidence': confidence
        })
    
    comparison_df = pd.DataFrame(results)
    
    if not comparison_df.empty:
        comparison_df = comparison_df.sort_values('win_probability', ascending=False)
    
    return comparison_df


def analyze_situational_matchup(pitcher: Dict, hitter: Dict, situation: str = 'all') -> Dict:
    """
    Analyze matchup in specific game situations.
    
    Args:
        pitcher: Pitcher archetype data
        hitter: Hitter archetype data
        situation: 'all', 'clutch', 'late_inning', 'runners_on', 'two_strikes'
    
    Returns:
        Dictionary with situational analysis
    """
    base_matchup = predict_individual_matchup(pitcher, hitter)
    
    result = {
        'base_matchup': base_matchup,
        'situational_adjustments': {}
    }
    
    # Clutch performance (late innings, close games)
    hitter_clutch_pct = hitter.get('clutch_pct', 50.0) or 50.0
    
    if situation == 'clutch' or situation == 'all':
        if hitter_clutch_pct > 75:
            clutch_adj = -0.3  # Favor hitter in clutch
            result['situational_adjustments']['clutch'] = {
                'adjustment': clutch_adj,
                'reason': f"Hitter has elite clutch performance ({hitter_clutch_pct:.1f}%ile)"
            }
        elif hitter_clutch_pct < 25:
            clutch_adj = 0.3  # Favor pitcher in clutch
            result['situational_adjustments']['clutch'] = {
                'adjustment': clutch_adj,
                'reason': f"Hitter struggles in clutch situations ({hitter_clutch_pct:.1f}%ile)"
            }
    
    # Two-strike situations
    hitter_battle_pct = hitter.get('battle_pct', 50.0) or 50.0
    pitcher_role = pitcher.get('matchup_role', '')
    
    if situation == 'two_strikes' or situation == 'all':
        if hitter_battle_pct > 80 and pitcher_role == 'PITCH TO CONTACT SURGEON':
            two_strike_adj = -0.5  # Elite spoiler vs contact pitcher
            result['situational_adjustments']['two_strikes'] = {
                'adjustment': two_strike_adj,
                'reason': "Elite spoiler hitter vs contact pitcher"
            }
        elif hitter_battle_pct < 30 and pitcher_role == 'DOMINANT ACE':
            two_strike_adj = 0.5  # Free swinger vs dominant ace
            result['situational_adjustments']['two_strikes'] = {
                'adjustment': two_strike_adj,
                'reason': "Free swinger vs dominant ace"
            }
    
    # Calculate total situational adjustment
    total_adjustment = sum(adj['adjustment'] for adj in result['situational_adjustments'].values())
    result['situational_score'] = base_matchup['combined_score'] + total_adjustment
    result['total_adjustment'] = total_adjustment
    
    return result


def simulate_game(pitcher: Dict, lineup_df: pd.DataFrame, n_simulations: int = 1000) -> Dict:
    """
    Monte Carlo simulation of a game to predict outcomes.
    
    Args:
        pitcher: Pitcher archetype data
        lineup_df: DataFrame with 9 hitter archetypes
        n_simulations: Number of simulations to run
    
    Returns:
        Dictionary with simulation results
    """
    # Get base predictions
    expected_stats = predict_expected_statistics(pitcher, lineup_df)
    base_win_prob = predict_game_outcome(pitcher, lineup_df)['win_probability']
    
    # Simulate games
    wins = 0
    runs_allowed_list = []
    strikeouts_list = []
    
    for _ in range(n_simulations):
        # Simulate runs allowed (using Poisson distribution)
        expected_runs = expected_stats['expected_runs']
        runs_allowed = np.random.poisson(expected_runs)
        runs_allowed_list.append(runs_allowed)
        
        # Simulate strikeouts (using normal distribution)
        expected_k = expected_stats['expected_strikeouts']
        strikeouts = max(0, int(np.random.normal(expected_k, expected_k * 0.15)))
        strikeouts_list.append(strikeouts)
        
        # Simple win condition: if runs allowed <= 4, pitcher's team wins
        # (This is simplified - in reality would need opponent's expected runs)
        if runs_allowed <= 4:
            wins += 1
    
    win_prob_sim = (wins / n_simulations) * 100
    
    return {
        'simulated_win_probability': round(win_prob_sim, 1),
        'base_win_probability': base_win_prob,
        'simulations_run': n_simulations,
        'avg_runs_allowed': round(np.mean(runs_allowed_list), 2),
        'avg_strikeouts': round(np.mean(strikeouts_list), 1),
        'runs_allowed_distribution': {
            'min': int(np.min(runs_allowed_list)),
            'max': int(np.max(runs_allowed_list)),
            'median': int(np.median(runs_allowed_list)),
            'p25': int(np.percentile(runs_allowed_list, 25)),
            'p75': int(np.percentile(runs_allowed_list, 75))
        }
    }


def get_start_sit_recommendations(pitcher: Dict, available_hitters: pd.DataFrame,
                                lineup_size: int = 9) -> Dict:
    """
    Recommend which hitters to start or sit based on matchup analysis.
    
    Args:
        pitcher: Pitcher archetype data
        available_hitters: DataFrame with available hitters (more than lineup_size)
        lineup_size: Number of lineup spots (default 9)
    
    Returns:
        Dictionary with start/sit recommendations
    """
    if len(available_hitters) <= lineup_size:
        return {
            'start': available_hitters.to_dict('records'),
            'sit': [],
            'message': 'Not enough hitters for recommendations'
        }
    
    # Analyze all matchups
    all_matchups = predict_lineup_performance(pitcher, available_hitters)
    
    # Sort by combined_score (ascending = best hitter matchups first)
    sorted_matchups = all_matchups.sort_values('combined_score', ascending=True)
    
    # Top N = start, rest = sit
    start_hitters = sorted_matchups.head(lineup_size)
    sit_hitters = sorted_matchups.tail(len(available_hitters) - lineup_size)
    
    return {
        'start': start_hitters[['hitter_name', 'hitter_grade', 'combined_score', 
                                'hitter_advantage', 'reasons']].to_dict('records'),
        'sit': sit_hitters[['hitter_name', 'hitter_grade', 'combined_score', 
                        'hitter_advantage', 'reasons']].to_dict('records'),
        'message': f'Recommended {lineup_size} starters based on matchup analysis'
    }


def prepare_visualization_data(prediction: Dict) -> Dict:
    """
    Prepare prediction data for visualization/charting.
    
    Args:
        prediction: Result from predict_game_outcome()
    
    Returns:
        Dictionary with data formatted for visualization
    """
    lineup_analysis = prediction['lineup_analysis']
    
    # Prepare data for various chart types
    chart_data = {
        'matchup_scores': {
            'hitters': lineup_analysis['hitter_name'].tolist(),
            'scores': lineup_analysis['combined_score'].tolist(),
            'advantages': lineup_analysis['hitter_advantage'].tolist()
        },
        'grade_distribution': {
            'grades': lineup_analysis['hitter_grade'].value_counts().to_dict()
        },
        'threat_analysis': {
            'top_threats': [t['name'] for t in prediction['top_threats']],
            'threat_scores': [t['score'] for t in prediction['top_threats']],
            'easy_outs': [e['name'] for e in prediction['easy_outs']],
            'out_scores': [e['score'] for e in prediction['easy_outs']]
        },
        'win_probability': prediction['win_probability'],
        'pitcher_advantage': prediction['pitcher_advantage']
    }
    
    return chart_data


def calculate_matchup_value(pitcher: Dict, hitter: Dict, 
                        context: Optional[Dict] = None) -> Dict:
    """
    Calculate the "value" of a matchup (useful for DFS, betting, etc.).
    
    Args:
        pitcher: Pitcher archetype data
        hitter: Hitter archetype data
        context: Optional context (salary, ownership, etc.)
    
    Returns:
        Dictionary with matchup value metrics
    """
    matchup = predict_individual_matchup(pitcher, hitter)
    
    # Base value score (0-100)
    # Negative combined_score (hitter advantage) = higher value for hitter
    # Positive combined_score (pitcher advantage) = higher value for pitcher
    
    if matchup['hitter_advantage']:
        hitter_value = 50 + abs(matchup['combined_score']) * 10
        pitcher_value = 50 - abs(matchup['combined_score']) * 10
    else:
        hitter_value = 50 - abs(matchup['combined_score']) * 10
        pitcher_value = 50 + abs(matchup['combined_score']) * 10
    
    hitter_value = max(0, min(100, hitter_value))
    pitcher_value = max(0, min(100, pitcher_value))
    
    result = {
        'hitter_value': round(hitter_value, 1),
        'pitcher_value': round(pitcher_value, 1),
        'matchup_quality': 'Strong' if abs(matchup['combined_score']) > 1.5 else 'Moderate' if abs(matchup['combined_score']) > 0.5 else 'Neutral',
        'recommendation': 'Start Hitter' if hitter_value > 60 else 'Start Pitcher' if pitcher_value > 60 else 'Neutral'
    }
    
    # Add context-based adjustments if provided
    if context:
        if 'hitter_salary' in context and 'avg_salary' in context:
            salary_ratio = context['hitter_salary'] / context['avg_salary']
            if salary_ratio < 0.8 and hitter_value > 50:  # Cheap hitter with good matchup
                result['value_play'] = True
                result['recommendation'] = 'Strong Value Play'
    
    return result
