#!/usr/bin/env python3
"""
Script to get Telegram ID from @userinfobot
"""

print("="*60)
print("GET TELEGRAM ID")
print("="*60)
print()
print("1. Open Telegram")
print("2. Find @userinfobot")
print("3. Send any message")
print("4. Bot will reply with your ID")
print()
print("ID looks like this:")
print("123456789")
print()

user_id = input("Paste your Telegram ID: ").strip()

if user_id.isdigit() and len(user_id) >= 8:
    print(f"\nOK: ID received: {user_id}")
    
    # Update .env file
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace or add TEST_USER_ID
        if 'TEST_USER_ID=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('TEST_USER_ID='):
                    lines[i] = f'TEST_USER_ID={user_id}'
                    break
            content = '\n'.join(lines)
        else:
            content += f'\nTEST_USER_ID={user_id}\n'
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK: ID saved to .env file")
        
    except Exception as e:
        print(f"ERROR: Save error: {e}")
        print(f"Add to .env file: TEST_USER_ID={user_id}")
    
    print("\nDone! Now you can run tests:")
    print("python test_karmabot_full.py")
    
else:
    print("ERROR: Invalid ID format!")
    print("ID must contain only digits and be longer than 7 characters")
