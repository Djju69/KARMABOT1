import subprocess
import sys

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Command: {cmd}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    print("Committing IndentationError fix...")
    
    # Add files
    if not run_command("git add ."):
        print("Failed to add files")
        return False
    
    # Commit
    commit_msg = "CRITICAL FIX: Fixed IndentationError in migrations.py line 503"
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("Failed to commit")
        return False
    
    # Push
    if not run_command("git push origin main"):
        print("Failed to push")
        return False
    
    print("Successfully committed and pushed fix!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
