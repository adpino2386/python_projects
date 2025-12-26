import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlalchemy import text
from pathlib import Path

def create_connection_postgresql():
    print("🛜  Connecting to the database...")
    
    # Load environment variables from .env file
    # Try multiple locations (since .env location may vary)
    current_file = Path(__file__)
    source_dir = current_file.parent.parent  # Go up from utils to Source
    app_dir = source_dir / "app"
    
    env_paths = [
        current_file.parent / ".env",        # Source/utils/.env
        app_dir / "utils" / ".env",          # Source/app/utils/.env
        source_dir / ".env",                 # Source/.env
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path), override=True)
            env_loaded = True
            print(f"   📄 Loaded .env from: {env_path}")
            break
    
    if not env_loaded:
        # Fallback to default load_dotenv behavior
        load_dotenv(override=True)
        print("   ⚠️  Using default .env location")
    
    # Build the PostgreSQL connection string
    DB_URL = f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}:5432/{os.environ['DB_NAME']}"
    
    # Create the engine object for connecting
    engine = create_engine(DB_URL)
    
    print("   ✅ Database connection established.")
    
    return engine