# core/utils/geo.py

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class GeoPoint:
    """Класс для представления географической точки"""
    latitude: float
    longitude: float
    
    def distance_to(self, other: 'GeoPoint') -> float:
        """Вычисляет расстояние до другой точки в километрах (формула Haversine)"""
        return haversine_distance(self.latitude, self.longitude, other.latitude, other.longitude)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Вычисляет расстояние между двумя точками на Земле по формуле Haversine.
    
    Args:
        lat1, lon1: Координаты первой точки
        lat2, lon2: Координаты второй точки
        
    Returns:
        Расстояние в километрах
    """
    # Радиус Земли в километрах
    R = 6371.0
    
    # Преобразование в радианы
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Разности координат
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Формула Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

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

def nearest_places(
    user_lat: float,
    user_lon: float,
    places: List[Dict],
    radius_km: float = 5.0,
    limit: int = 10
) -> List[Dict]:
    """
    Находит ближайшие заведения в заданном радиусе.
    
    Args:
        user_lat: Широта пользователя
        user_lon: Долгота пользователя
        places: Список заведений с координатами
        radius_km: Радиус поиска в километрах
        limit: Максимальное количество результатов
        
    Returns:
        Список ближайших заведений с расстояниями
    """
    user_point = GeoPoint(user_lat, user_lon)
    nearby_places = []
    
    for place in places:
        # Проверяем наличие координат
        if not place.get('latitude') or not place.get('longitude'):
            continue
            
        place_lat = float(place['latitude'])
        place_lon = float(place['longitude'])
        
        # Вычисляем расстояние
        distance = user_point.distance_to(GeoPoint(place_lat, place_lon))
        
        # Фильтруем по радиусу
        if distance <= radius_km:
            place_with_distance = place.copy()
            place_with_distance['distance_km'] = round(distance, 2)
            nearby_places.append(place_with_distance)
    
    # Сортируем по расстоянию и ограничиваем количество
    nearby_places.sort(key=lambda x: x['distance_km'])
    return nearby_places[:limit]

def find_places_in_radius(
    latitude: float,
    longitude: float,
    places: List[Dict],
    radius_km: float = 5.0,
    category: Optional[str] = None,
    limit: int = 20
) -> List[Dict]:
    """
    Универсальная функция поиска заведений в радиусе.
    
    Args:
        latitude: Широта пользователя
        longitude: Долгота пользователя
        places: Список всех заведений
        radius_km: Радиус поиска в километрах
        category: Фильтр по категории (опционально)
        limit: Максимальное количество результатов
        
    Returns:
        Список заведений в радиусе с расстояниями
    """
    # Фильтруем по категории если указана
    if category:
        places = [p for p in places if p.get('category_slug') == category]
    
    # Находим ближайшие
    nearby = nearest_places(latitude, longitude, places, radius_km, limit)
    
    return nearby

def calculate_bounding_box(
    latitude: float,
    longitude: float,
    radius_km: float
) -> Tuple[float, float, float, float]:
    """
    Вычисляет ограничивающий прямоугольник для поиска в БД.
    
    Args:
        latitude: Центральная широта
        longitude: Центральная долгота
        radius_km: Радиус в километрах
        
    Returns:
        Кортеж (min_lat, max_lat, min_lon, max_lon)
    """
    # Примерное преобразование километров в градусы
    # 1 градус широты ≈ 111 км
    # 1 градус долготы ≈ 111 км * cos(широта)
    
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * math.cos(math.radians(latitude)))
    
    return (
        latitude - lat_delta,  # min_lat
        latitude + lat_delta,  # max_lat
        longitude - lon_delta, # min_lon
        longitude + lon_delta  # max_lon
    )

def format_distance(distance_km: float) -> str:
    """
    Форматирует расстояние для отображения пользователю.
    
    Args:
        distance_km: Расстояние в километрах
        
    Returns:
        Отформатированная строка
    """
    if distance_km < 1.0:
        return f"{int(distance_km * 1000)} м"
    else:
        return f"{distance_km:.1f} км"
