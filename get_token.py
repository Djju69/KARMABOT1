#!/usr/bin/env python3
"""
Script to get bot token from @BotFather
"""

print("="*60)
print("GET BOT TOKEN")
print("="*60)
print()
print("1. Open Telegram")
print("2. Find @BotFather")
print("3. Send /mybots command")
print("4. Select your bot")
print("5. Click 'API Token'")
print("6. Copy the token")
print()
print("Token looks like this:")
print("1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890")
print()

token = input("Paste bot token: ").strip()

if token and ":" in token and len(token) > 20:
    print(f"\nOK: Token received: {token[:10]}...")
    
    # Update .env file
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace or add BOT_TOKEN
        if 'BOT_TOKEN=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('BOT_TOKEN='):
                    lines[i] = f'BOT_TOKEN={token}'
                    break
            content = '\n'.join(lines)
        else:
            content += f'\nBOT_TOKEN={token}\n'
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK: Token saved to .env file")
        
    except Exception as e:
        print(f"ERROR: Save error: {e}")
        print(f"Add to .env file: BOT_TOKEN={token}")
    
    # Update tester
    try:
        with open('test_karmabot_full.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_СЮДА_BOT_TOKEN"', f'BOT_TOKEN = os.getenv("BOT_TOKEN") or "{token}"')
        
        with open('test_karmabot_full.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK: Tester updated")
        
    except Exception as e:
        print(f"ERROR: Tester update error: {e}")
    
    print("\nDone! Now you can run tests:")
    print("python test_karmabot_full.py")
    
else:
    print("ERROR: Invalid token format!")
    print("Token must contain ':' and be longer than 20 characters")
