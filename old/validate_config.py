import json
import os
import sys

# Set console output encoding to UTF-8
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def validate_runtime():
    try:
        with open('runtime.txt', 'r') as f:
            content = f.read().strip()
            if not content:
                raise ValueError("runtime.txt is empty")
            if not content[0].isdigit():
                raise ValueError("runtime.txt should start with version number")
            print(f"✅ runtime.txt is valid. Python version: {content}")
            return True
    except Exception as e:
        print(f"❌ Error in runtime.txt: {e}")
        return False

def validate_railway():
    try:
        with open('railway.json', 'r') as f:
            data = json.load(f)
            required_sections = ['build', 'deploy']
            for section in required_sections:
                if section not in data:
                    raise ValueError(f"Missing required section: {section}")
            print("✅ railway.json is valid")
            return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in railway.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in railway.json: {e}")
        return False

def validate_requirements():
    try:
        with open('requirements.txt', 'r') as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if not packages:
                raise ValueError("No packages found in requirements.txt")
            print(f"✅ Found {len(packages)} packages in requirements.txt")
            return True
    except Exception as e:
        print(f"❌ Error in requirements.txt: {e}")
        return False

if __name__ == "__main__":
    print("=== Starting configuration validation...")
    results = [
        ("runtime.txt", validate_runtime()),
        ("railway.json", validate_railway()),
        ("requirements.txt", validate_requirements())
    ]
    
    if all(result[1] for result in results):
        print("\n[SUCCESS] All configurations are valid!")
        sys.exit(0)
    else:
        print("\n[ERROR] Some configurations are invalid. Please fix the issues above.")
        sys.exit(1)
