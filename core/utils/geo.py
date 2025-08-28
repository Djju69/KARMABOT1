# core/utils/geo.py

from typing import List, Dict


def find_restaurants(
    latitude: float,
    longitude: float,
    radius: int = 2000,
    lang: str = "ru"
) -> List[Dict]:
    """
    Функция для поиска ресторанов рядом с заданными координатами.
    Пока возвращает тестовые данные.

    :param latitude: Широта пользователя
    :param longitude: Долгота пользователя
    :param radius: Радиус поиска в метрах (по умолчанию 2000)
    :param lang: Язык локализации (пока не используется)
    :return: Список словарей с информацией о ресторанах
    """
    # TODO: Реализовать реальный поиск по базе данных или внешним API

    # Временные тестовые данные
    return [
        {
            "id": 1,
            "name": "Hải sản Mộc quán Nha Trang",
            "address": "123 Đường Biển, Nha Trang",
            "distance_km": 0.5
        },
        {
            "id": 2,
            "name": "Quán Ăn Ngon",
            "address": "456 Nguyễn Thị Minh Khai, Nha Trang",
            "distance_km": 1.2
        }
    ]
