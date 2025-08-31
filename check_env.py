#!/usr/bin/env python3
import os
import sys

def check_environment():
    try:
        # Set console output encoding to UTF-8 if on Windows
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
        port = os.getenv("PORT")
        print(f"PORT environment variable: {port}")
        print(f"Type: {type(port)}")
        
        if port is None:
            print("[ERROR] PORT is not set")
            return False
            
        try:
            port_int = int(port)
            if 1 <= port_int <= 65535:
                print(f"[OK] PORT is valid: {port_int}")
                return True
            else:
                print(f"[ERROR] PORT {port_int} is out of valid range (1-65535)")
                return False
                
        except ValueError:
            print(f"[ERROR] PORT must be a number, got: {port}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    sys.exit(0 if check_environment() else 1)
