import os
import json
import sys

# Set console output encoding to UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def create_default_railway_json():
    """Create a default railway.json configuration."""
    default_config = {
        "$schema": "https://railway.app/railway.schema.json",
        "build": {
            "builder": "nixpacks",
            "buildCommand": "pip install -r requirements.txt"
        },
        "deploy": {
            "startCommand": "python -m uvicorn web.main:app --host 0.0.0.0 --port $PORT",
            "healthCheckPath": "/health",
            "healthcheckTimeout": 30,
            "restartPolicyType": "ON_FAILURE"
        }
    }
    
    with open('railway.json', 'w') as f:
        json.dump(default_config, f, indent=2)
    print("[OK] Created default railway.json")
    return default_config

def fix_common_issues():
    """Fix common deployment issues."""
    issues_fixed = 0
    
    # 1. Ensure runtime.txt exists and is valid
    if not os.path.exists('runtime.txt'):
        with open('runtime.txt', 'w', encoding='utf-8') as f:
            f.write('3.11.9\n')
        print("[OK] Created runtime.txt with Python 3.11.9")
        issues_fixed += 1
    
    # 2. Validate railway.json
    if not os.path.exists('railway.json'):
        print(" railway.json not found, creating default configuration")
        create_default_railway_json()
        issues_fixed += 1
    else:
        try:
            with open('railway.json', 'r') as f:
                data = json.load(f)
                
            needs_update = False
            
            # Ensure required sections exist
            if 'build' not in data:
                data['build'] = {"builder": "nixpacks"}
                needs_update = True
                
            if 'deploy' not in data:
                data['deploy'] = {}
                needs_update = True
                
            # Ensure required deploy settings
            deploy = data['deploy']
            if 'startCommand' not in deploy:
                deploy['startCommand'] = "python -m uvicorn web.main:app --host 0.0.0.0 --port $PORT"
                needs_update = True
                
            if 'healthCheckPath' not in deploy:
                deploy['healthCheckPath'] = "/health"
                needs_update
                
            if needs_update:
                with open('railway.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("[OK] Updated railway.json with required settings")
                issues_fixed += 1
                
        except json.JSONDecodeError:
            print("[ERROR] Invalid railway.json, creating default configuration")
            create_default_railway_json()
            issues_fixed += 1
    
    # 3. Check requirements.txt
    if not os.path.exists('requirements.txt'):
        print("[ERROR] requirements.txt not found! Please create one with your dependencies.")
        return False
    
    if issues_fixed > 0:
        print(f"\n[OK] Fixed {issues_fixed} issues")
    else:
        print("[OK] No common issues found")
    
    return True

if __name__ == "__main__":
    print("=== Fixing common deployment issues...")
    success = fix_common_issues()
    sys.exit(0 if success else 1)
