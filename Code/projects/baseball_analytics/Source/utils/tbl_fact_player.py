from sqlalchemy.engine import Engine
import pylahman
import pybaseball as pyb
import pandas as pd
from datetime import date, timedelta

def create_fact_player_tables(engine: Engine):    
    def load_fact_player_tables(engine: Engine, df, category):
        try:
            table_name = 'fact_player_' + category
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
    current_year   = date.today().year
    five_years_ago = current_year - 5

    # Import the team data for the last 10 years
    # print("\n" + "="*40)
    # print(f"{'⬇️  Importing player stats':^40}")
    # print(f"{'Please wait...':^40}")
    # print("="*40 + "\n")
    print("⬇️  Importing player stats... please wait")
    
    fact_player_batting  = pyb.batting_stats(five_years_ago, current_year,  ind= 1, qual= 0)
    fact_player_pitching = pyb.pitching_stats(five_years_ago, current_year,  ind= 1, qual= 0)
    fact_player_fielding = pyb.fielding_stats(five_years_ago, current_year,  ind= 1, qual= 0)
    
    # Speed tables are by year - they do not include range
    # Setup year range
    #current_year = datetime.now().year
    years = range(current_year - 9, current_year + 1) # Last 10 years including current

    all_dfs = []

    for year in years:
        #print(f"Fetching sprint speed for {year}...")
        try:
            # Fetch data
            df = pyb.statcast_sprint_speed(year, 50)
            
            # Adding the years
            df['Season'] = year
            
            all_dfs.append(df)
        except Exception as e:
            print(f"Could not fetch data for {year}: {e}")

    # Combine everything into one fact table
    fact_player_running = pd.concat(all_dfs, ignore_index=True)

    # Apply the function
    load_fact_player_tables(engine, fact_player_batting,  'batting')
    load_fact_player_tables(engine, fact_player_pitching, 'pitching')
    load_fact_player_tables(engine, fact_player_fielding, 'fielding')
    load_fact_player_tables(engine, fact_player_running, 'running')
