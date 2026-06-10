# -*- coding: utf-8 -*-
"""
GUI компонент для Этапа 2: Корректировка профиля бренда
Интегрируется в главное приложение
"""

import os
import json
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox, filedialog, BooleanVar, Checkbutton, font as tkFont
import importers
import config

class Stage2ProfileEditor(ctk.CTkToplevel):
    """Окно для корректировки профиля бренда (Этап 2)"""
    
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.title("Этап 2: Корректировка профиля бренда")
        self.geometry("900x700")
        self.configure(fg_color="#0A0F1A")
        
        self.file_path = file_path
        self.headers = self._load_headers()
        self.profiles = importers.load_brand_profiles()
        
        # Автоматически определяем бренд
        df = pd.read_excel(file_path, sheet_name=0, nrows=5)
        self.detected_brand = importers.detect_brand_from_file(df) or "NEW_BRAND"
        
        self.selected_columns = {}
        self.synonyms_map = {}
        self._field_widgets = {}
        
        self.setup_ui()
    
    def _load_headers(self):
        """Загружает заголовки из файла"""
        df = pd.read_excel(self.file_path, sheet_name=0, nrows=0)
        return list(df.columns)
    
    def setup_ui(self):
        """Создает интерфейс"""
        # Заголовок
        header_frame = ctk.CTkFrame(self, fg_color="#1C222E")
        header_frame.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header_frame,
            text="🎯 Этап 2: Корректировка профиля бренда",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#EFF3F8"
        ).pack(anchor="w", padx=20, pady=15)
        
        ctk.CTkLabel(
            header_frame,
            text=f"Бренд: {self.detected_brand} | Файл: {os.path.basename(self.file_path)} ({len(self.headers)} колонок)",
            font=ctk.CTkFont(size=11),
            text_color="#7C8BA0"
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Основной контент
        content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Требуемые поля
        required_fields = ['Модель', 'Шум', 'Холод', 'Тепло', 'Мощность', 'Габариты', 'Цена']
        
        for field in required_fields:
            self.create_field_selector(content_frame, field)
        
        # Кнопки управления
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(
            button_frame,
            text="✓ Сохранить профиль",
            command=self.save_profile,
            fg_color="#00A8C5",
            hover_color="#0087A8"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="✕ Отмена",
            command=self.destroy,
            fg_color="#2C3E50"
        ).pack(side="left", padx=5)
    
    def create_field_selector(self, parent, field_name):
        """Создает селектор для одного поля"""
        card = ctk.CTkFrame(parent, fg_color="#1C222E", corner_radius=10)
        card.pack(fill="x", pady=10)
        
        # Заголовок поля
        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            title_frame,
            text=field_name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00A8C5"
        ).pack(anchor="w")
        
        # Combobox для выбора колонки
        combo_frame = ctk.CTkFrame(card, fg_color="transparent")
        combo_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            combo_frame,
            text="Выберите колонку:",
            font=ctk.CTkFont(size=10),
            text_color="#7C8BA0"
        ).pack(anchor="w", padx=0, pady=(0, 5))
        
        combo = ctk.CTkComboBox(
            combo_frame,
            values=self.headers,
            state="readonly",
            font=ctk.CTkFont(size=10),
            fg_color="#2C3E50",
            button_color="#00A8C5"
        )
        combo.pack(fill="x")
        combo.bind("<FocusOut>", lambda e: self._on_combo_change(field_name, combo, e))
        
        # Попытка предложить колонку автоматически
        suggested = importers.find_column_by_synonyms(self.headers, field_name, self.detected_brand)
        if suggested and suggested in self.headers:
            combo.set(suggested)
            self.selected_columns[field_name] = suggested
        
        # Поле для синонимов
        syn_frame = ctk.CTkFrame(card, fg_color="transparent")
        syn_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        ctk.CTkLabel(
            syn_frame,
            text="Дополнительные синонимы (через запятую):",
            font=ctk.CTkFont(size=9),
            text_color="#7C8BA0"
        ).pack(anchor="w", padx=0, pady=(0, 3))
        
        syn_entry = ctk.CTkEntry(
            syn_frame,
            placeholder_text="например: холодопроизв, cooling kw",
            font=ctk.CTkFont(size=9),
            fg_color="#2C3E50"
        )
        syn_entry.pack(fill="x")
        
        # Чекбокс для дефолтного значения
        default_var = BooleanVar()
        default_cb = Checkbutton(syn_frame, text="Заполнять пропуски дефолтным", 
                                 variable=default_var, font=("Segoe UI", 9), 
                                 bg="#1C222E", fg="#7C8BA0", selectcolor="#1C222E",
                                 activebackground="#1C222E")
        default_cb.pack(anchor="w", pady=(5, 0))
        
        # Сохраняем в словарь для доступа позже
        self._field_widgets[field_name] = {
            'combo': combo,
            'syn_entry': syn_entry,
            'default_var': default_var
        }
    
    def _on_combo_change(self, field_name, combo, event):
        """Обработка изменения выбора в combobox"""
        value = combo.get()
        if value:
            self.selected_columns[field_name] = value
    
    def save_profile(self):
        """Сохраняет профиль в brand_profiles.json"""
        # Собираем выбранные колонки и синонимы
        selected_cols = {}
        synonyms = {}
        filling_rules = {}
        
        for field_name, widgets in self._field_widgets.items():
            col = widgets['combo'].get()
            if col:
                selected_cols[field_name] = col
                
                # Получаем синонимы
                syn_text = widgets['syn_entry'].get().strip()
                if syn_text:
                    syns = [s.strip().lower() for s in syn_text.split(',') if s.strip()]
                    if syns:
                        synonyms[field_name] = syns
                
                # Заполнять пропуски дефолтным
                if widgets['default_var'].get():
                    filling_rules[field_name] = {
                        "use_default": True,
                        "default_value": None
                    }
        
        # Проверяем, что выбраны все обязательные поля
        required = ['Модель', 'Холод', 'Тепло', 'Мощность', 'Цена']
        missing = [f for f in required if f not in selected_cols]
        
        if missing:
            messagebox.showerror(
                "Ошибка",
                f"Пожалуйста, выберите колонки для: {', '.join(missing)}"
            )
            return
        
        # Сохраняем профиль
        brand_key = self.detected_brand.upper().replace(' ', '_')
        
        brand_profile = {
            "name": self.detected_brand,
            "aliases": [
                self.detected_brand.lower(),
                self.detected_brand.lower().replace(' ', ''),
                self.detected_brand.lower().replace('_', '')
            ],
            "column_synonyms": {},
            "filling_rules": filling_rules,
            "priority": 2,
            "manual_mapping": selected_cols,
            "confirmed_by_user": True
        }
        
        # Добавляем синонимы
        for field, col in selected_cols.items():
            brand_profile["column_synonyms"][field] = [col.lower()]
            if field in synonyms:
                brand_profile["column_synonyms"][field].extend(synonyms[field])
        
        # Обновляем profiles
        if 'brands' not in self.profiles:
            self.profiles['brands'] = {}
        
        self.profiles['brands'][brand_key] = brand_profile
        self.profiles['last_updated'] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Сохраняем в файл
        profile_path = os.path.join(os.path.dirname(__file__), 'brand_profiles.json')
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo(
                "✓ Успешно",
                f"Профиль '{brand_key}' сохранен!\n\n"
                f"Выбрано колонок: {len(selected_cols)}\n"
                f"При следующей загрузке файла этого бренда программа\n"
                f"автоматически применит эти настройки."
            )
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {e}")

def open_stage2_editor(parent, file_path):
    """Открывает окно редактора профиля (вызывается из главного приложения)"""
    editor = Stage2ProfileEditor(parent, file_path)
    editor.grab_set()