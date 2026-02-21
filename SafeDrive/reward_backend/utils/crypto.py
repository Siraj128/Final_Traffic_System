from cryptography.fernet import Fernet
from utils.config import Config
import random

# Initialize Fernet with the key from config
cipher_suite = Fernet(Config.FERNET_KEY.encode())

def encrypt_data(data: str) -> str:
    if not data:
        return ""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data:
        return ""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

def generate_luhn_card_number(prefix: str = "4587") -> str:
    """Generates a 16-digit card number that passes the Luhn check."""
    # Generate 15 digits
    digits = [int(d) for d in prefix.strip().replace(" ", "")]
    while len(digits) < 15:
        digits.append(random.randint(0, 9))
    
    # Calculate checksum digit
    total = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    
    checksum = (10 - (total % 10)) % 10
    digits.append(checksum)
    
    # Format as 4-4-4-4
    card_num = "".join(map(str, digits))
    return f"{card_num[:4]} {card_num[4:8]} {card_num[8:12]} {card_num[12:]}"

def validate_luhn(card_number: str) -> bool:
    """Validates a card number using the Luhn algorithm."""
    digits = [int(d) for d in card_number.replace(" ", "") if d.isdigit()]
    if not digits:
        return False
    
    checksum = digits.pop()
    total = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    
    return (total + checksum) % 10 == 0
