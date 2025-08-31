import os
import sys
from dotenv import load_dotenv

# Set console output to UTF-8
if sys.platform == 'win32':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load environment variables from .env file
load_dotenv()

# Path to .env file
env_file = '.env'

# Read existing .env file if it exists
env_vars = {}
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value

# Enable partner FSM feature
env_vars['FEATURE_PARTNER_FSM'] = 'true'

# Write back to .env file
with open(env_file, 'w', encoding='utf-8') as f:
    for key, value in env_vars.items():
        f.write(f"{key}={value}\n")

print("[SUCCESS] Partner FSM feature has been enabled in .env file")
