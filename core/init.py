# -*- coding: utf-8 -*-
"""
Core module - работа с данными и настройками.
"""

from .settings import load_settings, save_settings
from .models import ModelService

__all__ = ['load_settings', 'save_settings', 'ModelService']