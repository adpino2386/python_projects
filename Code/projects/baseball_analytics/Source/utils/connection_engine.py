import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlalchemy import text
from pathlib import Path

def create_connection_postgresql():
    print("🛜  Connecting to the database...")
    
    # Load environment variables from .env file
    # Try to find .env file in utils folder (relative to this file)
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=True)
    else:
        # Fallback to default load_dotenv behavior
        load_dotenv()
    
    # Build the PostgreSQL connection string
    DB_URL = f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}:5432/{os.environ['DB_NAME']}"
    
    # Create the engine object for connecting
    engine = create_engine(DB_URL)
    
    print("   ✅ Database connection established.")
    
    return engine