import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus

def create_connection_postgresql():
    """Create PostgreSQL connection engine"""
    print("🛜  Connecting to the database...")
    
    # Load environment variables from .env file
    load_dotenv()

    # Get environment variables
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME')
    
    # Check if all required variables are set
    if not all([db_user, db_pass, db_name]):
        missing = [var for var, val in [
            ('DB_USER', db_user),
            ('DB_PASS', db_pass),
            ('DB_NAME', db_name)
        ] if not val]
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    # URL-encode password to handle special characters
    encoded_password = quote_plus(db_pass)
    
    # Build the PostgreSQL connection string
    DB_URL = f"postgresql://{db_user}:{encoded_password}@{db_host}:5432/{db_name}"
    
    print(f"   Connecting to: {db_user}@{db_host}:5432/{db_name}")

    try:
        # Create the engine object for connecting
        engine = create_engine(DB_URL)
        
        # Test the connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        print("   ✅ Database connection established.")
        return engine
    
    except Exception as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            print(f"   ❌ Authentication failed for user '{db_user}'")
            print("   💡 Please check your DB_PASS in the .env file")
            print("   💡 Make sure there are no extra spaces or quotes in the password")
        elif "could not connect" in error_msg.lower() or "connection refused" in error_msg.lower():
            print(f"   ❌ Could not connect to PostgreSQL at {db_host}:5432")
            print("   💡 Make sure PostgreSQL is running")
            print("   💡 Check your DB_HOST in the .env file")
        else:
            print(f"   ❌ Connection error: {error_msg}")
        raise

