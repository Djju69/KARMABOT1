import os
import sys
import json

def print_section(title):
    print(f"\n{'-'*50}")
    print(f"{title.upper()}")
    print(f"{'-'*50}")

def print_token_info(label, token):
    print(f"\n{label}:")
    print(f"  Type: {type(token)}")
    print(f"  Length: {len(token) if token else 0}")
    print(f"  Value (raw): {token!r}")
    if token:
        print(f"  First 10 chars: {token[:10]!r}")
        print(f"  Last 10 chars: {token[-10:]!r}")
        print(f"  Contains ':': {':' in token}")
        if ':' in token:
            parts = token.split(':', 1)
            print(f"  Bot ID: {parts[0]}")
            print(f"  Hash part: {parts[1][:3]}...{parts[1][-3:] if len(parts[1]) > 6 else ''}")

# Set environment variable for testing
test_token = "ваш_новый_токен"
os.environ["BOTS__BOT_TOKEN"] = test_token
os.environ["ENVIRONMENT"] = "development"

print("Testing token handling...")
print(f"Python version: {sys.version}")
print(f"Default encoding: {sys.getdefaultencoding()}")
print(f"Filesystem encoding: {sys.getfilesystemencoding()}")

# Test 1: Check environment variable
print_section("Environment Variable")
token_from_env = os.getenv("BOTS__BOT_TOKEN")
print_token_info("Token from environment", token_from_env)

# Print raw bytes for inspection
print("\nRaw bytes:")
print(f"  Hex: {token_from_env.encode('utf-8').hex() if token_from_env else ''}")
print(f"  ASCII: {token_from_env.encode('ascii', errors='replace').decode('ascii') if token_from_env else ''}")

# Test 2: Check settings
print_section("Settings")
try:
    from core.config import Settings, load_settings
    settings = load_settings()
    print(f"Settings loaded successfully")
    print(f"Settings object: {settings}")
    
    if hasattr(settings, 'bots') and hasattr(settings.bots, 'bot_token'):
        print_token_info("Token from settings", settings.bots.bot_token)
    else:
        print("❌ No bot token found in settings")
    
except Exception as e:
    print(f"❌ Error loading settings: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

# Test 3: Compare tokens
print_section("Token Comparison")
if 'token_from_env' in locals() and hasattr(settings, 'bots') and hasattr(settings.bots, 'bot_token'):
    print(f"Environment token == Settings token: {token_from_env == settings.bots.bot_token}")
    print(f"Environment token type: {type(token_from_env)}")
    print(f"Settings token type: {type(settings.bots.bot_token)}")
    
    # Compare lengths
    print(f"Environment token length: {len(token_from_env) if token_from_env else 0}")
    print(f"Settings token length: {len(settings.bots.bot_token) if settings.bots.bot_token else 0}")
    
    # Compare character by character
    if token_from_env and settings.bots.bot_token:
        print("\nCharacter comparison:")
        for i, (e, s) in enumerate(zip(token_from_env, settings.bots.bot_token)):
            if e != s:
                print(f"  Mismatch at position {i}: '{e}' (env) != '{s}' (settings)")
                print(f"  Env char: {ord(e)} (0x{ord(e):x})")
                print(f"  Settings char: {ord(s)} (0x{ord(s):x})")
                break
        else:
            print("  All characters match")
else:
    print("❌ Cannot compare tokens - one or both are missing")
