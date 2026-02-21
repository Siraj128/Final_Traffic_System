import psycopg2
import sys

# New Local Credentials from config/.env
DB_HOST = "localhost"
DB_NAME = "smart_net_db"
DB_USER = "postgres"
DB_PASS = "Siraj.9892"
DB_PORT = "5432"

print(f"Testing connection to local DB: {DB_NAME} as {DB_USER}...")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    print(" [OK] Connection SUCCESS!")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f" [FAIL] Connection FAILED: {e}")
    sys.exit(1)
