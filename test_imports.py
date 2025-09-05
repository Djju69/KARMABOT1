#!/usr/bin/env python3
"""
Test script to verify that imports work correctly after fixing circular imports
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test that all critical imports work without circular import errors"""
    print("🔍 Testing imports...")

    try:
        # Test loyalty service import
        print("📦 Testing loyalty_service import...")
        from core.services.loyalty_service import LoyaltyService
        print("✅ loyalty_service imported successfully")

        # Test referral service import
        print("📦 Testing referral_service import...")
        from core.services.referral_service import ReferralService
        print("✅ referral_service imported successfully")

        # Test partner handler import
        print("📦 Testing partner handler import...")
        from core.handlers.partner import partner_router
        print("✅ partner handler imported successfully")

        # Test bot import
        print("📦 Testing bot import...")
        from bot.bot import start as start_bot
        print("✅ bot imported successfully")

        print("🎉 All critical imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ Import test passed - circular import issue resolved!")
        sys.exit(0)
    else:
        print("\n❌ Import test failed - issues remain")
        sys.exit(1)