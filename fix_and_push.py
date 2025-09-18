import subprocess
import sys

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Command: {cmd}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    print("🔧 Fixing personal cabinet database and import errors...")
    
    # Add all changes
    if not run_command("git add ."):
        print("❌ Failed to add changes")
        return
    
    # Commit changes
    commit_msg = """FIX: Personal cabinet database and import errors

- Fixed migration 016 to create users table if not exists
- Fixed import errors: spend_points -> subtract_karma, add_points -> add_karma
- Added get_or_create_user function
- Fixed function parameter names: description -> reason
- Personal cabinet should now work without errors"""
    
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("❌ Failed to commit changes")
        return
    
    # Push changes
    if not run_command("git push origin main"):
        print("❌ Failed to push changes")
        return
    
    print("✅ All changes committed and pushed successfully!")
    print("🚀 Personal cabinet should now work!")

if __name__ == "__main__":
    main()
