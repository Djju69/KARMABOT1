"""
Contract tests for KARMABOT1 - ensuring backward compatibility
Tests callback patterns, i18n keys, and API contracts
"""
import re
import pytest
from typing import Dict, Set

# Callback patterns that MUST NOT change (frozen contracts)
CALLBACK_PATTERNS = {
    # Legacy patterns from original code (IMMUTABLE)
    "restoran": r"^restoran_\d+_\d+_\d+_\d+$",
    "category": r"^category_[a-z_]+$", 
    "language": r"^lang_[a-z]{2}$",
    
    # New patterns (can be extended but not changed)
    "partner_category": r"^partner_cat:[a-z_]+$",
    "partner_action": r"^partner_(submit|cancel|edit|back)$",
    "moderation": r"^mod_(approve|reject|feature|archive|next|finish|back):\d+$",
    "reject_reason": r"^reject_reason:\d+:[a-z_]+$",
    "reject_custom": r"^reject_custom:\d+$",
}

# Required i18n keys that MUST exist in all languages (IMMUTABLE)
REQUIRED_I18N_KEYS = {
    # Legacy keys (cannot be removed)
    'back_to_main',
    'choose_category', 
    'show_nearest',
    'choose_language',
    'choose_district',
    
    # P1 additions (new but now required)
    'profile',
    'help',
    
    # Partner FSM keys
    'add_card',
    'my_cards',
    'card_status_draft',
    'card_status_pending', 
    'card_status_approved',
    'card_status_published',
    'card_status_rejected',
    'card_status_archived',
    
    # Common actions
    'cancel',
    'skip',
    'back',
    'next',
    'edit',
    'delete',
    'save',
    
    # Card renderer
    'contact_info',
    'address_info', 
    'discount_info',
    'show_on_map',
    'create_qr',
    'call_business',
    'book_service',
}

class TestCallbackContracts:
    """Test callback pattern contracts"""
    
    def test_callback_patterns_are_valid_regex(self):
        """All callback patterns must be valid regex"""
        for name, pattern in CALLBACK_PATTERNS.items():
            try:
                re.compile(pattern)
            except re.error as e:
                pytest.fail(f"Invalid regex pattern for '{name}': {pattern} - {e}")
    
    def test_legacy_callback_patterns_unchanged(self):
        """Legacy callback patterns must match expected format"""
        # Test legacy restaurant pattern
        assert re.match(CALLBACK_PATTERNS["restoran"], "restoran_2_10_1_0")
        assert re.match(CALLBACK_PATTERNS["restoran"], "restoran_1_5_2_3")
        assert not re.match(CALLBACK_PATTERNS["restoran"], "restoran_abc")
        
        # Test language pattern
        assert re.match(CALLBACK_PATTERNS["language"], "lang_ru")
        assert re.match(CALLBACK_PATTERNS["language"], "lang_en")
        assert not re.match(CALLBACK_PATTERNS["language"], "lang_russian")
    
    def test_new_callback_patterns_work(self):
        """New callback patterns must work correctly"""
        # Test partner category pattern
        assert re.match(CALLBACK_PATTERNS["partner_category"], "partner_cat:restaurants")
        assert re.match(CALLBACK_PATTERNS["partner_category"], "partner_cat:spa")
        
        # Test moderation patterns
        assert re.match(CALLBACK_PATTERNS["moderation"], "mod_approve:123")
        assert re.match(CALLBACK_PATTERNS["moderation"], "mod_reject:456")
        assert re.match(CALLBACK_PATTERNS["reject_reason"], "reject_reason:123:incomplete")

