import pandas as pd
from sqlalchemy.engine import Engine
import pandas as pd
from datetime import date, timedelta
from datetime import datetime
from sqlalchemy import text


def calculate_luck_scores(engine: Engine, min_ab= 25):
    """_summary_

    Args:
        engine (Engine): _description_
        min_ab (int, optional): _description_. Defaults to 25.

    Returns:
        _type_: _description_
    """
    query = "SELECT * FROM vw_batter_vs_pitcher_archetype"
    df = pd.read_sql(query, engine)
    
    #? Filter by At-Bats first to ensure statistical significance
    # Even though the SQL view has a filter, we can tighten it here if needed
    df = df[df['at_bats'] >= min_ab].copy()
    
    #? Calculate Ranks (Percentiles)
    df['ev_rank'] = df['avg_exit_velo'].rank(pct=True)
    df['speed_rank'] = df['avg_sprint_speed'].rank(pct=True)
    
    # Lower time is BETTER for home_to_first, so we rank descending
    df['h1_rank'] = df['avg_home_to_first'].rank(pct=True, ascending=False)
    df['ba_rank'] = df['batting_avg'].rank(pct=True)
    
    # 3. Weighting the "Potential" (Expected Performance)
    # 60% Exit Velo, 20% Sprint, 20% Home-to-1st
    df['potential_score'] = (df['ev_rank'] * 0.6) + (df['speed_rank'] * 0.2) + (df['h1_rank'] * 0.2)
    
    #? Luck Score Calculation
    # A positive score means their physical tools exceed their actual results
    # If High Positive (Unlucky) e.g. 0.40
    # The player’s tools are elite (e.g., 90th percentile), but their results are 
    # poor (e.g., 50th percentile). They are likely hitting into the "loudest outs" in the league.

    # If Near Zero (Fair) e.g. 0.05
    # The player is getting exactly what they deserve. 
    # Their speed and power perfectly explain their batting average.

    # If High Negative (Lucky) e.g. -0.4:
    # The player has weak tools (e.g., 30th percentile) but a high batting average (e.g., 70th percentile). 
    # They are likely benefiting from "bloop" hits, defensive errors.
    df['luck_score'] = df['potential_score'] - df['ba_rank']
    
    #? Sample Size Adjustment
    # This 'confidence' metric tells you how much you should trust the luck score
    
    # 0.90 to 1.0 -> High Confidence. This player has faced this archetype many times. 
    # The luck score is likely a true reflection of their performance.
    
    # 0.5 -> Moderate. There is enough data to see a trend, 
    # but it could still be swayed by a single lucky or unlucky game.
    
    # 0.1 or lower -> Low Certainty. The player has very few At-Bats against this archetype. 
    # The high luck score might just be "small-sample noise".
    df['luck_confidence'] = df['at_bats'] / df['at_bats'].max()
    
    # Add the current timestamp to every row
    df['calculation_date'] = datetime.now()
    
    # Sort by the luckiest (most underperforming) players first
    return df.sort_values('luck_score', ascending=False)

def update_fact_player_luck_summary(engine: Engine):
    """_summary_

    Args:
        engine (Engine): _description_
    """    
    print(f"💾 Creating fact_player_luck_summary...")
    
    # Call the function
    df = calculate_luck_scores(engine, min_ab= 25)
    
    try:
        # Loading message
        print(f"   🔃 Loading {len(df)} rows...")
        
        # Write to the database
        df[['batter', 'luck_score', 'luck_confidence', 'at_bats', 'calculation_date']].to_sql(
        'fact_player_luck_summary', 
        engine, 
        if_exists='replace', 
        index=False
        )
        
        print(f"   ✅ Successfully added {len(df)} new rows of data.")
    
    except Exception as e:
        print(f"   ❌ ETL Failed during extraction or loading: {e}")