# -*- coding: utf-8 -*-
"""
Конфигурация приложения.
Импортирует функции из settings.py для обратной совместимости.
"""
from settings import (
    DEFAULT_SETTINGS,
    load_settings,
    save_settings,
    load_models,
    save_models,
    load_clients,
    save_clients,
    add_client,
    update_client,
    delete_client,
    get_client_by_id,
    add_client_if_new
)

__all__ = [
    'DEFAULT_SETTINGS',
    'load_settings',
    'save_settings', 
    'load_models',
    'save_models',
    'load_clients',
    'save_clients',
    'add_client',
    'update_client',
    'delete_client',
    'get_client_by_id',
    'add_client_if_new'
]