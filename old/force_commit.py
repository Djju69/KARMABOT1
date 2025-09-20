#!/usr/bin/env python3
"""
Force commit to trigger Railway rebuild
"""
import subprocess
import sys

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd='.')
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def main():
    print("🚀 CREATING FORCE COMMIT FOR RAILWAY")
    print("="*50)

    # Create empty commit
    print("📝 Creating empty commit...")
    code, stdout, stderr = run_cmd('git commit --allow-empty -m "force-rebuild: Railway deployment stuck"')
    if code == 0:
        print("✅ Empty commit created")
    else:
        print(f"❌ Failed to create commit: {stderr}")
        return

    # Push to GitHub
    print("📤 Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Pushed to GitHub")
        print("\n🎯 SUCCESS!")
        print("Railway should now rebuild automatically")
        print("Check Railway logs in 5-10 minutes")
    else:
        print(f"❌ Failed to push: {stderr}")

    print("\n" + "="*50)
    print("📋 EXPECTED RESULT:")
    print("✅ Railway detects new commit")
    print("✅ Automatic rebuild starts")
    print("✅ New logs should appear with fixes")

if __name__ == "__main__":
    main()
