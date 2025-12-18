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
from utils.players_info import update_players
from utils.team_franchises import update_team_franchises
from utils.team_info import update_team_info

def main():
    # Create the engine
    engine = create_connection_postgresql() 
    
    # Update the players table
    update_players(engine)
    
    # Update the team_franchises table
    update_team_franchises(engine)
    
    # Update the team_info table
    update_team_info(engine)

if __name__ == "__main__":
    main()