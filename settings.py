# -*- coding: utf-8 -*-
import json
import os
import re
from datetime import datetime

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')
MODELS_FILE = os.path.join(os.path.dirname(__file__), 'models.json')
CLIENTS_FILE = os.path.join(os.path.dirname(__file__), 'clients.json')

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
    "logo_width": 3.0   # ширина логотипа в сантиметрах
}

def validate_settings(settings):
    """
    Валидирует настройки перед сохранением.
    Возвращает кортеж (is_valid, errors_list).
    """
    errors = []
    
    # Валидация названия компании
    company_name = settings.get("company_name", "").strip()
    if not company_name:
        errors.append("Название организации обязательно для заполнения")
    elif len(company_name) > 100:
        errors.append("Название организации слишком длинное (макс. 100 символов)")
    
    # Валидация HEX-цвета
    color = settings.get("primary_color", "").strip()
    if color:
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            errors.append("Основной цвет должен быть в формате HEX (например, #00A8C5)")
    
    # Валидация ширины логотипа
    try:
        logo_width = float(settings.get("logo_width", 0))
        if logo_width <= 0:
            errors.append("Ширина логотипа должна быть положительным числом")
        elif logo_width > 50:
            errors.append("Ширина логотипа слишком большая (макс. 50 см)")
    except (ValueError, TypeError):
        errors.append("Ширина логотипа должна быть числом")
    
    # Валидация пути к логотипу
    logo_path = settings.get("logo_path", "").strip()
    if logo_path and not os.path.exists(logo_path):
        # Предупреждение, но не ошибка - файл может появиться позже
        pass
    
    # Валидация URL сайта
    website = settings.get("website", "").strip()
    if website and not re.match(r'^https?://', website):
        errors.append("Адрес сайта должен начинаться с http:// или https://")
    
    # Валидация шрифта
    font_family = settings.get("font_family", "").strip()
    valid_fonts = ["Arial", "Times New Roman", "Calibri", "Cambria", "Courier New", "Verdana", "Segoe UI"]
    if font_family and font_family not in valid_fonts:
        errors.append(f"Шрифт должен быть одним из: {', '.join(valid_fonts)}")
    
    return (len(errors) == 0, errors)

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_SETTINGS)
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return dict(DEFAULT_SETTINGS)
    
    for key, value in DEFAULT_SETTINGS.items():
        if key not in data:
            data[key] = value
    return data

def save_settings(settings):
    """
    Сохраняет настройки с предварительной валидацией.
    Если валидация не прошла, выбрасывает ValueError.
    """
    is_valid, errors = validate_settings(settings)
    if not is_valid:
        raise ValueError("Ошибки валидации настроек:\n" + "\n".join(f"• {e}" for e in errors))
    
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def load_models():
    if not os.path.exists(MODELS_FILE):
        return {}
    
    try:
        with open(MODELS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_models(models):
    with open(MODELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(models, f, ensure_ascii=False, indent=2)

def load_clients():
    """
    Загружает список клиентов из файла.
    Каждый клиент содержит расширенные поля:
    - id: уникальный идентификатор
    - name: название организации/заказчик
    - contact_person: контактное лицо
    - phone: телефон
    - email: email
    - address: адрес
    - object_name: объект/название проекта
    - notes: заметки
    - created_at: дата создания
    """
    if not os.path.exists(CLIENTS_FILE):
        return []
    
    try:
        with open(CLIENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_clients(clients):
    with open(CLIENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)

def add_client(client_data):
    """
    Добавляет нового клиента с уникальным ID.
    """
    clients = load_clients()
    # Генерируем новый ID
    max_id = 0
    for c in clients:
        cid = c.get('id', 0)
        if isinstance(cid, int) and cid > max_id:
            max_id = cid
    
    new_client = {
        'id': max_id + 1,
        'name': client_data.get('name', ''),
        'contact_person': client_data.get('contact_person', ''),
        'phone': client_data.get('phone', ''),
        'email': client_data.get('email', ''),
        'address': client_data.get('address', ''),
        'object_name': client_data.get('object_name', ''),
        'notes': client_data.get('notes', ''),
        'created_at': datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    clients.append(new_client)
    save_clients(clients)
    return new_client['id']

def update_client(client_id, client_data):
    """
    Обновляет данные клиента по ID.
    """
    clients = load_clients()
    for i, c in enumerate(clients):
        if c.get('id') == client_id:
            clients[i].update({
                'name': client_data.get('name', ''),
                'contact_person': client_data.get('contact_person', ''),
                'phone': client_data.get('phone', ''),
                'email': client_data.get('email', ''),
                'address': client_data.get('address', ''),
                'object_name': client_data.get('object_name', ''),
                'notes': client_data.get('notes', ''),
            })
            save_clients(clients)
            return True
    return False

def delete_client(client_id):
    """
    Удаляет клиента по ID.
    """
    clients = load_clients()
    clients = [c for c in clients if c.get('id') != client_id]
    save_clients(clients)

def get_client_by_id(client_id):
    """Получает клиента по ID."""
    clients = load_clients()
    for c in clients:
        if c.get('id') == client_id:
            return c
    return None

def add_client_if_new(client_data):
    """
    Устаревшая функция - добавлена для обратной совместимости.
    Сохраняет базовые данные в формате 'Кому'.
    Новый код должен использовать add_client().
    """
    clients = load_clients()
    existing = next((c for c in clients if c.get('name') == client_data.get('to')), None)
    if existing:
        existing.update({
            'name': client_data.get('to', existing.get('name', '')),
            'phone': client_data.get('phone', existing.get('phone', '')),
            'object_name': client_data.get('object', existing.get('object_name', '')),
        })
    else:
        # Мигрируем старую запись в новый формат
        add_client({
            'name': client_data.get('to', ''),
            'contact_person': client_data.get('from', ''),
            'phone': client_data.get('phone', ''),
            'object_name': client_data.get('object', ''),
        })
    save_clients(clients)