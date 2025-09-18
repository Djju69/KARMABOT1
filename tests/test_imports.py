"""
Regression tests for critical imports and functionality
"""
import os
import sys
import importlib
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)

# Mock environment variables for tests
os.environ.update({
    "BOTS__BOT_TOKEN": "test_token",
    "ENVIRONMENT": "test",
    "FEATURES__BOT_ENABLED": "1"
})

class TestImports(unittest.TestCase):
    """Test critical imports and basic functionality"""
    
    def test_config_import(self):
        """Test core.config imports"""
        with patch.dict(os.environ, {"BOTS__BOT_TOKEN": "test_token"}):
            from core.config import Settings, Bots, FeatureFlags
            self.assertTrue(hasattr(Settings, 'model_fields'))
            self.assertTrue(hasattr(Bots, 'model_fields'))
            self.assertTrue(hasattr(FeatureFlags, 'model_fields'))
    
    def test_handlers_import(self):
        """Test core.handlers imports"""
        with patch.dict(os.environ, {"BOTS__BOT_TOKEN": "test_token"}):
            from core.handlers import basic_router, callback_router, main_menu_router
            self.assertTrue(hasattr(basic_router, 'include_router'))
            self.assertTrue(hasattr(callback_router, 'include_router'))
            self.assertTrue(hasattr(main_menu_router, 'include_router'))
    
    def test_compat_import(self):
        """Test core.compat imports"""
        with patch.dict(os.environ, {"BOTS__BOT_TOKEN": "test_token"}):
            from core.compat import compat_handler, call_compat, add_compat_aliases
            self.assertTrue(callable(compat_handler))
            self.assertTrue(callable(call_compat))
            self.assertTrue(callable(add_compat_aliases))

class TestSettings(unittest.TestCase):
    """Test settings functionality"""
    
    def test_settings_creation(self):
        """Test that settings can be created"""
        with patch.dict(os.environ, {
            "BOTS__BOT_TOKEN": "test_token",
            "ENVIRONMENT": "test"
        }):
            from core.config import Settings, Bots
            settings = Settings(bots=Bots(bot_token="test_token"))
            self.assertEqual(settings.bots.bot_token, "test_token")
            self.assertEqual(settings.environment, "test")

class TestRouters(unittest.TestCase):
    """Test router functionality"""
    
    def test_basic_router_handlers(self):
        """Test basic router has required handlers"""
        with patch.dict(os.environ, {"BOTS__BOT_TOKEN": "test_token"}):
            from core.handlers import basic_router
            # Check if router has the expected methods
            self.assertTrue(hasattr(basic_router, 'include_router'))
            self.assertTrue(hasattr(basic_router, 'message'))
            self.assertTrue(hasattr(basic_router, 'callback_query'))

if __name__ == "__main__":
    unittest.main()
