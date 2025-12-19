from sqlalchemy.engine import Engine
import pylahman
import pybaseball as pyb
import pandas as pd


def create_dim_franchise_table(engine: Engine):
    try:
        print("💾 Creating dim_franchise...")
        
        # Import the franchises
        #? Note: As of 2025-12-18 there is only data up to the 2024 season
        team_franchises = pylahman.TeamsFranchises()
        
        # Data cleaning
        # Identify all text columns
        text_cols = team_franchises.select_dtypes(include=['object', 'string']).columns

        # Convert to object first, then fill (since the columns are literal strings)
        for col in text_cols:
            # Converting to object allows 'N/A' to be treated as a normal string
            team_franchises[col] = team_franchises[col].astype(object).fillna('N/A')
            
            # Just in case some were literal 'nan' strings:
            team_franchises[col] = team_franchises[col].replace(['nan', 'None', '<NA>'], 'N/A')

        # Final verification
        null_count = team_franchises[text_cols].isnull().sum().sum()
        if null_count == 0:
            print("   ✅ All string columns are clean. No nulls found!")
        else:
            print(f"   ⚠️ Warning: {null_count} nulls still remain in text columns.")
            
        
        # Loading
        print(f"   🔃 Loading {len(team_franchises)} rows...")
        
        team_franchises.to_sql(
            'dim_franchise', 
            engine, 
            if_exists='replace',
            index=False, 
            chunksize=5000
        )
        
        print(f"   ✅ Successfully added {len(team_franchises)} new rows of data.")
    
    except Exception as e:
        print(f"   ❌ ETL Failed during extraction or loading: {e}")