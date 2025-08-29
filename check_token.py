import os
import sys
import platform

def mask(t: str | None) -> str:
    """Mask sensitive token data for logging."""
    if not t:
        return "<none>"
    t = t.strip()
    if len(t) <= 14:
        return "<too_short>"
    return f"{t[:4]}...{t[-4:]}"  # Show first 4 and last 4 chars

def get_windows_env_vars():
    """Get environment variables on Windows."""
    import subprocess
    try:
        # Use 'set' command to get all environment variables
        result = subprocess.run(['cmd', '/c', 'set'], 
                              capture_output=True, 
                              text=True,
                              shell=True)
        if result.returncode == 0:
            return dict(
                line.split('=', 1) 
                for line in result.stdout.splitlines() 
                if '=' in line
            )
    except Exception as e:
        print(f"Error getting Windows env vars: {e}")
    return {}

def check_token_validity(token: str) -> tuple[bool, str]:
    """Check if the token is valid by calling Telegram API."""
    import requests
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                return True, f"✅ Valid token for @{data['result'].get('username', 'unknown')}"
            return False, f"❌ Invalid token: {data.get('description', 'Unknown error')}"
        return False, f"❌ HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"❌ Error testing token: {e}"

def main():
    print("=" * 50)
    print("Telegram Bot Token Checker")
    print("=" * 50)
    
    # Get all environment variables
    env_vars = os.environ.copy()
    if platform.system() == 'Windows':
        env_vars.update(get_windows_env_vars())
    
    # Look for potential bot token variables
    token_vars = {}
    for var in env_vars:
        var_upper = var.upper()
        if any(x in var_upper for x in ['TOKEN', 'BOT', 'TELEGRAM']):
            token_vars[var] = env_vars[var]
    
    # Check BOTS__BOT_TOKEN specifically
    main_token = env_vars.get('BOTS__BOT_TOKEN')
    
    print("\n=== Token Check ===")
    print(f"BOTS__BOT_TOKEN: {mask(main_token) if main_token else '<not set>'}")
    if main_token:
        print(f"  - Length: {len(main_token)} characters")
        print(f"  - repr: {repr(main_token)}")
        print(f"  - Starts with: {main_token[:10]}...")
        print(f"  - Ends with: ...{main_token[-10:] if len(main_token) > 10 else main_token}")
        
        # Check token validity
        print("\n=== Testing Token Validity ===")
        is_valid, message = check_token_validity(main_token)
        print(message)
    
    # Show other potential token variables
    if token_vars:
        print("\n=== Other Potential Token Variables ===")
        for var, value in token_vars.items():
            if var != 'BOTS__BOT_TOKEN':
                print(f"{var}: {mask(value)} (length: {len(value)})")
    else:
        print("\nNo other token-like variables found in environment.")
    
    # Check for .env files
    print("\n=== Checking for .env files ===")
    env_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.lower().endswith('.env'):
                env_files.append(os.path.join(root, file))
    
    if env_files:
        print("Found .env files:")
        for env_file in env_files:
            print(f"- {env_file}")
    else:
        print("No .env files found in the project.")
    
    print("\n" + "=" * 50)
    if not main_token:
        print("❌ BOTS__BOT_TOKEN is not set in environment variables")
    print("=" * 50)

if __name__ == "__main__":
    main()
