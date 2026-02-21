import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import html

from utils.config import Config

# Configuration
SMTP_SERVER = Config.SMTP_SERVER
SMTP_PORT = Config.SMTP_PORT
SENDER_EMAIL = Config.SENDER_EMAIL
SENDER_PASSWORD = Config.SENDER_PASSWORD

def send_rank_upgrade_email(user_email, user_name, old_rank, new_rank):
    """Sends a professional HTML email when a driver upgrades their rank."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🌟 Achievement Unlocked: Welcome to {new_rank} Tier!"
        msg["From"] = f"SafeDrive Rewards <{SENDER_EMAIL}>"
        msg["To"] = user_email

        safe_name = html.escape(user_name)

        # Tier Colors
        tier_colors = {
            "Bronze": "#CD7F32",
            "Silver": "#C0C0C0",
            "Gold": "#FFD700",
            "Platinum": "#E5E4E2"
        }
        accent_color = tier_colors.get(new_rank, "#3B82F6")

        html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, {accent_color} 0%, #1e293b 100%); padding: 40px 20px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 28px;">Rank Upgraded!</h1>
                    <p style="font-size: 18px; opacity: 0.9;">Congratulations, {safe_name}!</p>
                </div>
                <div style="padding: 30px; line-height: 1.6; color: #333333;">
                    <p>We've noticed your exceptional driving behavior recently. Your commitment to safety has officially leveled you up!</p>
                    
                    <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; border-left: 5px solid {accent_color};">
                        <span style="display: block; font-size: 14px; color: #64748b; text-transform: uppercase;">Previous Tier</span>
                        <strong style="font-size: 20px; color: #94a3b8;">{old_rank}</strong>
                        <div style="margin: 10px 0; font-size: 24px;">⬇️</div>
                        <span style="display: block; font-size: 14px; color: #64748b; text-transform: uppercase;">New Achievement</span>
                        <strong style="font-size: 28px; color: {accent_color};">{new_rank}</strong>
                    </div>

                    <p>As a <strong>{new_rank}</strong> member, you now unlock:</p>
                    <ul style="padding-left: 20px;">
                        <li>Increased reward points multiplier</li>
                        <li>Exclusive cashback offers on FASTag</li>
                        <li>Priority support in the SafeDrive Assistant</li>
                    </ul>

                    <p style="margin-top: 30px;">Keep driving safe and aim for the next level!</p>
                    
                    <div style="text-align: center; margin-top: 40px;">
                        <a href="#" style="background-color: {accent_color}; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">View My Rewards</a>
                    </div>
                </div>
                <div style="background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #64748b;">
                    &copy; 2026 SafeDrive Rewards. All rights reserved.<br>
                    You received this because your driving score improved.
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
