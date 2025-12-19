import os
from sqlalchemy import create_engine
import pybaseball as pyb
import pybaseball.cache # Ensure caching is imported
import pandas as pd
from dotenv import load_dotenv
import time
from datetime import date, timedelta
from sqlalchemy.engine import Engine
from sqlalchemy import text
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from rapidfuzz import process
import re
import numpy as np
from io import StringIO
import pylahman

from utils.connection_engine import create_connection_postgresql
from utils.tbl_dim_player import create_dim_player_table
from utils.tbl_dim_franchise import create_dim_franchise_table
from utils.tbl_fact_player import create_fact_player_tables
from utils.tbl_fact_statcast_pitches import create_fact_statcast_events_pitch_by_pitch

def main():
    # Create the engine
    engine = create_connection_postgresql() 
    
    # Import and load the player information
    create_dim_player_table(engine)
    
    # Import and load the franchise table
    create_dim_franchise_table(engine)
    
    # Import and load the players' fact tables
    create_fact_player_tables(engine)
    
    # Import and load the events -pitch by pitch, 
    # from Statcast
    create_fact_statcast_events_pitch_by_pitch(engine, n_days= 730)

if __name__ == "__main__":
    main()