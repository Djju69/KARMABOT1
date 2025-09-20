#!/usr/bin/env python3
"""
Автотест для проверки консистентности i18n файлов
Проверяет:
- Одинаковый набор ключей во всех языках
- Отсутствие дубликатов
- Корректность JSON синтаксиса
"""

import json
import os
from pathlib import Path


def test_i18n_consistency():
    """Проверка консистентности i18n файлов"""
    locales_dir = Path("locales")
    
    # Найти все JSON файлы локализации
    locale_files = list(locales_dir.glob("*.json"))
    locale_files = [f for f in locale_files if f.name != "deprecated.json"]
    
    if not locale_files:
        raise AssertionError("No locale files found")
    
    # Загрузить все файлы локализации
    locales = {}
    for file_path in locale_files:
        lang = file_path.stem
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                locales[lang] = json.load(f)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise AssertionError(f"Error reading {file_path}: {e}")
    
    # Проверить консистентность ключей
    all_keys = set()
    for lang, data in locales.items():
        all_keys.update(data.keys())
    
    for lang, data in locales.items():
        missing_keys = all_keys - set(data.keys())
        if missing_keys:
            raise AssertionError(f"Missing keys in {lang}: {missing_keys}")
    
    # Проверить отсутствие дубликатов
    for lang, data in locales.items():
        keys = list(data.keys())
        if len(keys) != len(set(keys)):
            duplicates = [k for k in set(keys) if keys.count(k) > 1]
            raise AssertionError(f"Duplicate keys in {lang}: {duplicates}")
    
    # Проверить наличие TODO_TRANSLATE
    for lang, data in locales.items():
        todo_keys = [k for k, v in data.items() if "TODO_TRANSLATE" in str(v)]
        if todo_keys:
            print(f"Warning: TODO_TRANSLATE found in {lang}: {todo_keys}")
    
    print(f"✅ i18n consistency test passed for {len(locales)} languages")
    print(f"Total keys: {len(all_keys)}")
    return True


if __name__ == "__main__":
    test_i18n_consistency()
