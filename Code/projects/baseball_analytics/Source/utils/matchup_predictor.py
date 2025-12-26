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
