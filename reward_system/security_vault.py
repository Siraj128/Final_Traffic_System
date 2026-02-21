# security_vault.py
import hashlib
import hmac
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import SystemConfig

class SecurityVault:
    @staticmethod
    def generate_signature(data_string):
        """Creates a unique HMAC-SHA256 signature for data."""
        return hmac.new(
            SystemConfig.SYSTEM_SECRET.encode(),
            data_string.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_integrity(data_string, provided_signature):
        """Checks if the data has been tampered with."""
        if not provided_signature: return False
        expected_signature = SecurityVault.generate_signature(data_string)
        return hmac.compare_digest(expected_signature, provided_signature)

    @staticmethod
    def create_seal(plate_id, lifetime_credits, available_wallet):
        """Generates a secure seal for the driver's financial data."""
        data = f"{plate_id}:{lifetime_credits}:{available_wallet}"
        return SecurityVault.generate_signature(data)

    @staticmethod
    def is_seal_broken(plate_id, lifetime_credits, available_wallet, seal):
        """Verifies if the stored data matches the seal."""
        data = f"{plate_id}:{lifetime_credits}:{available_wallet}"
        return not SecurityVault.verify_integrity(data, seal)