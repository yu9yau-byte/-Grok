# -*- coding: utf-8 -*-
"""
Модуль-обёртка для генерации документов (DOCX/PDF).
Делегирует всю работу в generators.py.
"""
import generators

def generate_docx(variants, client_data, filename):
    """Генерация коммерческого предложения в формате DOCX."""
    generators.generate_docx(variants, client_data, filename)

def generate_pdf(variants, client_data, filename):
    """Генерация коммерческого предложения в формате PDF."""
    generators.generate_pdf(variants, client_data, filename)