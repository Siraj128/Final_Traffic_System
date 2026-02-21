import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add parent dir to path to import cloud_db_handler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def fix_schema():
    print("Fixing Database Schema...")
    
    # Connect using env variables directly for reliability
    host = os.getenv("CLOUD_DB_HOST")
    dbname = os.getenv("CLOUD_DB_NAME")
    user = os.getenv("CLOUD_DB_USER")
    password = os.getenv("CLOUD_DB_PASS")
    port = os.getenv("CLOUD_DB_PORT", "5432")

    if not all([host, dbname, user, password]):
        print("Error: Missing Cloud DB credentials in .env")
        return

    try:
        conn = psycopg2.connect(
            host=host,
            database=dbname,
            user=user,
            password=password,
            port=port,
            sslmode='require'
        )
        cur = conn.cursor()
        
        print("Checking/Adding column 'updated_at' to 'user_rewards'...")
        # Check if column exists first to avoid error
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='user_rewards' AND column_name='updated_at') THEN
                    ALTER TABLE user_rewards ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        conn.commit()
        print("Success: Column verified/added successfully!")
        
    except Exception as e:
        print(f"Error: Fix Failed: {e}")
    finally:
        if 'conn' in locals():
            cur.close()
            conn.close()

if __name__ == "__main__":
    fix_schema()
