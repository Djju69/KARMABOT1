import requests
import sys
import time

# Set console output encoding to UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_health_check():
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"\n[CHECK] Health check attempt {attempt + 1}/{max_retries}")
            
            # Test local health check
            local_url = 'http://localhost:8000/health'
            print(f"Testing local health check at {local_url}...")
            response = requests.get(local_url, timeout=10)
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text[:200]}...")  # Print first 200 chars
            
            if response.status_code == 200:
                data = response.json()
            else:
                print(f"[ERROR] Health check failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Connection error: {e}")
            
        if attempt < max_retries - 1:
            print(f"[INFO] Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    return False

if __name__ == "__main__":
    print("=== Starting health check...")
    success = test_health_check()
    sys.exit(0 if success else 1)
