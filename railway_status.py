#!/usr/bin/env python3
"""
Check Railway deployment status via GitHub Actions
"""
import subprocess
import sys
import time

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd='.')
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def main():
    print("🚀 Checking Railway deployment status...\n")

    # Check recent commits
    print("📋 Recent commits:")
    code, stdout, stderr = run_cmd("git log --oneline -3")
    if code == 0:
        print(stdout)
    else:
        print(f"❌ Git log failed: {stderr}")

    print("\n" + "="*50)
    print("🎯 NEXT STEPS:")
    print("1. Open: https://github.com/Djju69/KARMABOT1/actions")
    print("2. Check latest workflow run")
    print("3. Wait for Railway deployment (5-7 minutes)")
    print("4. Check Railway logs for:")
    print("   ✅ BOT_TOKEN detection logs")
    print("   ✅ Webhook cleanup messages")
    print("   ✅ Bot startup success")

if __name__ == "__main__":
    main()
