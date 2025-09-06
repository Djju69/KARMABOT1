#!/usr/bin/env python3
"""
Test bot token validity
"""
import os
import requests

def test_bot_token():
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ BOT_TOKEN not found")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('ok'):
            print(f"✅ Bot token is valid: {data['result']['first_name']}")
            print(f"   Username: @{data['result']['username']}")
            print(f"   ID: {data['result']['id']}")
            return True
        else:
            print(f"❌ Bot token is invalid: {data.get('description', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Error testing bot token: {e}")
        return False

if __name__ == "__main__":
    test_bot_token()
