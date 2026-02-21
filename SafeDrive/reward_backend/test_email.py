from services.email_service import send_rank_upgrade_email

if __name__ == "__main__":
    # Test Data
    test_email = "saqlain2210naik@gmail.com" # Default test recipient
    test_name = "Muhammad Saqlain"
    
    print(f"Attempting to send test rank upgrade email to {test_email}...")
    
    success = send_rank_upgrade_email(
        user_email=test_email,
        user_name=test_name,
        old_rank="Bronze",
        new_rank="Silver"
    )
    
    if success:
        print("[SUCCESS] Test email sent successfully!")
    else:
        print("[FAILED] Failed to send test email. Please check your App Password and Internet connection.")
