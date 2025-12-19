from sqlalchemy.engine import Engine
import pylahman
import pybaseball as pyb
import pandas as pd

def create_dim_player_table(engine: Engine):   
    try:
        print("💾 Creating dim_player...")
        players_lahman = pylahman.People()
        player_chadwick = pyb.chadwick_register()

        # Join lahman and chadwick on key identifiers and bring all the columns from lahman
        # Ignore if key_bbref is empty in chadwick
        players_chadwick_clean = player_chadwick[player_chadwick['key_retro'].notna()]
        players_lahman_clean   = players_lahman[players_lahman['retroID'].notna()]

        players_df = pd.merge(
            players_chadwick_clean,
            players_lahman_clean,
            left_on=['key_retro'],
            right_on=['retroID'],
            how='left',
        )

        # Remove unnecesary columns and drop them from the dataframe
        cols_to_remove = ['retroID', 'bbrefID', 'mlb_played_first', 'mlb_played_last']
        players_df = players_df.drop(columns= cols_to_remove)

        # Rename the fields
        rename_map = {
            # IDs
            "key_mlbam":     "key_mlbam",
            "key_retro":     "key_retro",
            "key_bbref":     "key_bbref",
            "key_fangraphs": "key_fangraphs",
            "ID":            "id_lahman",
            "playerID":      "player_id_lahman",

            # Names
            "name_last":     "last_name_chadwick",
            "name_first":    "first_name_chadwick",
            "nameLast":      "last_name_lahman",
            "nameFirst":     "first_name_lahman",
            "nameGiven":     "first_and_second_name_lahman",

            # Debut/Final game
            "debut":         "debut",
            "finalGame":     "final_game",

            # Info
            "weight":        "weight",
            "height":        "height",
            "bats":          "bats",
            "throws":        "throws",

            # Birth/Death
            "birthYear":     "birth_year",
            "birthMonth":    "birth_month",
            "birthDay":      "birth_day",
            "birthCity":     "birth_city",
            "birthCountry":  "birth_country",
            "birthState":    "birth_state",
            "deathYear":     "death_year",
            "deathMonth":    "death_month",
            "deathDay":      "death_day",
            "deathCountry":  "death_country",
            "deathState":    "death_state",
            "deathCity":     "death_city",
        }

        # Apply the rename
        players_df = players_df.rename(columns= rename_map)

        # Order the new columns
        ordered_cols = [
            "key_mlbam",
            "key_retro",
            "key_bbref",
            "key_fangraphs",
            "id_lahman",
            "player_id_lahman",
            "last_name_chadwick",
            "first_name_chadwick",
            "last_name_lahman",
            "first_name_lahman",
            "first_and_second_name_lahman",
            "debut",
            "final_game",
            "weight",
            "height",
            "bats",
            "throws",
            "birth_year",
            "birth_month",
            "birth_day",
            "birth_city",
            "birth_country",
            "birth_state",
            "death_year",
            "death_month",
            "death_day",
            "death_country",
            "death_state",
            "death_city"
        ]

        # Apply the order
        players_df = players_df[ordered_cols]

        # This selects only columns with numbers and fills their nulls with -1
        numeric_cols = players_df.select_dtypes(include=['number']).columns
        players_df[numeric_cols] = players_df[numeric_cols].fillna(-1)

        # Replace nulls in the text columns
        text_cols = [
            "key_retro",
            "key_bbref",
            "player_id_lahman",
            "last_name_chadwick",
            "first_name_chadwick",
            "last_name_lahman",
            "first_name_lahman",
            "first_and_second_name_lahman",
            "bats",
            "throws",
            "birth_city",
            "birth_country",
            "birth_state",
            "death_country",
            "death_state",
            "death_city"
        ]

        # Convert to a standard object type first and then fill the nulls with N/A
        for col in text_cols:
            players_df[col] = players_df[col].astype(object).fillna('N/A')
            

        # List the date columns
        date_cols = [
            "debut",
            "final_game"
        ]
        # Fill null dates with January 1st, 1700
        for col in date_cols:
            players_df[col] = players_df[col].fillna(pd.Timestamp('1700-01-01'))

        # Check for nulls in my table - there shouldn't be any
        if (players_df.isnull().sum() == 0).all():
            print(f"   ✅ No nulls found!")
        else:
            print("   ⚠️ WARNING - There are nulls in some columns.")

        # # --- STEP 5: LOADING ---
        print(f"   🔃 Loading {len(players_df)} rows...")
        
        players_df.to_sql(
            'dim_player', 
            engine, 
            if_exists='replace',
            index=False, 
            chunksize=5000
        )
        
        print(f"   ✅ Successfully added {len(players_df)} new rows of data.")

    except Exception as e:
        print(f"   ❌ ETL Failed during extraction or loading: {e}")
        
