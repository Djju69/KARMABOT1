"""
Скрипт для настройки переменных окружения Telegram бота.
Создает файл .env с необходимыми настройками.
"""
import os
import secrets
from pathlib import Path

def generate_secret_key() -> str:
    """Генерирует случайный секретный ключ."""
    return secrets.token_urlsafe(32)

def main():
    print("Настройка окружения для Telegram бота")
    print("-" * 40)
    
    # Запрашиваем у пользователя необходимые данные
    bot_token = input("Введите токен вашего Telegram бота: ").strip()
    bot_username = input("Введите username бота (без @): ").strip()
    
    # Генерируем секретный ключ для вебхука, если его нет
    webhook_secret = generate_secret_key()
    
    # Запрашиваем URL для вебхука
    webhook_url = input("\nВведите полный URL для вебхука (например, https://ваш-домен.com/webhooks/telegram): ").strip()
    
    # Запрашиваем URL для редиректа после авторизации
    login_redirect_url = input("\nВведите URL для редиректа после авторизации через Telegram (например, https://ваш-фронтенд.com/auth/telegram/callback): ").strip()
    
    # Создаем содержимое файла .env
    env_content = f"""# Настройки Telegram бота
TELEGRAM_BOT_TOKEN={bot_token}
TELEGRAM_BOT_USERNAME={bot_username}
TELEGRAM_WEBHOOK_URL={webhook_url}
TELEGRAM_WEBHOOK_SECRET={webhook_secret}
TELEGRAM_LOGIN_REDIRECT_URL={login_redirect_url}

# Дополнительные настройки (можно изменить при необходимости)
TELEGRAM_MAX_CONNECTIONS=40
TELEGRAM_AUTH_EXPIRE_MINUTES=15
"""
    # Проверяем существование файла .env
    env_file = Path(".env")
    if env_file.exists():
        print("\n⚠️  Внимание: Файл .env уже существует.")
        overwrite = input("Перезаписать существующий файл? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Отменено пользователем.")
            return
    
    # Записываем настройки в файл
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("\n✅ Файл .env успешно создан/обновлен!")
        print("\nСкопируйте следующие настройки в ваш хостинг или настройте их вручную:")
        print("\n" + "-" * 50)
        print(env_content)
        print("-" * 50)
        
        print("\nДалее выполните следующие шаги:")
        print("1. Убедитесь, что все URL-адреса корректны")
        print("2. Запустите приложение")
        print("3. Выполните настройку вебхука командой: python scripts/setup_telegram_webhook.py")
        print("4. Проверьте работу вебхука: python scripts/test_webhook.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка при создании файла .env: {e}")

if __name__ == "__main__":
    main()
