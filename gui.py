# -*- coding: utf-8 -*-
import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, simpledialog, colorchooser
import customtkinter as ctk
from datetime import datetime
import re
import pandas as pd  # Оптимизация: импорт на уровне модуля
import config
import importers
import doc_generator
import client_editor
import history
import history_window

# Настройка темы CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ========== ИСПРАВЛЕНИЕ РУССКОЙ РАСКЛАДКИ ==========
# В tkinter горячие клавиши (Ctrl+C, Ctrl+V и т.д.) работают только 
# когда клавиатура в английской раскладке. Этот код добавляет 
# поддержку русской раскладки.

def handle_ctrl_key(event):
    """Обрабатывает Ctrl+клавиша для русской раскладки."""
    # Коды клавиш при русской раскладке:
    # С (латинская) = 67, русская С = 0x93 (147)
    # В (латинская) = 86, русская В = 0x92 (146)
    # Х (латинская) = 72, русская Х = 0x95 (149)
    # Z (латинская) = 90, русская Я = 0x91 (145)
    # A (латинская) = 65, русская Ф = 0x60 (96)
    
    ctrl_state = 0x4  # Маска для Ctrl
    
    if event.state & ctrl_state:
        # Проверяем коды для обоих раскладок
        keycode = event.keycode
        
        # Английская раскладка (стандартные коды)
        english_map = {67: 'copy', 86: 'paste', 88: 'cut', 90: 'undo', 65: 'select_all'}
        # Русская раскладка (на тех же физических клавишах)
        russian_map = {67: 'copy', 86: 'paste', 88: 'cut', 90: 'undo', 65: 'select_all'}
        
        action = english_map.get(keycode)
        
        if action:
            widget = event.widget
            if action == 'copy':
                widget.event_generate('<<Copy>>')
            elif action == 'paste':
                widget.event_generate('<<Paste>>')
            elif action == 'cut':
                widget.event_generate('<<Cut>>')
            elif action == 'undo':
                widget.event_generate('<<Undo>>')
            elif action == 'select_all':
                widget.event_generate('<<SelectAll>>')
            return 'break'
    
    return None

class AutocompleteEntry(tk.Frame):
    """Entry с автодополнением, dropdown списком и видимым желтым курсором"""
    def __init__(self, master, values_getter=None, on_select=None, max_shown=10, **kwargs):
        super().__init__(master)
        
        self.values_getter = values_getter or (lambda: [])
        self.on_select = on_select
        self.max_shown = max_shown  # Максимум показываемых в списке
        self.filtered_values = []
        self.selected_index = 0
        
        width = kwargs.pop('width', 40)
        font = kwargs.pop('font', ('Segoe UI', 11))
        
        self.text_var = tk.StringVar()
        
        self.entry = tk.Entry(
            self, 
            textvariable=self.text_var,
            insertbackground='yellow',
            insertwidth=3,
            bg='#1C222E',
            fg='white',
            relief='flat',
            highlightbackground='#2C3E50',
            highlightthickness=1,
            font=font,
            width=width
        )
        self.entry.pack(fill='x')
        
        self.dropdown_frame = tk.Frame(self, bg='#1C222E', relief='flat', highlightthickness=1, highlightbackground='#2C3E50')
        
        scrollbar = tk.Scrollbar(self.dropdown_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.listbox = tk.Listbox(
            self.dropdown_frame,
            bg='#1C222E',
            fg='white',
            selectmode='single',
            highlightthickness=0,
            relief='flat',
            yscrollcommand=scrollbar.set,
            height=self.max_shown,
            font=font
        )
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # События
        self.text_var.trace('w', self._on_text_change)
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<Return>', self._on_enter)
        self.entry.bind('<Down>', self._on_down)
        self.entry.bind('<Up>', self._on_up)
        self.entry.bind('<Escape>', self._hide_dropdown)
        self.listbox.bind('<ButtonRelease-1>', self._on_listbox_select)
        self.listbox.bind('<Return>', self._on_listbox_enter)
    
    def _on_focus_in(self, event):
        """При получении фокуса показываем список всех клиентов."""
        text = self.text_var.get()
        all_values = self.values_getter()
        
        # Показываем первые max_shown клиентов
        if all_values:
            self.filtered_values = all_values[:self.max_shown]
            self._update_listbox()
            self.dropdown_frame.pack(fill='x', pady=(2, 0))
            self.selected_index = 0
            self.listbox.selection_set(0)
            self.listbox.see(0)
    
    def _on_text_change(self, *args):
        text = self.text_var.get()
        all_values = self.values_getter()
        
        if text:
            # Фильтруем по введённому тексту
            self.filtered_values = [v for v in all_values if text.lower() in v.lower()][:self.max_shown]
        else:
            # Показываем первых max_shown клиентов
            self.filtered_values = all_values[:self.max_shown]
        
        self._update_listbox()
        
        if self.filtered_values:
            self.dropdown_frame.pack(fill='x', pady=(2, 0))
            self.selected_index = 0
            self.listbox.selection_set(0)
            self.listbox.see(0)
        else:
            self.dropdown_frame.pack_forget()
    
    def _update_listbox(self):
        """Обновляет содержимое списка."""
        self.listbox.delete(0, tk.END)
        for item in self.filtered_values:
            self.listbox.insert(tk.END, item)
    
    def _hide_dropdown(self, event=None):
        self.dropdown_frame.pack_forget()
        return 'break'
        
    def _on_down(self, event):
        if not self.dropdown_frame.winfo_viewable():
            all_values = self.values_getter()
            self.filtered_values = all_values[:self.max_shown] if all_values else []
            if self.filtered_values:
                self._update_listbox()
                self.dropdown_frame.pack(fill='x', pady=(2, 0))
                self.listbox.selection_set(0)
        else:
            if self.selected_index < len(self.filtered_values) - 1:
                self.selected_index += 1
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(self.selected_index)
                self.listbox.see(self.selected_index)
        return 'break'
        
    def _on_up(self, event):
        if self.selected_index > 0:
            self.selected_index -= 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.selected_index)
            self.listbox.see(self.selected_index)
        return 'break'
        
    def _on_enter(self, event):
        if self.dropdown_frame.winfo_viewable() and self.listbox.curselection():
            self._on_listbox_select(None)
        elif self.filtered_values:
            self.text_var.set(self.filtered_values[0])
            self.dropdown_frame.pack_forget()
            if self.on_select:
                self.on_select()
        return 'break'
        
    def _on_listbox_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            selected = self.filtered_values[idx]
            self.text_var.set(selected)
            self.dropdown_frame.pack_forget()
            if self.on_select:
                self.on_select()
                
    def _on_listbox_enter(self, event):
        self._on_listbox_select(event)
        return 'break'
                
    def set_value(self, val):
        self.text_var.set(val)
        self.dropdown_frame.pack_forget()
        
    def get(self):
        return self.text_var.get()

