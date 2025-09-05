#!/usr/bin/env python3
"""Test loyalty service syntax"""
import sys
sys.path.insert(0, '.')

try:
    from core.services.loyalty_service import loyalty_service
    print("✅ loyalty_service import successful!")
    print(f"✅ Singleton instance: {loyalty_service}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
