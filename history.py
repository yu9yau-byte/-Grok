# -*- coding: utf-8 -*-
"""
Модуль управления историей коммерческих предложений.
"""
import json
import os
from datetime import datetime
import config

HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'history.json')

# ===== КЭШИРОВАНИЕ =====
_history_cache = None  # Кэш всей истории в памяти

def _get_cache():
    """Возвращает кэшированную историю, загружая из файла только при необходимости."""
    global _history_cache
    if _history_cache is None:
        _history_cache = load_history()
    return _history_cache

def invalidate_cache():
    """Сбрасывает кэш. Вызывать после изменений истории."""
    global _history_cache
    _history_cache = None


def load_history():
    """Загружает историю КП из файла."""
    if not os.path.exists(HISTORY_FILE):
        return []
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history):
    """Сохраняет историю КП в файл и обновляет кэш."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    # Обновляем кэш
    global _history_cache
    _history_cache = history


def add_proposal(variants, client_data, filename=None):
    """
    Добавляет новое КП в историю.
    
    Args:
        variants: список вариантов (модели, количество, цены)
        client_data: данные клиента
        filename: путь к сохранённому файлу (если есть)
    
    Returns:
        ID созданной записи в истории
    """
    history = _get_cache()
    
    # Генерируем ID
    max_id = 0
    for item in history:
        item_id = item.get('id', 0)
        if isinstance(item_id, int) and item_id > max_id:
            max_id = item_id
    
    new_id = max_id + 1
    
    # Считаем общую сумму (загружаем модели ОДИН раз)
    total_amount = 0
    models = config.load_models()
    for var in variants:
        model_key = var.get('model_key', '')
        qty = var.get('quantity', 1)
        model = models.get(model_key, {})
        price = model.get('price', 0)
        total_amount += price * qty + var.get('installation_price', 0) + var.get('approval_price', 0)
    
    proposal = {
        'id': new_id,
        'created_at': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'client': {
            'name': client_data.get('to', ''),
            'contact_person': client_data.get('from', ''),
            'phone': client_data.get('phone', ''),
            'email': client_data.get('email', ''),
            'object': client_data.get('object', ''),
            'date': client_data.get('date', ''),  # Дата КП для документов
        },
        'variants_count': len(variants),
        'total_amount': total_amount,
        'filename': filename,
        'variants': variants  # Полные данные вариантов для восстановления
    }
    
    history.insert(0, proposal)  # Добавляем в начало (новые сверху)
    save_history(history)
    
    return new_id


def get_proposal(proposal_id):
    """Получает КП по ID."""
    history = _get_cache()
    for item in history:
        if item.get('id') == proposal_id:
            return item
    return None


def delete_proposal(proposal_id):
    """Удаляет КП из истории."""
    history = _get_cache()
    history = [item for item in history if item.get('id') != proposal_id]
    save_history(history)


def get_analytics(month=None, year=None):
    """
    Возвращает аналитику по КП.
    
    Args:
        month: месяц (1-12), если None - все
        year: год, если None - текущий
    
    Returns:
        Словарь с аналитикой
    """
    history = _get_cache()
    
    if year is None:
        year = datetime.now().year
    
    total_proposals = 0
    total_amount = 0
    clients = set()
    
    monthly_stats = {}
    
    for item in history:
        created_at = item.get('created_at', '')
        if created_at:
            try:
                dt = datetime.strptime(created_at, '%d.%m.%Y %H:%M')
                item_year = dt.year
                item_month = dt.month
            except:
                continue
        else:
            continue
        
        # Фильтруем по году
        if item_year != year:
            continue
        
        total_proposals += 1
        total_amount += item.get('total_amount', 0)
        
        client_name = item.get('client', {}).get('name', '')
        if client_name:
            clients.add(client_name)
        
        # Статистика по месяцам
        month_key = f"{item_year}-{item_month:02d}"
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {'count': 0, 'amount': 0}
        monthly_stats[month_key]['count'] += 1
        monthly_stats[month_key]['amount'] += item.get('total_amount', 0)
    
    return {
        'total_proposals': total_proposals,
        'total_amount': total_amount,
        'unique_clients': len(clients),
        'year': year,
        'monthly_stats': monthly_stats
    }


def get_monthly_summary(year=None):
    """Возвращает сводку по месяцам за год."""
    if year is None:
        year = datetime.now().year
    
    history = _get_cache()
    months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
    
    monthly_data = []
    for month in range(1, 13):
        count = 0
        amount = 0
        
        for item in history:
            created_at = item.get('created_at', '')
            if created_at:
                try:
                    dt = datetime.strptime(created_at, '%d.%m.%Y %H:%M')
                    if dt.year == year and dt.month == month:
                        count += 1
                        amount += item.get('total_amount', 0)
                except:
                    pass
        
        monthly_data.append({
            'month': month,
            'month_name': months[month - 1],
            'count': count,
            'amount': amount
        })
    
    return monthly_data


def get_recent_proposals(limit=10):
    """Возвращает последние N КП."""
    history = _get_cache()
    return history[:limit]


def filter_proposals(filters=None):
    """
    Фильтрует предложения по заданным критериям.
    
    Args:
        filters: словарь с фильтрами
            - date_from: начальная дата (строка ДД.ММ.ГГГГ)
            - date_to: конечная дата (строка ДД.ММ.ГГГГ)
            - client_name: имя клиента (подстрока)
            - amount_min: минимальная сумма
            - amount_max: максимальная сумма
    
    Returns:
        Отфильтрованный список предложений
    """
    history = _get_cache()
    
    if not filters:
        return history
    
    result = []
    
    for item in history:
        # Фильтр по дате
        if filters.get('date_from'):
            try:
                item_date = datetime.strptime(item.get('created_at', '')[:10], '%d.%m.%Y')
                filter_date_from = datetime.strptime(filters['date_from'], '%d.%m.%Y')
                if item_date < filter_date_from:
                    continue
            except:
                pass
        
        if filters.get('date_to'):
            try:
                item_date = datetime.strptime(item.get('created_at', '')[:10], '%d.%m.%Y')
                filter_date_to = datetime.strptime(filters['date_to'], '%d.%m.%Y')
                if item_date > filter_date_to:
                    continue
            except:
                pass
        
        # Фильтр по клиенту
        if filters.get('client_name'):
            client_name = item.get('client', {}).get('name', '').lower()
            filter_name = filters['client_name'].lower()
            if filter_name not in client_name:
                continue
        
        # Фильтр по сумме
        amount = item.get('total_amount', 0)
        
        if filters.get('amount_min') is not None:
            if amount < filters['amount_min']:
                continue
        
        if filters.get('amount_max') is not None:
            if amount > filters['amount_max']:
                continue
        
        result.append(item)
    
    return result


def get_all_clients():
    """Возвращает список всех уникальных клиентов из истории."""
    history = _get_cache()
    clients = set()
    for item in history:
        name = item.get('client', {}).get('name', '')
        if name:
            clients.add(name)
    return sorted(list(clients))