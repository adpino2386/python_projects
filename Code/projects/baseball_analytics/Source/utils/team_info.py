from sqlalchemy.engine import Engine
import pylahman
import pybaseball as pyb
import pandas as pd


def update_team_info(engine: Engine):
    try:
        print("💾 Processing team_info...")
        
        # Import the data
        team_info = pylahman.Teams()

        # Identify all text columns
        text_cols = team_info.select_dtypes(include=['object', 'string']).columns

        # Convert to object first, then fill with N/A
        for col in text_cols:
            # Converting to object allows 'N/A' to be treated as a normal string
            team_info[col] = team_info[col].astype(object).fillna('N/A')
            
            # Just in case some were literal 'nan' strings:
            team_info[col] = team_info[col].replace(['nan', 'None', '<NA>'], 'N/A')

        # This selects only columns with numbers and fills their nulls with -1
        numeric_cols = team_info.select_dtypes(include=['number']).columns
        team_info[numeric_cols] = team_info[numeric_cols].fillna(-1)

        # Final verification
        null_count_text    = team_info[text_cols].isnull().sum().sum()
        null_count_numeric = team_info[numeric_cols].isnull().sum().sum()
        total_nulls        = null_count_text + null_count_numeric

        if total_nulls == 0:
            print("   ✅ All columns are clean. No nulls found!")
        else:
            print(f"   ⚠️ Warning: {total_nulls} nulls still remain some columns.")

        # Loading
        print(f"   Loading {len(team_info)} new rows into 'team_info'...")
        
        team_info.to_sql(
            'team_info', 
            engine, 
            if_exists='replace',
            index=False, 
            chunksize=5000
        )
        
        print(f"   ✅ Team information successfully added {len(team_info)} new rows of data.")
    
    except Exception as e:
        print(f"   ❌ ETL Failed during extraction or loading: {e}")