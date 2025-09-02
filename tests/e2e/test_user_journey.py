import pytest


@pytest.mark.e2e
def test_user_full_journey_skeleton():
    """
    E2E: регистрация → поиск → использование QR (скелет теста)

    План (для последующей имплементации):
    1) Регистрация/старт бота: /start и первичная настройка
    2) Поиск заведений: выбор категории, фильтры, пагинация 5/стр
    3) Просмотр карточки: кнопки ℹ️/🗺
    4) Использование QR: генерация и валидация (через web/api/qr)
    5) Проверка лояльности: начисление/списание

    Примечание: Тест помечен как xfail до подключения полноценной интеграции с aiogram и FastAPI TestClient
    """
    pytest.xfail("E2E сценарий будет реализован после подключения TestClient и моков aiogram")


@pytest.mark.e2e
def test_catalog_filters_pagination_skeleton():
    """
    E2E: каталог — фильтры (asia/europe/street/vege/all) → пагинация → карточка
    """
    pytest.xfail("Будет реализовано: проверка inline-фильтров и пагинации 5/стр")


@pytest.mark.e2e
def test_user_cabinet_profile_qr_history_skeleton():
    """
    E2E: кабинет пользователя — профиль → QR-коды → история
    """
    pytest.xfail("Будет реализовано: профиль, управление QR и история транзакций")

