import sys
import os
import time

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from cms_layer.cloud_db_handler import get_db_connection

def verify_rewards():
    print("\n" + "="*50)
    print(" [VERIFYING REWARD DATABASE]")
    print("="*50)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to Database.")
        return

    try:
        cur = conn.cursor()
        
        # 1. Check Total Count
        cur.execute("SELECT COUNT(*) FROM user_rewards")
        count = cur.fetchone()[0]
        print(f"\n📊 Total Tracked Plates: {count}")
        
        # 2. Get Recent Updates
        print("\n🏆 Top 10 Most Recently Credited Vehicles:")
        print("-" * 65)
        print(f"{'PLATE':<15} | {'POINTS':<10} | {'TYPE':<10} | {'LAST UPDATED'}")
        print("-" * 65)
        
        cur.execute("""
            SELECT plate_number, reward_points, vehicle_type, last_updated 
            FROM user_rewards 
            ORDER BY last_updated DESC 
            LIMIT 10
        """)
        
        rows = cur.fetchall()
        for row in rows:
            plate, points, vtype, updated = row
            # Format time
            time_str = updated.strftime("%H:%M:%S") if updated else "N/A"
            print(f"{plate:<15} | {points:<10} | {vtype:<10} | {time_str}")
            
        print("-" * 65)
        print("\n✅ Verification Complete.")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    while True:
        verify_rewards()
        print("\n🔄 Refreshing in 5 seconds... (Ctrl+C to stop)")
        time.sleep(5)
