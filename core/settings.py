# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')

DEFAULT_SETTINGS = {
    "company_name": "",
    "activity": "КОНДИЦИОНЕРЫ\nВЕНТИЛЯЦИЯ\nОТОПЛЕНИЕ",
    "address": "",
    "contacts": "",
    "website": "",
    "services": "проектирование – монтаж - сервисное обслуживание",
    "manager_signature": "",
    "logo_path": "",
    "primary_color": "#00A8C5",
    "font_family": "Segoe UI",
    "logo_width": 3.0
}

def load_settings():
    """Загружает настройки компании."""
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_SETTINGS)
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Заполняем отсутствующие ключи значениями по умолчанию
        for key, value in DEFAULT_SETTINGS.items():
            if key not in data:
                data[key] = value
        return data
    except Exception:
        return dict(DEFAULT_SETTINGS)

def save_settings(settings: dict):
    """Сохраняет настройки с валидацией."""
    # Простая валидация (можно расширить)
    if not settings.get("company_name", "").strip():
        raise ValueError("Название организации обязательно для заполнения")
    
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)