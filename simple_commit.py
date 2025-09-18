import os
import subprocess

# Change to the project directory
os.chdir(r'C:\Users\d9955\CascadeProjects\KARMABOT1-fixed')

# Run git commands
commands = [
    'git add .',
    'git commit -m "CRITICAL FIX: Fixed IndentationError in migrations.py line 503"',
    'git push origin main'
]

for cmd in commands:
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        print("---")
    except Exception as e:
        print(f"Error: {e}")
        print("---")

print("Done!")