class TestI18nContracts:
    """Test internationalization contracts"""
    
    def test_required_keys_exist_in_all_languages(self):
        """All required keys must exist in all supported languages"""
        from core.utils.locales_v2 import translations_v2
        
        for lang, texts in translations_v2.items():
            missing_keys = REQUIRED_I18N_KEYS - set(texts.keys())
            assert not missing_keys, f"Missing keys in {lang}: {missing_keys}"
    
    def test_no_keys_removed_from_russian(self):
        """Russian translation must contain all required keys"""
        from core.utils.locales_v2 import translations_v2
        
        ru_keys = set(translations_v2['ru'].keys())
        missing = REQUIRED_I18N_KEYS - ru_keys
        assert not missing, f"Missing required keys in Russian: {missing}"
    
    def test_backward_compatibility_keys(self):
        """Legacy keys must still exist and work"""
        from core.utils.locales_v2 import get_text
        
        # Test legacy keys
        assert get_text('back_to_main', 'ru') == 'Вернуться в главное меню🏘'
        assert get_text('choose_category', 'ru') == '🗂️ Категории'
        assert get_text('show_nearest', 'ru') == '📍 Показать ближайшие'
        
        # Test new keys
        assert get_text('profile', 'ru') == '👤 Личный кабинет'
        assert get_text('help', 'ru') == '❓ Помощь'
    
    def test_fallback_mechanism(self):
        """Fallback to Russian must work for missing keys"""
        from core.utils.locales_v2 import get_text
        
        # Test fallback for non-existent key
        result = get_text('non_existent_key', 'en')
        assert result == '[non_existent_key]'  # Ultimate fallback
        
        # Test language fallback
        result = get_text('profile', 'unknown_lang')
        assert result == '👤 Личный кабинет'  # Falls back to Russian

class TestDatabaseContracts:
    """Test database schema contracts"""
    
    def test_migration_table_structure(self):
        """Migration table must have correct structure"""
        from core.database.migrations import DatabaseMigrator
        
        migrator = DatabaseMigrator(":memory:")  # In-memory for testing
        migrator.init_migration_table()
        
        with migrator.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(schema_migrations)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'version': 'TEXT',
                'applied_at': 'TIMESTAMP', 
                'description': 'TEXT'
            }
            
            for col_name, col_type in expected_columns.items():
                assert col_name in columns, f"Missing column: {col_name}"
    
    def test_cards_v2_table_structure(self):
        """Cards v2 table must have required columns"""
        from core.database.migrations import DatabaseMigrator
        
        migrator = DatabaseMigrator(":memory:")
        migrator.run_all_migrations()
        
        with migrator.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(cards_v2)")
            columns = {row[1] for row in cursor.fetchall()}
            
            required_columns = {
                'id', 'partner_id', 'category_id', 'title', 'description',
                'contact', 'address', 'photo_file_id', 'status', 'created_at'
            }
            
            missing = required_columns - columns
            assert not missing, f"Missing columns in cards_v2: {missing}"
    
    def test_status_constraint(self):
        """Card status must be constrained to valid values"""
        from core.database.migrations import DatabaseMigrator
        
        migrator = DatabaseMigrator(":memory:")
        migrator.run_all_migrations()
        
        with migrator.get_connection() as conn:
            # Valid status should work
            conn.execute("""
                INSERT INTO partners_v2 (tg_user_id, display_name) VALUES (1, 'Test')
            """)
            conn.execute("""
                INSERT INTO categories_v2 (slug, name) VALUES ('test', 'Test')
            """)
            conn.execute("""
                INSERT INTO cards_v2 (partner_id, category_id, title, status)
                VALUES (1, 1, 'Test Card', 'pending')
            """)
            
            # Invalid status should fail
            with pytest.raises(Exception):
                conn.execute("""
                    INSERT INTO cards_v2 (partner_id, category_id, title, status)
                    VALUES (1, 1, 'Bad Card', 'invalid_status')
                """)

class TestFeatureFlagContracts:
    """Test feature flag contracts"""
    
    def test_feature_flags_default_to_false(self):
        """All feature flags must default to False for safety"""
        from core.settings import FeatureFlags
        
        flags = FeatureFlags()
        assert flags.partner_fsm is False
        assert flags.moderation is False
        assert flags.new_menu is False
        assert flags.qr_webapp is False
        assert flags.listen_notify is False
    
    def test_settings_load_without_env(self):
        """Settings must load with defaults when no .env file"""
        import os
        from core.settings import get_settings
        
        # Temporarily clear environment
        old_token = os.environ.get('BOT_TOKEN')
        old_admin = os.environ.get('ADMIN_ID')
        
        try:
            os.environ['BOT_TOKEN'] = 'test_token'
            os.environ['ADMIN_ID'] = '123456'
            
            settings = get_settings()
            assert settings.features.partner_fsm is False
            assert settings.features.moderation is False
            
        finally:
            # Restore environment
            if old_token:
                os.environ['BOT_TOKEN'] = old_token
            if old_admin:
                os.environ['ADMIN_ID'] = old_admin

