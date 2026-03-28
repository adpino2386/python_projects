import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus
from pathlib import Path

def create_connection_postgresql():
    """Create PostgreSQL connection engine"""
    print("🛜  Connecting to the database...")
    
    # Try to find .env file in multiple locations
    current_dir = Path(__file__).parent.parent  # Go up from utils/ to project root
    env_paths = [
        current_dir / '.env',
        Path.cwd() / '.env',
        Path('.env')
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path), override=True)
            print(f"   📄 Loaded .env from: {env_path}")
            env_loaded = True
            break
    
    if not env_loaded:
        # Try default location
        load_dotenv()
        print("   ⚠️  Using default .env loading (may not find file)")

    # Get environment variables
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME')
    
    # Debug: Show what we got (without showing full password)
    print(f"   📋 DB_USER: {db_user}")
    print(f"   📋 DB_PASS: {'✅ Set' if db_pass else '❌ Not set'} (length: {len(db_pass) if db_pass else 0})")
    print(f"   📋 DB_HOST: {db_host}")
    print(f"   📋 DB_NAME: {db_name}")
    
    # Check if all required variables are set
    if not all([db_user, db_pass, db_name]):
        missing = [var for var, val in [
            ('DB_USER', db_user),
            ('DB_PASS', db_pass),
            ('DB_NAME', db_name)
        ] if not val]
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    # Check for common issues
    if db_pass.startswith('"') and db_pass.endswith('"'):
        print("   ⚠️  WARNING: Password appears to have quotes! Removing them...")
        db_pass = db_pass.strip('"').strip("'")
    if db_pass.startswith("'") and db_pass.endswith("'"):
        print("   ⚠️  WARNING: Password appears to have single quotes! Removing them...")
        db_pass = db_pass.strip("'").strip('"')
    
    # URL-encode password to handle special characters (!#$ etc.)
    encoded_password = quote_plus(db_pass)
    
    # Build the PostgreSQL connection string using SQLAlchemy URL
    # This is more reliable than string formatting
    from sqlalchemy.engine.url import URL
    db_url = URL.create(
        drivername="postgresql",
        username=db_user,
        password=db_pass,  # SQLAlchemy will handle encoding
        host=db_host,
        port=5432,
        database=db_name
    )
    
    print(f"   🔗 Connecting to: {db_user}@{db_host}:5432/{db_name}")

    try:
        # Create the engine object for connecting
        engine = create_engine(db_url, pool_pre_ping=True)
        
        # Test the connection
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        
        print("   ✅ Database connection established.")
        return engine
    
    except Exception as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            print(f"   ❌ Authentication failed for user '{db_user}'")
            print("   💡 Please check your DB_PASS in the .env file")
            print("   💡 Make sure there are no extra spaces or quotes in the password")
            print("   💡 Try connecting with: psql -U {} -d {}".format(db_user, db_name))
        elif "could not connect" in error_msg.lower() or "connection refused" in error_msg.lower():
            print(f"   ❌ Could not connect to PostgreSQL at {db_host}:5432")
            print("   💡 Make sure PostgreSQL is running")
            print("   💡 Check your DB_HOST in the .env file")
        else:
            print(f"   ❌ Connection error: {error_msg}")
        raise

