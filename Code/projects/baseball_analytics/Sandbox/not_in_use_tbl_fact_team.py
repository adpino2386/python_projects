from sqlalchemy.engine import Engine
import pylahman
import pybaseball as pyb
import pandas as pd
from datetime import date, timedelta

def create_team_fact_tables(engine: Engine):    
    def load_fact_team_tables(engine: Engine, df, category):
        try:
            table_name = 'fact_team_' + category
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

    # Declare the years
    current_year  = date.today().year
    ten_years_ago = current_year - 10

    # Import the team data for the last 10 years
    fact_team_batting  = pyb.team_batting(ten_years_ago, current_year,  ind= 1, qual= 0)
    fact_team_pitching = pyb.team_pitching(ten_years_ago, current_year,  ind= 1, qual= 0)
    fact_team_fielding = pyb.team_fielding(ten_years_ago, current_year,  ind= 1, qual= 0)

    # Apply the function
    load_fact_team_tables(engine, fact_team_batting,  'batting')
    load_fact_team_tables(engine, fact_team_pitching, 'pitching')
    load_fact_team_tables(engine, fact_team_fielding, 'fielding')
