"""
Test script to verify PostgreSQL database connection
Run this to troubleshoot connection issues
"""
import os
from dotenv import load_dotenv
from utils.connection_engine import create_connection_postgresql

def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    
    # Load .env file
    load_dotenv()
    
    # Check if .env file exists and show what's loaded
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"✅ Found .env file: {os.path.abspath(env_file)}")
    else:
        print(f"❌ .env file not found at: {os.path.abspath(env_file)}")
        print("   Please create a .env file with your database credentials")
        return
    
    # Show what variables are set (without showing passwords)
    print("\nEnvironment variables:")
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME')
    
    print(f"  DB_USER: {db_user if db_user else '❌ NOT SET'}")
    print(f"  DB_PASS: {'✅ SET' if db_pass else '❌ NOT SET'} ({'*' * len(db_pass) if db_pass else ''})")
    print(f"  DB_HOST: {db_host}")
    print(f"  DB_NAME: {db_name if db_name else '❌ NOT SET'}")
    
    if not all([db_user, db_pass, db_name]):
        print("\n❌ Missing required environment variables!")
        print("   Please check your .env file")
        return
    
    # Test connection
    print("\n" + "=" * 60)
    try:
        engine = create_connection_postgresql()
        print("\n✅ SUCCESS! Database connection is working!")
        
        # Test a simple query (SQLAlchemy 2.0 requires text() wrapper)
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"\n📊 PostgreSQL Version: {version.split(',')[0]}")
        
    except Exception as e:
        print(f"\n❌ FAILED! Error: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Verify your PostgreSQL is running:")
        print("      - Windows: Check Services or run 'pg_ctl status'")
        print("      - Linux/Mac: 'sudo systemctl status postgresql' or 'brew services list'")
        print("   2. Verify your credentials:")
        print("      - Try connecting with psql: psql -U your_username -d your_database")
        print("   3. Check your .env file:")
        print("      - Make sure there are no quotes around values")
        print("      - Make sure there are no extra spaces")
        print("      - Special characters in password may need URL encoding")
        print("   4. Check PostgreSQL is listening on port 5432:")
        print("      - Windows: netstat -an | findstr 5432")
        print("      - Linux/Mac: netstat -an | grep 5432")

if __name__ == "__main__":
    test_connection()

