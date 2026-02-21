
"""
tools/setup_app_db_postgres.py

This script creates the 'safedrive_apps' PostgreSQL database and its schema.
It replaces the old MongoDB setup for the Mobile App.

Tables Created:
1. users: Stores app user profiles (Separate from RTO registry).
2. vehicles: Stores vehicles linked to app users.
3. transactions: Stores wallet history (Earned, Redeemed, Penalty).
4. notifications: Stores user alerts.
"""

import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.settings import SystemConfig

# Configuration for Admin Connection (to create DB)
DB_CONFIG = SystemConfig.DB_PARAMS
ADMIN_DB = "postgres" # Connect to default DB to create new one
NEW_DB_NAME = "safedrive_apps"

def create_database():
    """Creates the safedrive_apps database if it doesn't exist."""
    print(f">> Connecting to '{ADMIN_DB}' to create '{NEW_DB_NAME}'...")
    
    try:
        conn = psycopg2.connect(
            dbname=ADMIN_DB,
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if DB exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{NEW_DB_NAME}'")
        if not cur.fetchone():
            print(f">> Creating Database '{NEW_DB_NAME}'...")
            cur.execute(f"CREATE DATABASE {NEW_DB_NAME}")
            print(">> Database Created Successfully.")
        else:
            print(f">> Database '{NEW_DB_NAME}' already exists.")
            
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"xx Failed to create database: {e}")
        return False

def create_schema():
    """Connects to the new database and creates tables."""
    print(f">> Connecting to '{NEW_DB_NAME}' to create Schema...")
    
    try:
        conn = psycopg2.connect(
            dbname=NEW_DB_NAME,
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        cur = conn.cursor()
        
        # --- 1. USERS TABLE ---
        print(">> Creating Table: users")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL, -- Storing hashed password
                mobile VARCHAR(20),
                avatar_url TEXT,
                role VARCHAR(20) DEFAULT 'user',
                
                -- Gamification
                wallet_balance DECIMAL(10,2) DEFAULT 0.00,
                total_earned_points INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                tier VARCHAR(20) DEFAULT 'Bronze',
                
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP
            );
        """)

        # --- 2. VEHICLES TABLE ---
        print(">> Creating Table: vehicles")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                plate_number VARCHAR(20) UNIQUE NOT NULL, -- The Link to RTO
                vehicle_type VARCHAR(50) DEFAULT 'Car',
                is_primary BOOLEAN DEFAULT FALSE,
                added_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # --- 3. TRANSACTIONS TABLE ---
        print(">> Creating Table: transactions")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                txn_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                type VARCHAR(20) NOT NULL, -- 'EARNED', 'REDEEMED', 'PENALTY'
                amount DECIMAL(10,2) NOT NULL,
                description TEXT,
                reference_id VARCHAR(100), -- Can be Violation ID or Reward ID
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # --- 4. NOTIFICATIONS TABLE ---
        print(">> Creating Table: notifications")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                noti_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                title VARCHAR(100),
                message TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        conn.commit()
        print(">> Schema Creation Complete.")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"xx Failed to create Schema: {e}")

if __name__ == "__main__":
    if create_database():
        create_schema()
