from sqlalchemy.engine import Engine
import pylahman
import pybaseball as pyb
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import text


def update_fact_statcast_pitches(engine: Engine):
    table_name = 'fact_statcast_pitches'
    print(f"💾 Updating {table_name}...")
    
    
    def get_latest_date_from_db():
        """Find the max date in the fact_statcast_pitches  

        Returns:
            _type_: _description_
        """
        query = text("SELECT MAX(game_date) FROM fact_statcast_pitches")
        
        with engine.connect() as conn:
            result = conn.execute(query).scalar()
            
        return result

    # Execute and calculate fetch window
    last_date = get_latest_date_from_db()

    if last_date:
        # I want to start fetching from the day AFTER the last recorded date
        fetch_start = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
        # Fetch up to yesterday
        fetch_end = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        if fetch_start <= fetch_end:
            print(f"   🔄 Last data was {last_date}. Fetching from {fetch_start} to {fetch_end}...")
            new_data = pyb.statcast(start_dt=fetch_start, end_dt=fetch_end)
            new_data.to_sql('fact_statcast_pitches', engine, if_exists='append', index=False)
        else:
            print("   ✅ Database is already up to date.")
    else:
        print("   ❌ Empty table. You need to run an initial seed fetch.")
