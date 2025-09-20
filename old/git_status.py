#!/usr/bin/env python3
import subprocess
import os

def main():
    """Check git status and save to file"""
    try:
        # Check git status
        result = subprocess.run(['git', 'status'], capture_output=True, text=True, encoding='utf-8')
        
        # Save output to file
        with open('git_status_output.txt', 'w', encoding='utf-8') as f:
            f.write(f"Exit code: {result.returncode}\n")
            f.write(f"Output:\n{result.stdout}\n")
            if result.stderr:
                f.write(f"Error:\n{result.stderr}\n")
        
        print("Git status saved to git_status_output.txt")
        
        # Check if we're up to date with remote
        result2 = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True, encoding='utf-8')
        with open('git_log_output.txt', 'w', encoding='utf-8') as f:
            f.write(f"Recent commits:\n{result2.stdout}\n")
        
        print("Git log saved to git_log_output.txt")
        
    except Exception as e:
        with open('git_error.txt', 'w', encoding='utf-8') as f:
            f.write(f"Error: {e}\n")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
