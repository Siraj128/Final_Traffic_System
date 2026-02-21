
import os
import psycopg2
import time
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load env from parent directory (Traffic_System_Root/.env)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(_PROJECT_ROOT, '.env'))

class CloudDBHandler:
    def __init__(self):
        self.module_name = "DB_HANDLER"
        
        # Cloud Credentials
        self.cloud_host = os.getenv("CLOUD_DB_HOST")
        self.cloud_name = os.getenv("CLOUD_DB_NAME")
        self.cloud_user = os.getenv("CLOUD_DB_USER")
        self.cloud_pass = os.getenv("CLOUD_DB_PASS")
        self.cloud_port = os.getenv("CLOUD_DB_PORT", "5432")
        
        # Local Credentials (Fallback / Edge)
        self.local_host = os.getenv("DB_HOST", "127.0.0.1")
        self.local_name = os.getenv("DB_NAME", "traffic_reward_pro")
        self.local_user = os.getenv("DB_USER", "postgres")
        self.local_pass = os.getenv("DB_PASS", "aynan@2023")
        self.local_port = os.getenv("DB_PORT", "5432")

    def get_cloud_connection(self):
        """Returns connection to DigitalOcean Postgres."""
        if not self.cloud_host:
            print(f"⚠️ [{self.module_name}] Cloud Credentials Missing in .env")
            return None
            
        try:
            conn = psycopg2.connect(
                host=self.cloud_host,
                database=self.cloud_name,
                user=self.cloud_user,
                password=self.cloud_pass,
                port=self.cloud_port,
                sslmode="require",
                connect_timeout=5 
            )
            return conn
        except Exception as e:
            print(f"❌ [{self.module_name}] Cloud Connection Failed: {e}")
            return None

    def get_local_connection(self):
        """Returns connection to Local Edge Postgres."""
        try:
            conn = psycopg2.connect(
                host=self.local_host,
                database=self.local_name,
                user=self.local_user,
                password=self.local_pass,
                port=self.local_port
            )
            return conn
        except Exception as e:
            print(f"❌ [{self.module_name}] Local Connection Failed: {e}")
            return None

    def get_best_connection(self):
        """Tries Cloud, falls back to Local."""
        conn = self.get_cloud_connection()
        if conn: return conn, "CLOUD"
        
        print(f"⚠️ [{self.module_name}] Falling back to Local DB...")
        conn = self.get_local_connection()
        if conn: return conn, "LOCAL"
        
        return None, "NONE"

# Singleton Instance
db = CloudDBHandler()

def get_db_connection():
    """Compatibility wrapper for server.py"""
    conn, source = db.get_best_connection()
    return conn
