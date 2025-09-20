#!/usr/bin/env python3
"""
Rollback to working deployment
"""
def main():
    print("⏪ ROLLBACK TO WORKING DEPLOYMENT")
    print("="*50)

    print("🎯 STRATEGY:")
    print("Rollback to 2-day-old working version")
    print("Test if Railway accepts the rollback")
    print("Then gradually re-add fixes")

    print("\n" + "="*50)
    print("📋 FIND WORKING COMMIT:")

    print("\n1. Check GitHub commits:")
    print("   - Go to: https://github.com/Djju69/KARMABOT1")
    print("   - Look at commit history")
    print("   - Find commit from 2 days ago")
    print("   - Copy commit hash")

    print("\n2. Or use git log:")
    print("   git log --oneline --since='2 days ago'")
    print("   # Find the commit hash")

    print("\n" + "="*50)
    print("🔄 ROLLBACK STEPS:")

    print("\n📋 STEP 1: RESET TO WORKING COMMIT")
    print("   git reset --hard [COMMIT_HASH]")
    print("   git push --force origin main")

    print("\n📋 STEP 2: CHECK RAILWAY")
    print("   - Wait for Railway to rebuild")
    print("   - Check if old version works")
    print("   - Look for successful webhook mode")

    print("\n📋 STEP 3: VERIFY WORKING STATE")
    print("   - Should see in logs:")
    print("     ✅ 'Railway detected, using webhook'")
    print("     ✅ Router imports working")
    print("     ✅ Bot started in webhook mode")

    print("\n" + "="*50)
    print("🔧 IF ROLLBACK WORKS:")

    print("\n📋 STEP 4: GRADUAL FIXES")
    print("1. Test current working state")
    print("2. Add ONE fix at a time:")
    print("   - Fix router imports")
    print("   - Add debug messages")
    print("   - Test each change")
    print("3. Commit and push after each fix")
    print("4. Verify Railway accepts changes")

    print("\n📋 STEP 5: IDENTIFY BROKEN CHANGE")
    print("- Which commit broke Railway?")
    print("- Was it router changes?")
    print("- Was it environment variables?")
    print("- Was it dependency updates?")

    print("\n" + "="*50)
    print("⚡ IMMEDIATE ACTION:")

    print("\n1. Find 2-day-old commit hash:")
    print("   git log --oneline --since='2 days ago'")

    print("\n2. Rollback:")
    print("   git reset --hard [HASH]")
    print("   git push --force origin main")

    print("\n3. Monitor Railway logs")

    print("\n" + "="*50)
    print("🎯 EXPECTED OUTCOME:")

    print("✅ Railway accepts rollback")
    print("✅ Old version works in webhook mode")
    print("✅ Can identify what broke it")
    print("✅ Gradual fixes possible")

    print("\n" + "="*50)
    print("⚠️ RISKS:")

    print("- Force push overwrites history")
    print("- May lose recent fixes")
    print("- Need to re-add fixes carefully")
    print("- Test each change individually")

    print("\n" + "="*50)
    print("🚀 START ROLLBACK:")

    print("1. Get commit hash from 2 days ago")
    print("2. Run: git reset --hard [HASH]")
    print("3. Run: git push --force origin main")
    print("4. Watch Railway rebuild")

    print("\nThis should work if Railway integration is OK!")
    print("Then we can fix issues one by one.")

if __name__ == "__main__":
    main()
