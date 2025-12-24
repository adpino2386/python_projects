from sqlalchemy.engine import Engine
import pylahman
import pybaseball as pyb
import pandas as pd
from datetime import date, timedelta

def create_fact_statcast_events_pitch_by_pitch(engine: Engine, n_days= 90):
    """
    Pulls raw pitch-by-pitch data for all games played in the last 'n_days' 
    and then extracts the final score for each game.
    """
    def load_fact_statcast_events(engine: Engine, df):
        try:
            table_name = 'fact_statcast_pitches'
            print(f"💾 Creating {table_name}...")
            
            # Loading
            print(f"   🔃 Loading {len(df)} rows...")
            
            df.to_sql(
                table_name, 
                engine, 
                if_exists='replace',
                index=False, 
                chunksize=5000
            )
            
            print(f"   ✅ Successfully added {len(df)} new rows of data.")
        
        except Exception as e:
            print(f"   ❌ ETL Failed during extraction or loading: {e}")
    
    # Get today's date
    today = date.today()

    # Calculate the start and end dates for the n-day range
    end_date = today - timedelta(days= 1)  # Search up to yesterday
    start_date = today - timedelta(days= n_days)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    print(f"Searching for all games played from {start_date_str} to {end_date_str}...")

    try:
        # Pull all pitch-by-pitch data in that range
        fact_statcast_pitches_last_n_days = pyb.statcast(start_dt= start_date_str, end_dt= end_date_str)
        
    except Exception as e:
        print(f"Error retrieving Statcast data: {e}")
        return pd.DataFrame()

    if fact_statcast_pitches_last_n_days.empty:
        print(f"No games found between {start_date_str} and {end_date_str}.")
        return pd.DataFrame()

    print(f"Successfully pulled {len(fact_statcast_pitches_last_n_days)} pitch events for the last {n_days} days.")

    # def filter_days(df, days):
    #     cutoff = today - timedelta(days=days)
    #     # Convert 'Date' column to datetime objects if they aren't already
    #     df['game_date'] = pd.to_datetime(df['game_date']).dt.date
    #     return df[df['game_date'] >= cutoff]

    # # Sub-df from the main one
    # results_1_day_df   = filter_days(fact_statcast_pitches_last_90_days, 1)
    # results_7_days_df  = filter_days(fact_statcast_pitches_last_90_days, 7)
    # results_30_days_df = filter_days(fact_statcast_pitches_last_90_days, 30)

    # Apply the function
    load_fact_statcast_events(engine, fact_statcast_pitches_last_n_days)