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

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import IsolationForest

from utils.connection_engine import create_connection_postgresql
from utils.tbl_dim_player import create_dim_player_table
from utils.tbl_dim_franchise import create_dim_franchise_table
from utils.tbl_fact_player import create_fact_player_tables
from utils.update_tbl_fact_statcast_pitches import update_fact_statcast_pitches
from utils.tbl_dim_pitcher_archetypes import create_dim_pitcher_archetypes
from utils.tbl_luck_scores import update_fact_player_luck_summary

def main():
    # Create the engine
    engine = create_connection_postgresql() 
    
    # # Import and load the player information
    # create_dim_player_table(engine)
    
    # # Import and load the franchise table
    # create_dim_franchise_table(engine)
    
    # # Import and load the players' fact tables
    # create_fact_player_tables(engine)
    
    # # Check the max date in fact_statcast_pitches.
    # # If the max date is not yesterday's date, then update the table and 
    # # append the days missing.
    # update_fact_statcast_pitches(engine)
    
    # TODO: Check the last date that it was updated.
    # if it has been less than 3 weeks since the last
    # time, then do not run it. 
    # If I re-cluster every day, a pitcher might jump from "Archetype 0" to "Archetype 1" 
    # just because of one bad outing. This makes your dashboard confusing for users who see a 
    # player's label constantly changing.    
    # ? KMeans model
    # Update the dim_pitcher_archetypes 
    create_dim_pitcher_archetypes(engine)
    
    # # Update Luck Score table
    # update_fact_player_luck_summary(engine)
    
if __name__ == "__main__":
    main() 