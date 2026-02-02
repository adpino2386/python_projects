import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.engine import Engine

def create_connection_postgresql():
    """Create PostgreSQL connection engine"""
    print("🛜  Connecting to the database...")
    
    # Load environment variables from .env file
    load_dotenv()

    # Build the PostgreSQL connection string
    DB_URL = f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}:5432/{os.environ['DB_NAME']}"

    # Create the engine object for connecting
    engine = create_engine(DB_URL)

    print("   ✅ Database connection established.")
    
    return engine

