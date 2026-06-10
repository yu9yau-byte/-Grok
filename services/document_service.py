# -*- coding: utf-8 -*-
"""
Сервис генерации коммерческих предложений.
Убирает дублирование между DOCX и PDF.
"""
import os
from datetime import datetime
import config  # временно, позже заменим на core
from generators.docx_generator import generate_docx
from generators.pdf_generator import generate_pdf


class DocumentService:
    """Основной сервис для создания документов КП."""
    
    @staticmethod
    def generate_docx(variants: list, client_data: dict, filename: str):
        """Генерирует коммерческое предложение в формате DOCX."""
        try:
            generate_docx(variants, client_data, filename)
            # Сохраняем в историю (позже перенесём в HistoryService)
            import history
            history.add_proposal(variants, client_data, filename)
            return True
        except Exception as e:
            raise Exception(f"Ошибка генерации DOCX: {str(e)}")

    @staticmethod
    def generate_pdf(variants: list, client_data: dict, filename: str):
        """Генерирует коммерческое предложение в формате PDF."""
        try:
            generate_pdf(variants, client_data, filename)
            # Сохраняем в историю
            import history
            history.add_proposal(variants, client_data, filename)
            return True
        except Exception as e:
            raise Exception(f"Ошибка генерации PDF: {str(e)}")

    @staticmethod
    def validate_proposal(variants: list, client_data: dict) -> tuple:
        """Проверяет данные перед генерацией."""
        errors = []
        
        if not variants:
            errors.append("Добавьте хотя бы один вариант в предложение.")
        
        if not client_data.get("to", "").strip():
            errors.append("Поле 'Заказчик' обязательно.")
        
        # Проверка наличия моделей
        models = config.load_models()
        missing = [v["model_key"] for v in variants if v["model_key"] not in models]
        if missing:
            errors.append(f"Модели не найдены в базе: {', '.join(missing)}")
        
        return len(errors) == 0, errors