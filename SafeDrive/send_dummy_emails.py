import sys
import os

# Add the parent directory to sys.path to import reward_backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from reward_backend.services.email_service import send_rank_upgrade_email

def send_dummy_emails(target_email):
    user_name = "Muhammad Saqlain"
    
    # 🥈 Silver
    print(f"Sending Silver Tier email to {target_email}...")
    send_rank_upgrade_email(target_email, user_name, "Bronze", "Silver")
    
    # 🥇 Gold
    print(f"Sending Gold Tier email to {target_email}...")
    send_rank_upgrade_email(target_email, user_name, "Silver", "Gold")
    
    # 🥉 Bronze (Fallback/Welcome/Demo)
    # The user asked for Bronze too, though usually it's the starting tier. 
    # We'll send it as a 'Welcome' or custom achievement for demo purposes.
    print(f"Sending Bronze Tier email to {target_email}...")
    send_rank_upgrade_email(target_email, user_name, "New Driver", "Bronze")

if __name__ == "__main__":
    target = "saqlain2210nail@gmail.com"
    send_dummy_emails(target)
    print("Done! All dummy emails sent successfully.")
