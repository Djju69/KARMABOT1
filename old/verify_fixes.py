#!/usr/bin/env python3
"""
Verify that all deployment fixes are applied correctly
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_file_content(filename, expected_content, line_number=None):
    """Check if file contains expected content"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        if line_number:
            lines = content.split('\n')
            if line_number <= len(lines):
                return expected_content in lines[line_number - 1]
            return False

        return expected_content in content
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        return False

def main():
    """Verify all fixes are applied"""
    print("🔍 Verifying deployment fixes...")

    issues = []

    # Check language_keyboard.py imports
    if not check_file_content('core/keyboards/language_keyboard.py',
                            'from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton'):
        issues.append("❌ Missing InlineKeyboardMarkup imports in language_keyboard.py")

    # Check partner.py i18n import
    if not check_file_content('core/handlers/partner.py',
                            'from core.utils.locales_v2 import get_text as _'):
        issues.append("❌ Wrong i18n import in partner.py")

    # Check partner.py keyboard imports
    if not check_file_content('core/handlers/partner.py',
                            'ReplyKeyboardMarkup, KeyboardButton'):
        issues.append("❌ Missing ReplyKeyboardMarkup imports in partner.py")

    # Check loyalty_service singleton
    if not check_file_content('core/services/loyalty_service.py',
                            'loyalty_service = LoyaltyService(get_db())'):
        issues.append("❌ Missing loyalty_service singleton")

    # Check referral_service singleton
    if not check_file_content('core/services/referral_service.py',
                            'referral_service = ReferralService()'):
        issues.append("❌ Missing referral_service singleton")

    # Check callback.py import fix
    if not check_file_content('core/handlers/callback.py',
                            'from core.handlers.category_handlers_v2 import show_categories_v2'):
        issues.append("❌ Wrong import in callback.py")

    # Check stop_bot_instances.py exists
    if not os.path.exists('stop_bot_instances.py'):
        issues.append("❌ stop_bot_instances.py not found")
    else:
        if not check_file_content('stop_bot_instances.py',
                                'drop_pending_updates=True'):
            issues.append("❌ stop_bot_instances.py missing enhanced cleanup")

    if issues:
        print("\n❌ Found issues:")
        for issue in issues:
            print(f"  {issue}")
        print("\n💡 Please apply the fixes before deploying!")
        return False
    else:
        print("✅ All fixes verified successfully!")
        print("\n🚀 Ready for deployment!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