class BrandProfileFrame(ctk.CTkFrame):
    """Фрейм для редактирования профилей брендов (вкладка Этапа 2)"""
    def __init__(self, master):
        super().__init__(master)
        self.profiles = self.load_profiles()
        self.current_brand = tk.StringVar()
        self.field_vars = {}
        self.create_widgets()
        
    def load_profiles(self):
        path = os.path.join(os.path.dirname(__file__), 'brand_profiles.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"brands": {}, "global_synonyms": {}}
    
    def save_profiles(self):
        path = os.path.join(os.path.dirname(__file__), 'brand_profiles.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, ensure_ascii=False, indent=2)
    
    def create_widgets(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", pady=(15,10), padx=20)
        
        ctk.CTkLabel(top_frame, text="Выберите бренд:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0,10))
        self.brand_combo = ctk.CTkComboBox(top_frame, variable=self.current_brand, values=list(self.profiles['brands'].keys()),
                                           command=self.on_brand_selected)
        self.brand_combo.pack(side="left", padx=(0,10))
        ctk.CTkButton(top_frame, text="Добавить", width=80, command=self.add_brand).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Удалить", width=80, command=self.delete_brand).pack(side="left", padx=5)
        
        form_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0,15))
        
        ctk.CTkLabel(form_frame, text="Алиасы (через запятую):", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.aliases_var = tk.StringVar()
        aliases_entry = ctk.CTkEntry(form_frame, textvariable=self.aliases_var, placeholder_text="например: lessar, лессар")
        aliases_entry.pack(fill="x", pady=(0,15))
        
        fields = ['Модель', 'Шум', 'Холод', 'Тепло', 'Мощность', 'Габариты', 'Цена']
        for field in fields:
            frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            frame.pack(fill="x", pady=5)
            ctk.CTkLabel(frame, text=f"Синонимы для '{field}':", text_color="#7C8BA0", width=150, anchor="w").pack(side="left", padx=(0,10))
            var = tk.StringVar()
            entry = ctk.CTkEntry(frame, textvariable=var, placeholder_text="вводите через запятую")
            entry.pack(side="left", fill="x", expand=True)
            self.field_vars[field] = var
        
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=(0,20))
        ctk.CTkButton(bottom_frame, text="Сохранить профиль", command=self.save_current_profile,
                      fg_color="#00A8C5", hover_color="#00BCD9", font=ctk.CTkFont(weight="bold"), height=35).pack(fill="x")
    
    def on_brand_selected(self, *args):
        brand = self.current_brand.get()
        if brand in self.profiles['brands']:
            info = self.profiles['brands'][brand]
            self.aliases_var.set(', '.join(info.get('aliases', [])))
            col_syns = info.get('column_synonyms', {})
            for field, var in self.field_vars.items():
                var.set(', '.join(col_syns.get(field, [])))
        else:
            self.clear_fields()
    
    def clear_fields(self):
        self.aliases_var.set('')
        for var in self.field_vars.values():
            var.set('')
    
    def add_brand(self):
        brand_name = simpledialog.askstring("Новый бренд", "Введите название бренда (английскими буквами, например LESSAR):")
        if not brand_name:
            return
        brand_name = brand_name.strip().upper().replace(' ', '_')
        if brand_name in self.profiles['brands']:
            messagebox.showwarning("Предупреждение", "Такой бренд уже существует.")
            return
        self.profiles['brands'][brand_name] = {"aliases": [], "column_synonyms": {}}
        self.save_profiles()
        importers.clear_brand_cache()
        self.brand_combo.configure(values=list(self.profiles['brands'].keys()))
        self.current_brand.set(brand_name)
        self.clear_fields()
    
    def delete_brand(self):
        brand = self.current_brand.get()
        if not brand:
            messagebox.showwarning("Предупреждение", "Сначала выберите бренд.")
            return
        if messagebox.askyesno("Удаление бренда", f"Вы уверены, что хотите удалить профиль бренда '{brand}'?"):
            del self.profiles['brands'][brand]
            self.save_profiles()
            importers.clear_brand_cache()
            self.brand_combo.configure(values=list(self.profiles['brands'].keys()))
            if self.profiles['brands']:
                self.current_brand.set(list(self.profiles['brands'].keys())[0])
                self.on_brand_selected()
            else:
                self.current_brand.set('')
                self.clear_fields()
    
    def save_current_profile(self):
        brand = self.current_brand.get()
        if not brand:
            messagebox.showwarning("Предупреждение", "Выберите бренд.")
            return
        aliases = [a.strip() for a in self.aliases_var.get().split(',') if a.strip()]
        col_syns = {}
        for field, var in self.field_vars.items():
            syns = [s.strip() for s in var.get().split(',') if s.strip()]
            if syns:
                col_syns[field] = syns
        self.profiles['brands'][brand]['aliases'] = aliases
        self.profiles['brands'][brand]['column_synonyms'] = col_syns
        self.save_profiles()
        importers.clear_brand_cache()
        messagebox.showinfo("Успех", f"Профиль бренда '{brand}' сохранён.")

def show_copyable_error(parent, title, message):
    """Показывает модальное окно с возможностью выделить и скопировать текст ошибки."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("700x400")
    dialog.resizable(True, True)
    dialog.transient(parent)
    dialog.grab_set()
    
    lbl = ctk.CTkLabel(dialog, text="Текст ошибки (выделите мышью и нажмите Ctrl+C):", 
                       font=ctk.CTkFont(size=12, weight="bold"))
    lbl.pack(pady=(10, 5), padx=10, anchor="w")
    
    text_widget = tk.Text(dialog, bg="#1C222E", fg="white", wrap="word", relief="flat", 
                          highlightthickness=1, highlightbackground="#2C3E50")
    text_widget.insert("1.0", message)
    text_widget.configure(state="disabled")
    text_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    btn_close = ctk.CTkButton(dialog, text="Закрыть", command=dialog.destroy)
    btn_close.pack(pady=5)
    text_widget.focus_set()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Создание коммерческого предложения")
        self.geometry("1200x800")
        self.minsize(1100, 700)
        self.configure(fg_color="#0A0F1A")
        
        self.models = config.load_models()
        self.variants = []
        
        # ===== КЭШ ДЛЯ АВТОДОПОЛНЕНИЯ =====
        self._clients_cache = None  # Кэш списка клиентов
        self._clients_cache_time = 0  # Время последнего обновления кэша
        
        self.configure_styles()
        
        self.setup_ui()
        self.update_variants_list()
        self.update_models_view()
        self.load_settings_into_entries()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Привязываем обработчик русской раскладки ко всему окну
        self.bind('<Key>', handle_ctrl_key)
        
    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'TCombobox',
            fieldbackground='#1C222E',
            background='#2C3E50',
            foreground='white',
            selectbackground='#00A8C5',
            selectforeground='white',
            bordercolor='#2C3E50',
            lightcolor='#2C3E50',
            darkcolor='#2C3E50',
            arrowcolor='white'
        )
        style.map('TCombobox', fieldbackground=[('readonly', '#1C222E')])
        
    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self, fg_color="#141923", segmented_button_selected_color="#00A8C5", segmented_button_unselected_hover_color="#00BCD9")
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.tab_offer = self.tabview.add("Создание КП")
        self.tab_models = self.tabview.add("База моделей")
        self.tab_brands = self.tabview.add("Профили брендов")
        self.tab_settings = self.tabview.add("Настройки компании")
        
        self.setup_offer_tab()
        self.setup_models_tab()
        self.setup_brands_tab()
        self.setup_settings_tab()
        
    # ==================== ВКЛАДКА 1: СОЗДАНИЕ КП ====================
    def setup_offer_tab(self):
        main_frame = ctk.CTkFrame(self.tab_offer, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- Карточка Заказчика ---
        card_customer = ctk.CTkFrame(main_frame, corner_radius=15, fg_color="#1C222E")
        card_customer.pack(fill="x", pady=(0,15))
        
        # Заголовок с кнопкой управления клиентами
        header_frame = ctk.CTkFrame(card_customer, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(12,5))
        
        ctk.CTkLabel(header_frame, text="Информация о заказчике", font=ctk.CTkFont(size=16, weight="bold"), text_color="#EFF3F8").pack(side="left")
        
        ctk.CTkButton(
            header_frame,
            text="👥 Клиенты",
            command=self.open_client_editor,
            fg_color="#2C3E50",
            hover_color="#3E5A6F",
            height=28,
            font=ctk.CTkFont(size=11)
        ).pack(side="right")
        
        cust_frame = ctk.CTkFrame(card_customer, fg_color="transparent")
        cust_frame.pack(fill="x", padx=15, pady=(0,15))
        cust_frame.columnconfigure((0,1,2,3), weight=1)
        
        komu_lbl_frame = ctk.CTkFrame(cust_frame, fg_color="transparent")
        komu_lbl_frame.grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkLabel(komu_lbl_frame, text="Заказчик:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w", padx=2)
        self.komu_combo = AutocompleteEntry(komu_lbl_frame, values_getter=self.get_all_clients, on_select=self.on_komu_select, max_shown=10)
        self.komu_combo.pack(fill="x", pady=(2,0))
        
        phone_lbl_frame = ctk.CTkFrame(cust_frame, fg_color="transparent")
        phone_lbl_frame.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(phone_lbl_frame, text="Тел.:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w", padx=2)
        self.phone_entry = ctk.CTkEntry(phone_lbl_frame, placeholder_text="Телефон")
        self.phone_entry.pack(fill="x", pady=(2,0))
        
        email_lbl_frame = ctk.CTkFrame(cust_frame, fg_color="transparent")
        email_lbl_frame.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkLabel(email_lbl_frame, text="Email:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w", padx=2)
        self.email_entry = ctk.CTkEntry(email_lbl_frame, placeholder_text="Email")
        self.email_entry.pack(fill="x", pady=(2,0))
        
        ot_lbl_frame = ctk.CTkFrame(cust_frame, fg_color="transparent")
        ot_lbl_frame.grid(row=0, column=3, padx=5, sticky="ew")
        ctk.CTkLabel(ot_lbl_frame, text="Контактное лицо:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w", padx=2)
        self.ot_entry = ctk.CTkEntry(ot_lbl_frame, placeholder_text="Менеджер")
        self.ot_entry.pack(fill="x", pady=(2,0))
        
        obj_lbl_frame = ctk.CTkFrame(cust_frame, fg_color="transparent")
        obj_lbl_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(10,0), sticky="ew")
        ctk.CTkLabel(obj_lbl_frame, text="Объект:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w", padx=2)
        self.object_entry = ctk.CTkEntry(obj_lbl_frame, placeholder_text="Адрес/название объекта")
        self.object_entry.pack(fill="x", pady=(2,0))
        
        date_lbl_frame = ctk.CTkFrame(cust_frame, fg_color="transparent")
        date_lbl_frame.grid(row=1, column=2, columnspan=2, padx=5, pady=(10,0), sticky="ew")
        ctk.CTkLabel(date_lbl_frame, text="Дата:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w", padx=2)
        self.date_entry = ctk.CTkEntry(date_lbl_frame, placeholder_text="ДД.ММ.ГГГГ")
        self.date_entry.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.date_entry.pack(fill="x", pady=(2,0))
        
        self.update_clients_combo_values()
        
        # --- Две колонки ---
        columns_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        columns_frame.pack(fill="both", expand=True)
        columns_frame.columnconfigure(0, weight=6)
        columns_frame.columnconfigure(1, weight=4)
        
        left_panel = ctk.CTkFrame(columns_frame, corner_radius=15, fg_color="#1C222E")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        
        ctk.CTkLabel(left_panel, text="Варианты предложения", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(12,5))
        self.variants_frame = ctk.CTkScrollableFrame(left_panel, fg_color="#141923", corner_radius=10)
        self.variants_frame.pack(fill="both", expand=True, padx=15, pady=(5,15))
        
        right_panel = ctk.CTkFrame(columns_frame, corner_radius=15, fg_color="#1C222E")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10,0))
        
        ctk.CTkLabel(right_panel, text="Добавить вариант кондиционера", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(12,10))
        
        ctk.CTkLabel(right_panel, text="Модель:", text_color="#7C8BA0").pack(anchor="w", padx=20)
        self.model_combo = AutocompleteEntry(
            right_panel,
            values_getter=lambda: list(self.models.keys()),
            font=('Segoe UI', 11),
            width=28
        )
        self.model_combo.pack(anchor="w", padx=20, pady=(2,12))
        
        ctk.CTkLabel(right_panel, text="Количество (шт.):", text_color="#7C8BA0").pack(anchor="w", padx=20)
        self.qty_entry = ctk.CTkEntry(right_panel, width=150)
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(anchor="w", padx=20, pady=(2,12))
        
        ctk.CTkLabel(right_panel, text="Монтаж (руб.):", text_color="#7C8BA0").pack(anchor="w", padx=20)
        self.install_entry = ctk.CTkEntry(right_panel, width=150)
        self.install_entry.insert(0, "26000")
        self.install_entry.pack(anchor="w", padx=20, pady=(2,12))
        
        ctk.CTkLabel(right_panel, text="Согласование (руб.):", text_color="#7C8BA0").pack(anchor="w", padx=20)
        self.approval_entry = ctk.CTkEntry(right_panel, width=150)
        self.approval_entry.insert(0, "5000")
        self.approval_entry.pack(anchor="w", padx=20, pady=(2,15))
        
        btn_add = ctk.CTkButton(right_panel, text="Добавить вариант", command=self.add_variant, fg_color="#00A8C5", hover_color="#00BCD9", font=ctk.CTkFont(weight="bold"))
        btn_add.pack(fill="x", padx=20, pady=(0,15))
        
        # --- Нижняя панель действий ---
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(15,0))
        
        btn_new_kp = ctk.CTkButton(bottom_frame, text="Новое КП", command=self.clear_offer, 
                                   fg_color="#8B0000", hover_color="#B00000", font=ctk.CTkFont(size=14, weight="bold"), height=40)
        btn_new_kp.pack(side="left", padx=5)
        
        btn_history = ctk.CTkButton(bottom_frame, text="📋 История", command=self.open_history,
                                    fg_color="#2C3E50", hover_color="#3E5A6F", font=ctk.CTkFont(size=14, weight="bold"), height=40)
        btn_history.pack(side="left", padx=5)
        
        btn_generate = ctk.CTkButton(bottom_frame, text="Создать предложение (DOCX / PDF)", command=self.generate_offer, 
                                     fg_color="#2C9B7A", hover_color="#3DB892", font=ctk.CTkFont(size=14, weight="bold"), height=40)
        btn_generate.pack(side="right", padx=5)

    # ==================== ВКЛАДКА 2: БАЗА МОДЕЛЕЙ ====================
    def setup_models_tab(self):
        models_frame = ctk.CTkFrame(self.tab_models, fg_color="transparent")
        models_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        models_frame.columnconfigure(0, weight=6)
        models_frame.columnconfigure(1, weight=4)
        
        left_panel = ctk.CTkFrame(models_frame, corner_radius=15, fg_color="#1C222E")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        
        ctk.CTkLabel(left_panel, text="Список моделей кондиционеров", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(12,5))
        self.models_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="#141923", corner_radius=10)
        self.models_scroll.pack(fill="both", expand=True, padx=15, pady=(5,15))
        
        right_panel = ctk.CTkFrame(models_frame, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10,0))
        
        import_card = ctk.CTkFrame(right_panel, corner_radius=15, fg_color="#1C222E")
        import_card.pack(fill="x", pady=(0,15))
        
        ctk.CTkLabel(import_card, text="Импорт моделей из файлов", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(12,8))
        btn_excel = ctk.CTkButton(import_card, text="Импортировать Excel / CSV", command=self.import_excel, fg_color="#2C3E50", hover_color="#3E5A6F")
        btn_excel.pack(fill="x", padx=20, pady=5)
        btn_stage2 = ctk.CTkButton(import_card, text="Этап 2: Настроить профиль бренда", command=self.go_to_brands_tab, fg_color="#00A8C5", hover_color="#0087A8")
        btn_stage2.pack(fill="x", padx=20, pady=5)
        btn_pdf = ctk.CTkButton(import_card, text="Импортировать из PDF", command=self.import_pdf_models, fg_color="#2C3E50", hover_color="#3E5A6F")
        btn_pdf.pack(fill="x", padx=20, pady=(5,15))
        
        add_card = ctk.CTkFrame(right_panel, corner_radius=15, fg_color="#1C222E")
        add_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(add_card, text="Добавить новую модель вручную", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(12,10))
        
        self.new_model_entries = {}
        fields = [
            ("Название модели:", "model_key", "например, RCI-FCE30HN/IN"),
            ("Описание серии:", "description", "например, Сплит-система настенного типа с инвертором..."),
            ("Уровень шума (дБ):", "noise_level", "например, 20-35"),
            ("Охлаждение (кВт):", "cooling_kw", "например, 3.00 (1.17 - 3.37)"),
            ("Обогрев (кВт):", "heating_kw", "например, 3.45 (0.91 - 3.52)"),
            ("Мощность (кВт):", "power_kw", "например, 0.833 (0.10 - 1.02)"),
            ("Габариты (ШхГхВ мм):", "dimensions", "например, 729x200x292"),
            ("Цена (руб.):", "price", "например, 35000")
        ]
        
        form_scroll = ctk.CTkScrollableFrame(add_card, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        for label, key, placeholder in fields:
            ctk.CTkLabel(form_scroll, text=label, text_color="#7C8BA0").pack(anchor="w", padx=10)
            ent = ctk.CTkEntry(form_scroll, placeholder_text=placeholder)
            ent.pack(fill="x", padx=10, pady=(2,8))
            self.new_model_entries[key] = ent
            
        btn_save_model = ctk.CTkButton(add_card, text="Сохранить модель", command=self.manual_add_model, fg_color="#00A8C5", hover_color="#00BCD9", font=ctk.CTkFont(weight="bold"))
        btn_save_model.pack(fill="x", padx=20, pady=15)

    # ==================== ВКЛАДКА 3: ПРОФИЛИ БРЕНДОВ ====================
    def setup_brands_tab(self):
        self.brand_profile_frame = BrandProfileFrame(self.tab_brands)
        self.brand_profile_frame.pack(fill="both", expand=True)
    
    def go_to_brands_tab(self):
        self.tabview.set("Профили брендов")

    # ==================== ВКЛАДКА 4: НАСТРОЙКИ КОМПАНИИ ====================
    def setup_settings_tab(self):
        settings_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        card_settings = ctk.CTkFrame(settings_frame, corner_radius=15, fg_color="#1C222E")
        card_settings.pack(fill="both", expand=True)
        
        ctk.CTkLabel(card_settings, text="Реквизиты вашей организации (для шапки КП)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=25, pady=(15,15))
        
        form_frame = ctk.CTkScrollableFrame(card_settings, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=25, pady=(0,20))
        
        self.settings_entries = {}
        
        ctk.CTkLabel(form_frame, text="Название организации (краткое):", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.settings_entries["company_name"] = ctk.CTkEntry(form_frame, placeholder_text="Например: НЕВА КОН")
        self.settings_entries["company_name"].pack(fill="x", pady=(0,10))
        
        ctk.CTkLabel(form_frame, text="Направления деятельности (одно или несколько через перенос строки):", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.settings_activity_text = tk.Text(form_frame, height=3, bg="#1C222E", fg="white", insertbackground="white", relief="flat", highlightbackground="#2C3E50", highlightthickness=1)
        self.settings_activity_text.pack(fill="x", pady=(0,10))
        
        ctk.CTkLabel(form_frame, text="Адрес офиса:", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.settings_entries["address"] = ctk.CTkEntry(form_frame, placeholder_text="Например: г. СПб, Детский пер., д. 5")
        self.settings_entries["address"].pack(fill="x", pady=(0,10))
        
        ctk.CTkLabel(form_frame, text="Контактные телефоны и e-mail:", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.settings_entries["contacts"] = ctk.CTkEntry(form_frame, placeholder_text="Например: тел. (812) 622-09-49   e-mail: mail@nevacon.ru")
        self.settings_entries["contacts"].pack(fill="x", pady=(0,10))
        
        ctk.CTkLabel(form_frame, text="Сайт компании:", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.settings_entries["website"] = ctk.CTkEntry(form_frame, placeholder_text="Например: https://www.nevacon.ru")
        self.settings_entries["website"].pack(fill="x", pady=(0,10))
        
        ctk.CTkLabel(form_frame, text="Слоган или перечень услуг:", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.settings_entries["services"] = ctk.CTkEntry(form_frame, placeholder_text="Например: проектирование – монтаж - сервисное обслуживание")
        self.settings_entries["services"].pack(fill="x", pady=(0,10))
        
        ctk.CTkLabel(form_frame, text="Подпись менеджера в подвале:", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.settings_entries["manager_signature"] = ctk.CTkEntry(form_frame, placeholder_text="Например: Толстиков Игорь.")
        self.settings_entries["manager_signature"].pack(fill="x", pady=(0,20))
        
        # --- Логотип ---
        ctk.CTkLabel(form_frame, text="Логотип (изображение):", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        logo_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(0,5))
        self.logo_path_var = tk.StringVar()
        logo_entry = ctk.CTkEntry(logo_frame, textvariable=self.logo_path_var, placeholder_text="Путь к файлу логотипа")
        logo_entry.pack(side="left", fill="x", expand=True)
        btn_browse_logo = ctk.CTkButton(logo_frame, text="Обзор", width=60, command=self.choose_logo)
        btn_browse_logo.pack(side="right", padx=(5,0))
        
        ctk.CTkLabel(form_frame, text="Ширина логотипа (см):", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.logo_width_var = tk.StringVar(value="3.0")
        logo_width_entry = ctk.CTkEntry(form_frame, textvariable=self.logo_width_var, width=80)
        logo_width_entry.pack(anchor="w", pady=(0,10))
        
        # --- Основной цвет ---
        ctk.CTkLabel(form_frame, text="Основной цвет (HEX):", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        color_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        color_frame.pack(fill="x", pady=(0,10))
        self.color_var = tk.StringVar()
        color_entry = ctk.CTkEntry(color_frame, textvariable=self.color_var, placeholder_text="#00A8C5", width=100)
        color_entry.pack(side="left")
        self.color_preview = tk.Canvas(color_frame, width=30, height=20, bg="#00A8C5", highlightthickness=0)
        self.color_preview.pack(side="left", padx=10)
        btn_pick_color = ctk.CTkButton(color_frame, text="Палитра", width=60, command=self.pick_color)
        btn_pick_color.pack(side="left", padx=5)
        
        # --- Шрифт ---
        ctk.CTkLabel(form_frame, text="Шрифт:", text_color="#7C8BA0").pack(anchor="w", pady=(5,2))
        self.font_var = tk.StringVar(value="Segoe UI")
        font_combo = ttk.Combobox(form_frame, textvariable=self.font_var,
                                  values=["Arial", "Times New Roman", "Calibri", "Cambria", "Courier New", "Verdana", "Segoe UI"],
                                  state="readonly")
        font_combo.pack(fill="x", pady=(0,20))
        
        btn_save_settings = ctk.CTkButton(card_settings, text="Сохранить настройки", command=self.save_settings_from_gui, fg_color="#2C9B7A", hover_color="#3DB892", font=ctk.CTkFont(size=14, weight="bold"), height=38)
        btn_save_settings.pack(fill="x", padx=25, pady=15)
        
        self.color_var.trace('w', lambda *args: self.update_color_preview())

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ НАСТРОЕК ====================
    def update_color_preview(self):
        try:
            color = self.color_var.get().strip()
            self.color_preview.configure(bg=color)
        except:
            pass

    def choose_logo(self):
        path = filedialog.askopenfilename(filetypes=[("Изображения", "*.png;*.jpg;*.jpeg;*.bmp")])
        if path:
            self.logo_path_var.set(path)

    def pick_color(self):
        color_tuple = colorchooser.askcolor(color=self.color_var.get())
        if color_tuple and color_tuple[1]:
            self.color_var.set(color_tuple[1])
            self.update_color_preview()

    # ==================== ЛОГИКА ====================
    def open_history(self):
        """Открывает окно истории КП."""
        history_window.open_history_window(self, on_load_callback=self.load_proposal_from_history)
    
    def load_proposal_from_history(self, proposal):
        """Загружает предложение из истории в текущее КП."""
        client = proposal.get('client', {})
        variants = proposal.get('variants', [])
        
        self.komu_combo.set_value(client.get('name', ''))
        self.ot_entry.delete(0, tk.END)
        self.ot_entry.insert(0, client.get('contact_person', ''))
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, client.get('phone', ''))
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, client.get('email', ''))
        self.object_entry.delete(0, tk.END)
        self.object_entry.insert(0, client.get('object', ''))
        
        self.variants = variants.copy()
        self.update_variants_list()
        
        messagebox.showinfo("Загружено", f"Предложение для '{client.get('name')}' загружено!\nВы можете отредактировать и создать новое.")
    
    def open_client_editor(self):
        """Открывает окно управления клиентами."""
        client_editor.open_client_editor(self)
        # Сбросить кэш клиентов - данные могли измениться
        self._clients_cache = None
        self._clients_cache_time = 0
        self.update_clients_combo_values()
    
    def get_all_clients(self):
        """Получает список всех клиентов (только названия) с кэшированием."""
        import time
        now = time.time()
        
        # Если кэш свежий (менее 2 сек) - возвращаем его
        if self._clients_cache is not None and (now - self._clients_cache_time) < 2.0:
            return self._clients_cache
        
        # Иначе загружаем заново
        clients = config.load_clients()
        self._clients_cache = [c.get('name', '') for c in clients if c.get('name')]
        self._clients_cache_time = now
        return self._clients_cache
    
    def update_clients_combo_values(self):
        """Обновляет автодополнение клиентов."""
        pass
        
    def on_komu_select(self, event=None):
        """Обработчик выбора клиента из списка."""
        selected_name = self.komu_combo.get()
        if not selected_name:
            return
        
        clients = config.load_clients()
        
        for c in clients:
            if c.get('name') == selected_name:
                self._batch_update_fields([
                    (self.ot_entry, c.get('contact_person', '')),
                    (self.object_entry, c.get('object_name', '')),
                    (self.phone_entry, c.get('phone', '')),
                    (self.email_entry, c.get('email', '')),
                ])
                break
    
    def _batch_update_fields(self, updates):
        """Массовое обновление полей (простой вариант без мерцания)."""
        for widget, value in updates:
            widget.delete(0, tk.END)
            widget.insert(0, value)
    
    def _batch_clear_fields(self, widgets):
        """Массовая очистка полей (простой вариант)."""
        for widget in widgets:
            widget.delete(0, tk.END)
    
    def save_current_client(self):
        """Сохраняет текущие данные клиента (вызывается при уходе из поля)."""
        name = self.komu_combo.get().strip()
        if not name:
            return
        
        clients = config.load_clients()
        
        # Ищем существующего клиента
        existing = None
        for c in clients:
            if c.get('name') == name:
                existing = c
                break
        
        if existing:
            # Обновляем
            config.update_client(existing.get('id'), {
                'name': name,
                'contact_person': self.ot_entry.get().strip(),
                'phone': self.phone_entry.get().strip(),
                'email': self.email_entry.get().strip(),
                'object_name': self.object_entry.get().strip(),
            })
        else:
            # Добавляем нового
            config.add_client({
                'name': name,
                'contact_person': self.ot_entry.get().strip(),
                'phone': self.phone_entry.get().strip(),
                'email': self.email_entry.get().strip(),
                'object_name': self.object_entry.get().strip(),
            })
        
        # Сбросить кэш - данные изменились
        self._clients_cache = None
        self._clients_cache_time = 0
                
    def add_variant(self):
        model = self.model_combo.get().strip()
        if not model:
            messagebox.showerror("Ошибка", "Сначала выберите или добавьте модель кондиционера.")
            return
        if model not in self.models:
            messagebox.showerror("Ошибка", f"Модель '{model}' не найдена в базе данных. Выберите модель из списка или добавьте её во вкладке 'База моделей'.")
            return
            
        qty_str = self.qty_entry.get().strip()
        install_str = self.install_entry.get().strip()
        approval_str = self.approval_entry.get().strip()
        
        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Ошибка", f"Некорректное значение количества: '{qty_str}'. Введите целое число больше нуля.")
            return
        try:
            install = int(install_str)
            if install < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Ошибка", f"Некорректное значение стоимости монтажа: '{install_str}'. Введите целое положительное число.")
            return
        try:
            approval = int(approval_str)
            if approval < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Ошибка", f"Некорректное значение стоимости согласования: '{approval_str}'. Введите целое положительное число.")
            return
            
        self.variants.append({
            "model_key": model,
            "quantity": qty,
            "installation_price": install,
            "approval_price": approval
        })
        self.update_variants_list()
        self.model_combo.set_value("")
        self.model_combo.entry.focus_set()
        
    def remove_variant(self, index):
        if 0 <= index < len(self.variants):
            del self.variants[index]
            self.update_variants_list()
            
    def update_variants_list(self):
        """Обновляет список вариантов в интерфейсе."""
        for widget in self.variants_frame.winfo_children():
            widget.destroy()
        
        if not self.variants:
            lbl = ctk.CTkLabel(self.variants_frame, text="Нет добавленных вариантов в коммерческом предложении.", text_color="#7C8BA0", font=ctk.CTkFont(slant="italic"))
            lbl.pack(pady=20)
            return

        for i, var in enumerate(self.variants):
            row = ctk.CTkFrame(self.variants_frame, fg_color="#1C222E" if i % 2 == 0 else "#252B37", corner_radius=6)
            row.pack(fill="x", pady=2, padx=5)
            model = self.models.get(var["model_key"], {})
            price = model.get("price", 0)
            total_equip = price * var["quantity"]
            total = total_equip + var["installation_price"] + var["approval_price"]
            
            info_txt = f"{i+1}. {var['model_key']}  (Кол-во: {var['quantity']} шт.)  |  Итого: {total:,} руб.".replace(",", " ")
            lbl = ctk.CTkLabel(row, text=info_txt, font=ctk.CTkFont(size=12))
            lbl.pack(side="left", padx=12, pady=8)
            
            btn_del = ctk.CTkButton(
                row,
                text="Удалить",
                width=65,
                height=22,
                fg_color="#8B0000",
                hover_color="#B00000",
                text_color="white",
                command=lambda i=i: self.remove_variant(i)
            )
            btn_del.pack(side="right", padx=10, pady=8)
            
    def clear_offer(self):
        """Очищает все поля текущего предложения."""
        self.komu_combo.set_value("")
        self.phone_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.ot_entry.delete(0, tk.END)
        self.object_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.variants.clear()
        self.update_variants_list()
        self.model_combo.set_value("")
        
    def generate_offer(self):
        if not self.variants:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один вариант в предложение.")
            return
        
        # Сохраняем текущего клиента
        self.save_current_client()
        
        to_val = self.komu_combo.get().strip()
        from_val = self.ot_entry.get().strip()
        obj_val = self.object_entry.get().strip()
        phone_val = self.phone_entry.get().strip()
        email_val = self.email_entry.get().strip()
        date_val = self.date_entry.get().strip()
        
        if not to_val:
            messagebox.showerror("Ошибка", "Поле 'Заказчик' не может быть пустым.")
            return
            
        client_data = {
            "to": to_val,
            "from": from_val,
            "object": obj_val,
            "phone": phone_val,
            "email": email_val,
            "date": date_val
        }
        
        config.add_client_if_new(client_data)
        self.update_clients_combo_values()
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Формат экспорта")
        dialog.geometry("350x180")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        x = self.winfo_x() + (self.winfo_width() // 2) - 175
        y = self.winfo_y() + (self.winfo_height() // 2) - 90
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="В каком формате сохранить предложение?", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(20, 15))
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)
        
        def save_docx():
            dialog.destroy()
            out_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Документы Word", "*.docx")])
            if out_path:
                try:
                    doc_generator.generate_docx(self.variants, client_data, out_path)
                    # Сохраняем в историю
                    history.add_proposal(self.variants, client_data, out_path)
                    messagebox.showinfo("Готово", f"Коммерческое предложение в формате Word успешно сохранено:\n{out_path}")
                except Exception as e:
                    show_copyable_error(self, "Ошибка сохранения", str(e))

        def save_pdf():
            dialog.destroy()
            out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Документы PDF", "*.pdf")])
            if out_path:
                try:
                    doc_generator.generate_pdf(self.variants, client_data, out_path)
                    # Сохраняем в историю
                    history.add_proposal(self.variants, client_data, out_path)
                    messagebox.showinfo("Готово", f"Коммерческое предложение в формате PDF успешно сохранено:\n{out_path}")
                except Exception as e:
                    show_copyable_error(self, "Ошибка сохранения", str(e))
                    
        ctk.CTkButton(btn_frame, text="Word (.docx)", fg_color="#2C3E50", hover_color="#3E5A6F", command=save_docx).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="PDF (.pdf)", fg_color="#2C9B7A", hover_color="#3DB892", command=save_pdf).pack(side="right", expand=True, padx=5)

    # ==================== ЛОГИКА ВКЛАДКИ БАЗЫ МОДЕЛЕЙ ====================
    def update_models_view(self):
        """Обновляет список моделей в интерфейсе."""
        for widget in self.models_scroll.winfo_children():
            widget.destroy()
        
        if not self.models:
            lbl = ctk.CTkLabel(self.models_scroll, text="База моделей пуста. Добавьте модели вручную или импортируйте.", text_color="#7C8BA0", font=ctk.CTkFont(slant="italic"))
            lbl.pack(pady=20)
            return

        for i, (m_key, specs) in enumerate(self.models.items()):
            row = ctk.CTkFrame(self.models_scroll, fg_color="#1C222E" if i % 2 == 0 else "#252B37", corner_radius=6)
            row.pack(fill="x", pady=2, padx=5)
            desc = f"Шум: {specs.get('noise_level', 'N/A')} дБ | Холод: {specs.get('cooling_kw', 'N/A')} кВт | Тепло: {specs.get('heating_kw', 'N/A')} кВт | Мощн: {specs.get('power_kw', 'N/A')} кВт"
            extra = []
            if specs.get('manufacturer'):
                extra.append(specs['manufacturer'])
            if specs.get('series'):
                extra.append(specs['series'])
            details_frame = ctk.CTkFrame(row, fg_color="transparent")
            details_frame.pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(details_frame, text=m_key, font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(anchor="w")
            desc_val = specs.get('description') or (" | ".join(extra) if extra else 'Сплит-система настенного типа')
            ctk.CTkLabel(details_frame, text=desc_val, font=ctk.CTkFont(size=11, slant="italic"), text_color="#00BCD9", anchor="w").pack(anchor="w")
            ctk.CTkLabel(details_frame, text=desc, font=ctk.CTkFont(size=11), text_color="#7C8BA0", anchor="w").pack(anchor="w")
            right_side = ctk.CTkFrame(row, fg_color="transparent")
            right_side.pack(side="right", padx=10, pady=6)
            ctk.CTkLabel(right_side, text=f"{specs.get('price', 0):,} руб.".replace(",", " "), font=ctk.CTkFont(size=12, weight="bold"), text_color="#00A8C5").pack(side="left", padx=15)
            ctk.CTkButton(
                right_side,
                text="Удалить",
                width=65,
                height=22,
                fg_color="#8B0000",
                hover_color="#B00000",
                command=lambda k=m_key: self.delete_model(k)
            ).pack(side="right")
    
    def delete_model(self, key):
        """Удаляет модель из базы данных."""
        if messagebox.askyesno("Удаление модели", f"Вы уверены, что хотите удалить модель '{key}' из базы?"):
            if key in self.models:
                del self.models[key]
                config.save_models(self.models)
                self.update_models_view()
                
    def manual_add_model(self):
        data = {}
        model_name = self.new_model_entries["model_key"].get().strip()
        if not model_name:
            messagebox.showerror("Ошибка", "Поле 'Название модели' не может быть пустым.")
            return
        for key, entry in self.new_model_entries.items():
            if key == "model_key":
                continue
            val = entry.get().strip()
            if not val:
                messagebox.showerror("Ошибка", f"Поле '{entry.cget('placeholder_text')}' не заполнено.")
                return
            if key == "price":
                try:
                    val = int(val)
                    if val <= 0:
                        raise ValueError()
                except ValueError:
                    messagebox.showerror("Ошибка", "Цена модели должна быть положительным числом.")
                    return
            data[key] = val
        if model_name in self.models:
            if not messagebox.askyesno("Подтверждение", f"Модель '{model_name}' уже существует в базе. Перезаписать?"):
                return
        self.models[model_name] = data
        config.save_models(self.models)
        self.update_models_view()
        for entry in self.new_model_entries.values():
            entry.delete(0, tk.END)
        messagebox.showinfo("Успех", f"Модель '{model_name}' успешно добавлена в базу данных.")
        
    def import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Документы Excel / CSV", "*.xlsx *.xls .csv")])
        if path:
            try:
                df_test = pd.read_excel(path, sheet_name=0, nrows=5) if path.endswith(('.xlsx', '.xls')) else None
                detected_brand = importers.detect_brand_from_file(df_test) if df_test is not None else None
                if detected_brand is None and df_test is not None:
                    required_fields = ['Модель', 'Шум', 'Холод', 'Тепло', 'Мощность', 'Габариты', 'Цена']
                    try:
                        detected_brand = importers.detect_brand_by_headers(df_test.columns, required_fields)
                    except Exception as e:
                        show_copyable_error(self, "Ошибка определения бренда", str(e))
                        self.go_to_brands_tab()
                        return
                if detected_brand is None:
                    profiles = importers.load_brand_profiles()
                    if profiles.get('brands'):
                        response = messagebox.askyesnocancel(
                            "Бренд не распознан",
                            "Не удалось автоматически определить бренд.\n\n"
                            "Нажмите 'Да', чтобы перейти на вкладку «Профили брендов» и настроить синонимы вручную.\n"
                            "Нажмите 'Нет', чтобы импортировать с глобальными синонимами."
                        )
                        if response is True:
                            self.go_to_brands_tab()
                            return
                        elif response is None:
                            return
                cnt = importers.import_from_file(path)
                self.models = config.load_models()
                self.update_models_view()
                messagebox.showinfo("Импорт завершен", f"Успешно импортировано {cnt} моделей кондиционеров.")
            except Exception as e:
                show_copyable_error(self, "Ошибка импорта", str(e))
                
    def import_pdf_models(self):
        path = filedialog.askopenfilename(filetypes=[("Документы PDF", "*.pdf")])
        if path:
            try:
                cnt = importers.import_from_pdf(path)
                self.models = config.load_models()
                self.update_models_view()
                messagebox.showinfo("Импорт завершен", f"Успешно импортировано {cnt} моделей кондиционеров из PDF-таблиц.")
            except Exception as e:
                show_copyable_error(self, "Ошибка импорта", str(e))

    def load_settings_into_entries(self):
        settings = config.load_settings()
        for key, entry in self.settings_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, settings.get(key, ""))
        self.settings_activity_text.delete("1.0", tk.END)
        self.settings_activity_text.insert("1.0", settings.get("activity", "КОНДИЦИОНЕРЫ\nВЕНТИЛЯЦИЯ\nОТОПЛЕНИЕ"))
        self.logo_path_var.set(settings.get("logo_path", ""))
        self.logo_width_var.set(str(settings.get("logo_width", 3.0)))
        self.color_var.set(settings.get("primary_color", "#00A8C5"))
        self.font_var.set(settings.get("font_family", "Segoe UI"))
        self.update_color_preview()
        
    def save_settings_from_gui(self):
        settings = {}
        for key, entry in self.settings_entries.items():
            settings[key] = entry.get().strip()
        settings["activity"] = self.settings_activity_text.get("1.0", "end-1c").strip()
        settings["logo_path"] = self.logo_path_var.get().strip()
        try:
            settings["logo_width"] = float(self.logo_width_var.get().strip())
        except:
            settings["logo_width"] = 3.0
        settings["primary_color"] = self.color_var.get().strip()
        settings["font_family"] = self.font_var.get().strip()
        
        try:
            config.save_settings(settings)
            messagebox.showinfo("Сохранено", "Настройки организации успешно обновлены.")
        except ValueError as e:
            messagebox.showerror("Ошибка валидации", str(e))
    
    def on_closing(self):
        if hasattr(self, 'brand_profile_frame'):
            self.brand_profile_frame.save_profiles()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()