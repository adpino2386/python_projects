import streamlit as st
from pybaseball import standings
import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy import text

from utils.connection_engine import create_connection_postgresql

engine = create_connection_postgresql() 

# 1. App Title & Sidebar
st.set_page_config(page_title="Baseball Edge Analytics", layout="wide")
st.title("⚾ Baseball Edge: Pythagorean Predictor")
st.sidebar.header("Filter Options")

# # 2. Data Fetching (Cached for speed)
# @st.cache_data
# def get_mlb_standings():
#     # Gets current year standings
#     data = standings(2024) 
#     # standings returns a list of dataframes by division; we'll combine them
#     full_standings = pd.concat(data)
#     return full_standings

# df = get_mlb_standings()

# # 3. Calculation Logic
# exponent = 1.83
# df['Expected_Win_Pct'] = (df['RS']**exponent) / (df['RS']**exponent + df['RA']**exponent)
# df['Diff'] = df['W-L%'] - df['Expected_Win_Pct']

# # 4. User Interface
# st.subheader("Current Season Performance vs. Expectation")
# st.write("Teams with a negative 'Diff' are underperforming their stats (Buy Low).")

# # Display the table
# formatted_df = df[['Tm', 'W', 'L', 'W-L%', 'RS', 'RA', 'Expected_Win_Pct', 'Diff']]
# st.dataframe(formatted_df.style.background_gradient(subset=['Diff'], cmap='RdYlGn'))

# # 5. Search Feature
# target_team = st.sidebar.selectbox("Select a Team to Analyze", df['Tm'].unique())
# team_data = df[df['Tm'] == target_team].iloc[0]

# st.metric(label=f"{target_team} Expected Win %", 
#         value=f"{team_data['Expected_Win_Pct']:.3f}", 
#         delta=f"{team_data['Diff']:.3f} (vs Actual)")