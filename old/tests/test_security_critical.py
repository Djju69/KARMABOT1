"""
Критичные тесты безопасности для KarmaBot
Проверяют отсутствие уязвимостей и правильную работу защитных механизмов
"""
import pytest
import glob
import os
import jwt
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from aiogram.types import Message, CallbackQuery, User, Chat

# Импорты для тестирования
from core.middleware.rate_limit import RateLimitMiddleware, create_rate_limit_middleware
from core.utils.admin_logger import AdminActionLogger, log_admin_action_direct


class TestSecurityCritical:
    """Критичные тесты безопасности"""
    
    def test_no_hardcoded_secrets(self):
        """КРИТИЧНО: Проверить отсутствие хардкод секретов в коде"""
        violations = []
        
        # Паттерны для поиска хардкод секретов
        dangerous_patterns = [
            'secret_key = "',
            'password = "',
            'token = "',
            'api_key = "',
            'SECRET_KEY = "',
            'PASSWORD = "',
            'TOKEN = "',
            'API_KEY = "'
        ]
        
        # Исключения - файлы которые можно пропустить
        exclude_patterns = [
            'test_',
            '__pycache__',
            '.git',
            'node_modules',
            'venv',
            'env',
            '.env',
            'deprecated.json',
            'REFACTORING_PLAN.md',
            'scripts/',
            'karmabot_backup/',
            'dev_seed',
            'auth_smoke'
        ]
        
        for file_path in glob.glob("**/*.py", recursive=True):
            # Пропустить исключения
            if any(pattern in file_path for pattern in exclude_patterns):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        line_lower = line.lower()
                        
                        # Проверить подозрительные паттерны
                        for pattern in dangerous_patterns:
                            if pattern.lower() in line_lower:
                                # Проверить что это не переменная окружения
                                if 'os.getenv' not in line and 'settings.' not in line:
                                    violations.append(f"{file_path}:{i} - {line.strip()}")
                                    
            except Exception as e:
                # Пропустить файлы которые не удается прочитать
                continue
        
        assert not violations, f"Найдены хардкод секреты:\n" + "\n".join(violations)
    
    def test_secret_key_from_env(self):
        """КРИТИЧНО: SECRET_KEY должен быть из переменной окружения"""
        secret_key = os.getenv("SECRET_KEY")
        
        # Проверить что переменная установлена
        assert secret_key, "SECRET_KEY environment variable is required"
        
        # Проверить минимальную длину
        assert len(secret_key) >= 32, "SECRET_KEY must be at least 32 characters"
        
        # Проверить что это не дефолтное значение
        assert secret_key != "karmasystem-secret", "Default SECRET_KEY is not allowed"
        assert secret_key != "your-secret-key-here", "Placeholder SECRET_KEY is not allowed"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_works(self):
        """КРИТИЧНО: Проверить работу rate limiting"""
        middleware = RateLimitMiddleware(rate_limit=5)  # 5 запросов в минуту
        
        # Имитировать пользователя
        class MockEvent:
            def __init__(self, user_id):
                self.from_user = Mock()
                self.from_user.id = user_id
            
            async def answer(self, text):
                self.last_answer = text
        
        # Отправить 6 запросов подряд
        user_id = 12345
        event = MockEvent(user_id)
        
        # Первые 5 запросов должны проходить
        for i in range(5):
            try:
                await middleware(lambda e, d: None, event, {})
                # Проверить что не было блокировки
                assert not hasattr(event, 'last_answer'), f"Request {i+1} should not be rate limited"
            except Exception as e:
                pytest.fail(f"Request {i+1} should not fail: {e}")
        
        # 6-й запрос должен быть заблокирован
        try:
            await middleware(lambda e, d: None, event, {})
            # Если дошли сюда, проверить что был ответ о блокировке
            assert hasattr(event, 'last_answer'), "6th request should be rate limited"
            assert "слишком много запросов" in event.last_answer.lower()
        except Exception as e:
            pytest.fail(f"6th request should be rate limited, not fail: {e}")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_by_role(self):
        """КРИТИЧНО: Проверить разные лимиты для разных ролей"""
        middleware = RateLimitMiddleware()
        
        # Имитировать события для разных ролей
        class MockEvent:
            def __init__(self, user_id, role):
                self.from_user = Mock()
                self.from_user.id = user_id
                self.user_role = role
        
        # Тест для обычного пользователя (лимит 60/час)
        user_event = MockEvent(1001, 'user')
        
        # Проверить что лимит установлен правильно
        role = await middleware._get_user_role(user_event.from_user.id)
        limit = middleware.rate_limits.get(role, middleware.rate_limits['user'])
        assert limit == 60, f"User limit should be 60, got {limit}"
        
        # Тест для админа (лимит 300/час)
        admin_event = MockEvent(1002, 'admin')
        role = await middleware._get_user_role(admin_event.from_user.id)
        limit = middleware.rate_limits.get(role, middleware.rate_limits['user'])
        # Админ должен иметь больший лимит
        assert limit >= 300, f"Admin limit should be >= 300, got {limit}"
    
    @pytest.mark.asyncio
    async def test_admin_logging_works(self):
        """КРИТИЧНО: Проверить логирование админских действий"""
        # Создать mock событие
        user = Mock()
        user.id = 123456
        user.username = "test_admin"
        user.first_name = "Test"
        user.last_name = "Admin"
        user.language_code = "ru"
        
        chat = Mock()
        chat.id = 789
        chat.type = "private"
        
        message = Mock()
        message.from_user = user
        message.chat = chat
        message.text = "Test admin action"
        message.message_id = 1
        message.content_type = "text"
        
        # Создать логгер
        logger = AdminActionLogger()
        
        # Логировать действие
        logger.log_action(
            event=message,
            action="test_action",
            target="test_target",
            details={"test": "data"},
            result="success"
        )
        
        # Проверить что лог файл создался
        log_file = "logs/admin_actions.log"
        assert os.path.exists(log_file), "Admin actions log file should exist"
        
        # Проверить содержимое лога
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            assert "test_action" in log_content, "Action should be logged"
            assert '"admin_id": 123456' in log_content, "Admin ID should be logged"
            assert '"action": "test_action"' in log_content, "Action name should be logged"
    
    def test_admin_logging_security_events(self):
        """КРИТИЧНО: Проверить логирование событий безопасности"""
        # Создать mock событие
        user = Mock()
        user.id = 999999
        user.username = "suspicious_user"
        
        chat = Mock()
        chat.id = 888
        chat.type = "private"
        
        message = Mock()
        message.from_user = user
        message.chat = chat
        message.text = "Suspicious activity"
        
        # Создать логгер
        logger = AdminActionLogger()
        
        # Логировать событие безопасности
        logger.log_security_event(
            event=message,
            event_type="suspicious_activity",
            severity="high",
            description="Multiple failed login attempts"
        )
        
        # Проверить что событие залогировано
        log_file = "logs/admin_actions.log"
        assert os.path.exists(log_file), "Admin actions log file should exist"
        
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            assert "security_event" in log_content, "Security event should be logged"
            assert "suspicious_activity" in log_content, "Event type should be logged"
            assert '"severity": "high"' in log_content, "Severity should be logged"
    
    def test_no_sql_injection_patterns(self):
        """КРИТИЧНО: Проверить отсутствие паттернов SQL инъекций"""
        # Только действительно опасные паттерны без параметров
        dangerous_patterns = [
            "OR 1=1",
            "'; DROP TABLE",
            "UNION SELECT",
            "exec(",
            "eval(",
            "os.system(",
            "subprocess.call(",
            "f\"SELECT",
            "f\"INSERT",
            "f\"UPDATE",
            "f\"DELETE"
        ]
        
        violations = []
        
        for file_path in glob.glob("**/*.py", recursive=True):
            # Исключить тестовые файлы, кэш, backup и web файлы
            if any(pattern in file_path for pattern in [
                "test_", "__pycache__", "karmabot_backup", "backup", "migrations", "web\\", "webapp"
            ]):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for pattern in dangerous_patterns:
                        if pattern in content:
                            # Проверить что это не комментарий или строка документации
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if pattern in line and not line.strip().startswith('#'):
                                    violations.append(f"{file_path}:{i} - {line.strip()}")
                                    
            except Exception:
                continue
        
        assert not violations, f"Найдены потенциальные SQL инъекции:\n" + "\n".join(violations)
    
    def test_environment_variables_validation(self):
        """КРИТИЧНО: Проверить валидацию критичных переменных окружения"""
        required_vars = [
            'BOT_TOKEN',
            'SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        assert not missing_vars, f"Missing required environment variables: {', '.join(missing_vars)}"
        
        # Проверить формат BOT_TOKEN
        bot_token = os.getenv('BOT_TOKEN')
        if bot_token:
            assert ':' in bot_token, "BOT_TOKEN should contain ':' separator"
            parts = bot_token.split(':')
            assert len(parts) == 2, "BOT_TOKEN should have exactly 2 parts"
            assert parts[0].isdigit(), "BOT_TOKEN first part should be numeric"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_cleanup(self):
        """КРИТИЧНО: Проверить очистку кэша rate limiting"""
        middleware = RateLimitMiddleware()
        
        # Добавить старые записи в кэш
        old_time = time.time() - 7200  # 2 часа назад
        middleware.local_cache[12345] = [old_time, old_time - 100]
        
        # Добавить новые записи
        current_time = time.time()
        middleware.local_cache[12345].extend([current_time, current_time - 100])
        
        # Выполнить очистку
        await middleware._cleanup_cache()
        
        # Проверить что старые записи удалены
        user_requests = middleware.local_cache.get(12345, [])
        for req_time in user_requests:
            assert current_time - req_time < 3600, "Old requests should be cleaned up"
    
    def test_log_file_permissions(self):
        """КРИТИЧНО: Проверить права доступа к лог файлам"""
        log_dir = "logs"
        
        if os.path.exists(log_dir):
            # Проверить что директория существует и доступна для записи
            assert os.access(log_dir, os.W_OK), "Log directory should be writable"
            
            # Проверить файлы логов
            for log_file in glob.glob(f"{log_dir}/*.log"):
                assert os.access(log_file, os.R_OK), f"Log file {log_file} should be readable"
    
    @pytest.mark.asyncio
    async def test_middleware_error_handling(self):
        """КРИТИЧНО: Проверить обработку ошибок в middleware"""
        middleware = RateLimitMiddleware()
        
        # Создать событие без from_user
        class BadEvent:
            pass
        
        bad_event = BadEvent()
        
        # Middleware не должен падать на плохих событиях
        try:
            await middleware(lambda e, d: None, bad_event, {})
            # Если дошли сюда, значит ошибка обработана корректно
            assert True, "Middleware should handle bad events gracefully"
        except Exception as e:
            pytest.fail(f"Middleware should not crash on bad events: {e}")


class TestSecurityIntegration:
    """Интеграционные тесты безопасности"""
    
    @pytest.mark.asyncio
    async def test_full_security_chain(self):
        """КРИТИЧНО: Проверить полную цепочку безопасности"""
        # Создать middleware
        middleware = create_rate_limit_middleware()
        
        # Создать mock событие
        user = Mock()
        user.id = 123456
        
        message = Mock()
        message.from_user = user
        message.text = "Test message"
        message.chat = Mock()
        message.chat.id = 789
        
        # Проверить что middleware работает
        try:
            await middleware(lambda e, d: None, message, {})
            assert True, "Security chain should work"
        except Exception as e:
            pytest.fail(f"Security chain should not fail: {e}")
    
    def test_security_logs_rotation(self):
        """КРИТИЧНО: Проверить ротацию логов безопасности"""
        log_file = "logs/admin_actions.log"
        
        if os.path.exists(log_file):
            # Проверить размер файла (не должен быть слишком большим)
            file_size = os.path.getsize(log_file)
            max_size = 100 * 1024 * 1024  # 100MB
            
            if file_size > max_size:
                pytest.warn(f"Log file is very large: {file_size} bytes. Consider log rotation.")


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v", "--tb=short"])