class TestCardRendererContracts:
    """Test card renderer contracts"""
    
    def test_renderer_protocol_compliance(self):
        """All renderers must implement the protocol"""
        from core.services.card_renderer import DefaultCardRenderer, LegacyCardRenderer
        
        renderers = [DefaultCardRenderer(), LegacyCardRenderer()]
        test_card = {
            'id': 1,
            'title': 'Test Card',
            'description': 'Test Description',
            'contact': '+1234567890'
        }
        
        for renderer in renderers:
            # Must have render_card method
            assert hasattr(renderer, 'render_card')
            result = renderer.render_card(test_card)
            assert isinstance(result, str)
            assert 'Test Card' in result
            
            # Must have render_card_preview method
            assert hasattr(renderer, 'render_card_preview') 
            preview = renderer.render_card_preview(test_card)
            assert isinstance(preview, str)
    
    def test_backward_compatibility_functions(self):
        """Backward compatibility functions must work"""
        from core.services.card_renderer import render_card, render_card_preview
        
        test_card = {
            'title': 'Test Card',
            'description': 'Test Description'
        }
        
        # Functions must exist and work
        result = render_card(test_card)
        assert isinstance(result, str)
        assert 'Test Card' in result
        
        preview = render_card_preview(test_card)
        assert isinstance(preview, str)

class TestKeyboardContracts:
    """Test keyboard layout contracts"""
    
    def test_main_menu_backward_compatibility(self):
        """Main menu must work with feature flags"""
        from core.keyboards.reply_v2 import get_main_menu_reply
        from core.settings import settings
        
        # Test with new menu disabled (legacy mode)
        original_flag = settings.features.new_menu
        settings.features.new_menu = False
        
        try:
            keyboard = get_main_menu_reply('ru')
            assert keyboard is not None
            assert len(keyboard.keyboard) == 2  # 2x2 layout
            assert len(keyboard.keyboard[0]) == 2  # 2 buttons per row
            
        finally:
            settings.features.new_menu = original_flag
    
    def test_legacy_keyboard_aliases(self):
        """Legacy keyboard function aliases must work"""
        from core.keyboards.reply_v2 import return_to_main_menu, get_main_menu_keyboard
        
        # Legacy aliases must exist and work
        keyboard1 = return_to_main_menu('ru')
        assert keyboard1 is not None
        
        keyboard2 = get_main_menu_keyboard('ru')
        assert keyboard2 is not None

# Integration test
class TestEndToEndContracts:
    """End-to-end contract tests"""
    
    def test_complete_card_workflow(self):
        """Complete card workflow must work without breaking"""
        from core.database.db_v2 import DatabaseServiceV2
        from core.services.card_renderer import card_service
        
        # Use in-memory database for testing
        db = DatabaseServiceV2(":memory:")
        
        # Create partner
        from core.database.db_v2 import Partner
        partner = Partner(
            id=None,
            tg_user_id=12345,
            display_name="Test Partner"
        )
        partner_id = db.create_partner(partner)
        assert partner_id > 0
        
        # Create card
        from core.database.db_v2 import Card
        card = Card(
            id=None,
            partner_id=partner_id,
            category_id=1,  # Assuming category exists from migrations
            title="Test Business",
            description="Test Description",
            status="pending"
        )
        card_id = db.create_card(card)
        assert card_id > 0
        
        # Render card
        card_data = {
            'id': card_id,
            'title': 'Test Business',
            'description': 'Test Description',
            'status': 'pending'
        }
        
        rendered = card_service.render_card(card_data)
        assert isinstance(rendered, str)
        assert 'Test Business' in rendered

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
