import pybaseball as pyb
import pandas as pd

from connection_engine import connect_to_db

# Establish database connection
engine = connect_to_db()

# Example: Get all 2024 season batting stats from FanGraphs
# This is a sample function; your final ETL will be more complex.
def extract_batting_data(year=2023):
    # fgs is FanGraphs Season Stats
    df = pyb.batting_stats_bref(year)
    # Rename columns to match your SQL schema (e.g., 'BB' for Walks, 'K' for Strikeouts)
    df = df.rename(columns={'ID': 'player_id', 'Tm': 'team_id'})
    return df

# # For the 'players' table, extract player IDs and names
# def extract_player_info(df):
#     return df[['player_id', 'Name']].copy()

# def calculate_metrics(df):
#     # NOTE: This is a simplified transformation.
#     # wRC+ and FIP require complex league constants, which you'd calculate here.

#     # Example: Simple calculation for BABIP (H - HR) / (AB - K - HR + SF)
#     # Ensure column names match your SQL schema!
#     df['BABIP'] = (df['H'] - df['HR']) / (df['AB'] - df['K'] - df['HR'] + df['SF'])

#     # Add placeholder values for wRC_PLUS and FIP (which you'll replace later)
#     df['wRC_PLUS'] = 100 # Placeholder
#     df['FIP'] = 3.50   # Placeholder

#     return df

# def load_data(df, table_name, engine, if_exists='append'):
#     print(f"Loading data into {table_name}...")
#     try:
#         df.to_sql(
#             table_name,
#             engine,
#             if_exists=if_exists,  # 'append' adds new data; 'replace' clears and reloads
#             index=False,
#             method='multi'        # Faster loading for larger dataframes
#         )
#         print(f"Successfully loaded {len(df)} rows into {table_name}.")
#     except Exception as e:
#         print(f"Error loading data: {e}")


# if __name__ == '__main__':
#     batting_df = extract_batting_data(year=2024)
    
#     # 1. Load Player Info (if_exists='append' to only add new players)
#     player_info_df = extract_player_info(batting_df)
#     load_data(player_info_df, 'players', engine, if_exists='append')

#     # 2. Transform and Load Batting Stats (Replace existing stats for the season)
#     processed_batting_df = calculate_metrics(batting_df)
    
#     # Select only the columns that match your batting_stats table schema
#     batting_stats_cols = ['player_id', 'season', 'team_id', 'G', 'AB', 'H', 'HR', 'BB', 'K', 'PA', 'wRC_PLUS', 'BABIP']
    
#     load_data(processed_batting_df[batting_stats_cols], 'batting_stats', engine, if_exists='replace')