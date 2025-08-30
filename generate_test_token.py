import os
import random
import string

def generate_test_token():
    """Generate a test token in the format '1234567890:ABCdefGHIjklmNOPQRSTUVWXYZ0123456789'"""
    # Generate a random 10-digit number for the bot ID
    bot_id = ''.join(random.choices(string.digits, k=10))
    
    # Generate a random 35-character string for the token hash
    chars = string.ascii_letters + string.digits
    token_hash = ''.join(random.choices(chars, k=35))
    
    # Combine into a token
    token = f"{bot_id}:{token_hash}"
    return token

if __name__ == "__main__":
    test_token = generate_test_token()
    print(f"Generated test token: {test_token}")
    print("\nTo use this token, run:")
    print(f'set BOTS__BOT_TOKEN="{test_token}"')
    print("python main_v2.py")
