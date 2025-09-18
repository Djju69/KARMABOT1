#!/usr/bin/env python3
"""
Check GitHub and Railway integration status
"""
def main():
    print("🔍 CHECKING GITHUB + RAILWAY INTEGRATION")
    print("="*50)

    print("📋 CHECKLIST:")

    print("\n1. 🌐 GITHUB REPO STATUS:")
    print("   - Repository: https://github.com/Djju69/KARMABOT1")
    print("   - Check if latest commits are there")
    print("   - Look for: 'force: Trigger Railway rebuild' commits")

    print("\n2. 🚂 RAILWAY SETTINGS:")
    print("   - Go to: Railway Dashboard -> Settings")
    print("   - GitHub section should show:")
    print("     ✅ Repository: Djju69/KARMABOT1")
    print("     ✅ Branch: main (NOT master)")
    print("     ✅ Connected: Yes")

    print("\n3. 🔗 GITHUB WEBHOOKS:")
    print("   - Go to: https://github.com/Djju69/KARMABOT1/settings/hooks")
    print("   - Should have Railway webhook")
    print("   - If missing: Railway integration is broken")

    print("\n4. 📊 RAILWAY DEPLOYMENTS:")
    print("   - Railway Dashboard -> Deployments")
    print("   - Check latest deployment timestamp")
    print("   - Should match latest GitHub commit time")

    print("\n" + "="*50)
    print("🛠️ TROUBLESHOOTING STEPS:")

    print("\n📋 STEP 1: VERIFY GITHUB COMMITS")
    print("   1. Open: https://github.com/Djju69/KARMABOT1")
    print("   2. Check latest commits")
    print("   3. Look for recent 'force rebuild' commits")
    print("   4. Confirm they exist")

    print("\n📋 STEP 2: CHECK RAILWAY INTEGRATION")
    print("   1. Railway Dashboard -> Settings -> GitHub")
    print("   2. Verify repository connection")
    print("   3. Verify branch is 'main'")
    print("   4. If broken: Disconnect and reconnect")

    print("\n📋 STEP 3: MANUAL DEPLOY TRIGGER")
    print("   1. Make any small change to any file")
    print("   2. Commit: git commit -m 'manual trigger'")
    print("   3. Push: git push origin main")
    print("   4. Wait 2 minutes")
    print("   5. Check Railway deployments")

    print("\n📋 STEP 4: CHECK RAILWAY BUILD LOGS")
    print("   1. Railway -> Deployments -> Latest deployment")
    print("   2. Click 'View Logs'")
    print("   3. Look for Git clone messages")
    print("   4. Should show: 'Cloning from GitHub...'")

    print("\n" + "="*50)
    print("🎯 POSSIBLE ISSUES:")

    print("\n1. 🔀 WRONG BRANCH:")
    print("   - Railway set to 'master', code in 'main'")
    print("   - Fix: Change Railway branch to 'main'")

    print("\n2. 🔗 BROKEN WEBHOOK:")
    print("   - GitHub not notifying Railway of changes")
    print("   - Fix: Delete and recreate webhook")

    print("\n3. 📦 REPO PERMISSIONS:")
    print("   - Railway can't access private repo")
    print("   - Fix: Make repo public or check permissions")

    print("\n4. 🏗️ BUILD CACHE:")
    print("   - Railway using cached old build")
    print("   - Fix: Force rebuild or change Dockerfile")

    print("\n" + "="*50)
    print("⚡ IMMEDIATE ACTION:")
    print("1. Check GitHub commits")
    print("2. Verify Railway Settings")
    print("3. Make manual change and push")
    print("4. Monitor Railway deployments")

    print("\n" + "="*50)
    print("📞 IF STILL BROKEN:")
    print("Contact Railway support with:")
    print("- GitHub repo URL")
    print("- Railway project ID")
    print("- Screenshots of Settings")
    print("- Build logs")

if __name__ == "__main__":
    main()
