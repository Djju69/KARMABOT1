import os
from dotenv import load_dotenv

print("Testing environment variables...")

# Load .env file
load_dotenv()

# Check required variables
required_vars = ["BOT_TOKEN", "DISABLE_WEB_SERVER", "REDIS_URL"]
all_ok = True

for var in required_vars:
    value = os.getenv(var)
    if value is None:
        print(f"[ERROR] {var} is not set")
        all_ok = False
    else:
        print(f"[OK] {var} is set")

if all_ok:
    print("\n[SUCCESS] All required environment variables are set")
    print("You can now run the bot with: python main_v2.py")
else:
    print("\n[ERROR] Some required environment variables are missing")
    print("Please update your .env file with the required variables")
