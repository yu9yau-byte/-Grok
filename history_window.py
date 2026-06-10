# -*- coding: utf-8 -*-
"""
Окно истории коммерческих предложений.
"""
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
import history
import config


class HistoryWindow(ctk.CTkToplevel):
    """Окно управления историей КП."""
    
    def __init__(self, parent, on_load_callback=None):
        super().__init__(parent)
        
        self.title("История коммерческих предложений")
        self.geometry("1100x750")
        self.minsize(1000, 650)
        
        self.transient(parent)
        self.grab_set()
        
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 550
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 375
        self.geometry(f"+{x}+{y}")
        
        self.on_load_callback = on_load_callback
        self.current_filters = {}
        
        self.setup_ui()
        self.load_history()
    
    def setup_ui(self):
        """Настраиваем интерфейс."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Заголовок
        title_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1C222E")
        title_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            title_frame, 
            text="История коммерческих предложений",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00A8C5"
        ).pack(pady=12, padx=15, anchor="w")
        
        # ===== ПАНЕЛЬ ФИЛЬТРОВ =====
        filter_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1C222E")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        filter_inner = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_inner.pack(fill="x", padx=15, pady=10)
        
        # Заголовок фильтров
        ctk.CTkLabel(
            filter_inner,
            text="🔍 Фильтры:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 8))
        
        # Поля фильтров в одну строку
        filters_row = ctk.CTkFrame(filter_inner, fg_color="transparent")
        filters_row.pack(fill="x")
        
        # Дата ОТ
        date_from_frame = ctk.CTkFrame(filters_row, fg_color="transparent")
        date_from_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(date_from_frame, text="От:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w")
        self.date_from_entry = ctk.CTkEntry(date_from_frame, placeholder_text="ДД.ММ.ГГГГ", width=100, fg_color="#141923")
        self.date_from_entry.pack(anchor="w", pady=(2, 0))
        
        # Дата ДО
        date_to_frame = ctk.CTkFrame(filters_row, fg_color="transparent")
        date_to_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(date_to_frame, text="До:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w")
        self.date_to_entry = ctk.CTkEntry(date_to_frame, placeholder_text="ДД.ММ.ГГГГ", width=100, fg_color="#141923")
        self.date_to_entry.pack(anchor="w", pady=(2, 0))
        
        # Клиент
        client_frame = ctk.CTkFrame(filters_row, fg_color="transparent")
        client_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(client_frame, text="Клиент:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w")
        self.client_filter_entry = ctk.CTkEntry(client_frame, placeholder_text="Поиск...", width=150, fg_color="#141923")
        self.client_filter_entry.pack(anchor="w", pady=(2, 0))
        
        # Сумма ОТ
        amount_min_frame = ctk.CTkFrame(filters_row, fg_color="transparent")
        amount_min_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(amount_min_frame, text="Сумма от:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w")
        self.amount_min_entry = ctk.CTkEntry(amount_min_frame, placeholder_text="0", width=80, fg_color="#141923")
        self.amount_min_entry.pack(anchor="w", pady=(2, 0))
        
        # Сумма ДО
        amount_max_frame = ctk.CTkFrame(filters_row, fg_color="transparent")
        amount_max_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(amount_max_frame, text="до:", font=ctk.CTkFont(size=11), text_color="#7C8BA0").pack(anchor="w")
        self.amount_max_entry = ctk.CTkEntry(amount_max_frame, placeholder_text="∞", width=80, fg_color="#141923")
        self.amount_max_entry.pack(anchor="w", pady=(2, 0))
        
        # Кнопки фильтрации
        btn_filter_frame = ctk.CTkFrame(filters_row, fg_color="transparent")
        btn_filter_frame.pack(side="left", padx=(10, 0))
        
        ctk.CTkButton(
            btn_filter_frame,
            text="Применить",
            command=self.apply_filters,
            fg_color="#00A8C5",
            hover_color="#00BCD9",
            height=30,
            width=80
        ).pack(pady=(10, 0))
        
        ctk.CTkButton(
            btn_filter_frame,
            text="Сбросить",
            command=self.clear_filters,
            fg_color="#2C3E50",
            hover_color="#3E5A6F",
            height=30,
            width=80
        ).pack(pady=(10, 0), padx=(5, 0))
        
        # ===== АНАЛИТИКА =====
        analytics_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1C222E")
        analytics_frame.pack(fill="x", pady=(0, 10))
        
        analytics_inner = ctk.CTkFrame(analytics_frame, fg_color="transparent")
        analytics_inner.pack(fill="x", padx=15, pady=10)
        
        # Заголовок аналитики
        ctk.CTkLabel(
            analytics_inner,
            text="📊 Аналитика:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 8))
        
        # Карточки статистики
        stats_frame = ctk.CTkFrame(analytics_inner, fg_color="transparent")
        stats_frame.pack(fill="x")
        
        self.analytics_labels = {}
        
        stats_items = [
            ("total_count", "Найдено КП:", "0"),
            ("total_amount", "На сумму:", "0 ₽"),
            ("unique_clients", "Клиентов:", "0"),
        ]
        
        for i, (key, label, default) in enumerate(stats_items):
            card = ctk.CTkFrame(stats_frame, corner_radius=8, fg_color="#141923")
            card.pack(side="left", fill="x", expand=True, padx=(0, 10) if i < 2 else (0, 0))
            
            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color="#7C8BA0"
            ).pack(pady=(8, 2), padx=8)
            
            value_lbl = ctk.CTkLabel(
                card,
                text=default,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#00A8C5"
            )
            value_lbl.pack(pady=(0, 8), padx=8)
            self.analytics_labels[key] = value_lbl
        
        # ===== СПИСОК КП =====
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)
        
        # Левая панель - список КП
        list_frame = ctk.CTkFrame(content_frame, corner_radius=10, fg_color="#1C222E")
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(list_frame, text="Список предложений", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(12, 5), padx=10, anchor="w")
        
        # Listbox для КП
        listbox_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.proposals_listbox = tk.Listbox(
            listbox_frame,
            bg="#141923",
            fg="white",
            selectbackground="#00A8C5",
            selectforeground="white",
            relief="flat",
            font=("Segoe UI", 11),
            highlightthickness=0
        )
        self.proposals_listbox.pack(fill="both", expand=True)
        self.proposals_listbox.bind("<<ListboxSelect>>", self.on_proposal_select)
        
        # Кнопки действий под списком
        btn_action_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        btn_action_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            btn_action_frame,
            text="Загрузить в КП",
            command=self.load_proposal,
            fg_color="#2C9B7A",
            hover_color="#3DB892",
            height=32
        ).pack(fill="x", pady=(0, 5))
        
        ctk.CTkButton(
            btn_action_frame,
            text="Удалить",
            command=self.delete_proposal,
            fg_color="#8B0000",
            hover_color="#B00000",
            height=32
        ).pack(fill="x")
        
        # Правая панель - детали выбранного КП
        detail_frame = ctk.CTkFrame(content_frame, corner_radius=10, fg_color="#1C222E")
        detail_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        detail_inner = ctk.CTkScrollableFrame(detail_frame, fg_color="transparent")
        detail_inner.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(detail_inner, text="Детали предложения", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 15))
        
        self.detail_labels = {}
        
        detail_fields = [
            ("date", "Дата:"),
            ("client", "Клиент:"),
            ("contact", "Контактное лицо:"),
            ("phone", "Телефон:"),
            ("email", "Email:"),
            ("object", "Объект:"),
            ("variants_count", "Вариантов:"),
            ("amount", "Сумма:"),
        ]
        
        for key, label in detail_fields:
            ctk.CTkLabel(detail_inner, text=label, text_color="#7C8BA0", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(5, 2))
            
            value_lbl = ctk.CTkLabel(
                detail_inner,
                text="-",
                font=ctk.CTkFont(size=12),
                anchor="w",
                justify="left"
            )
            value_lbl.pack(anchor="w", pady=(0, 8))
            self.detail_labels[key] = value_lbl
        
        # Кнопка закрытия
        ctk.CTkButton(
            main_frame,
            text="Закрыть",
            command=self.destroy,
            fg_color="#2C3E50",
            hover_color="#3E5A6F",
            height=35
        ).pack(pady=(10, 0))
    
    def apply_filters(self):
        """Применяет фильтры к списку."""
        filters = {}
        
        # Дата ОТ
        date_from = self.date_from_entry.get().strip()
        if date_from:
            filters['date_from'] = date_from
        
        # Дата ДО
        date_to = self.date_to_entry.get().strip()
        if date_to:
            filters['date_to'] = date_to
        
        # Клиент
        client_name = self.client_filter_entry.get().strip()
        if client_name:
            filters['client_name'] = client_name
        
        # Сумма ОТ
        amount_min = self.amount_min_entry.get().strip()
        if amount_min:
            try:
                filters['amount_min'] = int(amount_min)
            except ValueError:
                messagebox.showwarning("Ошибка", "Минимальная сумма должна быть числом.")
                return
        
        # Сумма ДО
        amount_max = self.amount_max_entry.get().strip()
        if amount_max:
            try:
                filters['amount_max'] = int(amount_max)
            except ValueError:
                messagebox.showwarning("Ошибка", "Максимальная сумма должна быть числом.")
                return
        
        self.current_filters = filters
        self.load_history()
    
    def clear_filters(self):
        """Очищает все фильтры."""
        self.date_from_entry.delete(0, tk.END)
        self.date_to_entry.delete(0, tk.END)
        self.client_filter_entry.delete(0, tk.END)
        self.amount_min_entry.delete(0, tk.END)
        self.amount_max_entry.delete(0, tk.END)
        self.current_filters = {}
        self.load_history()
    
    def load_history(self):
        """Загружает историю и обновляет интерфейс."""
        # Получаем отфильтрованные данные
        if self.current_filters:
            proposals = history.filter_proposals(self.current_filters)
        else:
            proposals = history.load_history()
        
        # Обновляем аналитику
        total_amount = sum(p.get('total_amount', 0) for p in proposals)
        unique_clients = len(set(p.get('client', {}).get('name', '') for p in proposals if p.get('client', {}).get('name')))
        
        self.analytics_labels["total_count"].configure(text=str(len(proposals)))
        self.analytics_labels["total_amount"].configure(text=f"{total_amount:,} ₽".replace(",", " "))
        self.analytics_labels["unique_clients"].configure(text=str(unique_clients))
        
        # Обновляем список КП
        self.proposals_listbox.delete(0, tk.END)
        
        if not proposals:
            self.proposals_listbox.insert(0, "(Нет предложений)")
            return
        
        for proposal in proposals:
            date = proposal.get('created_at', '')[:10]
            client = proposal.get('client', {}).get('name', 'Неизвестно')
            amount = proposal.get('total_amount', 0)
            count = proposal.get('variants_count', 0)
            
            display_text = f"{date} | {client[:25]}{'...' if len(client) > 25 else ''} | {count} шт. | {amount:,} ₽".replace(",", " ")
            self.proposals_listbox.insert(tk.END, display_text)
        
        self.current_proposals = proposals
    
    def on_proposal_select(self, event):
        """Обработчик выбора КП из списка."""
        selection = self.proposals_listbox.curselection()
        if not selection or not hasattr(self, 'current_proposals'):
            return
        
        index = selection[0]
        if index >= len(self.current_proposals):
            return
        
        proposal = self.current_proposals[index]
        client = proposal.get('client', {})
        
        # Обновляем детали
        self.detail_labels["date"].configure(text=proposal.get('created_at', '-'))
        self.detail_labels["client"].configure(text=client.get('name', '-'))
        self.detail_labels["contact"].configure(text=client.get('contact_person', '-'))
        self.detail_labels["phone"].configure(text=client.get('phone', '-'))
        self.detail_labels["email"].configure(text=client.get('email', '-'))
        self.detail_labels["object"].configure(text=client.get('object', '-'))
        self.detail_labels["variants_count"].configure(text=str(proposal.get('variants_count', 0)))
        
        amount = proposal.get('total_amount', 0)
        self.detail_labels["amount"].configure(text=f"{amount:,} ₽".replace(",", " "))
    
    def load_proposal(self):
        """Загружает выбранное КП в основное окно."""
        selection = self.proposals_listbox.curselection()
        if not selection or not hasattr(self, 'current_proposals'):
            messagebox.showwarning("Внимание", "Выберите предложение из списка.")
            return
        
        index = selection[0]
        if index >= len(self.current_proposals):
            return
        
        proposal = self.current_proposals[index]
        
        if self.on_load_callback:
            self.on_load_callback(proposal)
        
        self.destroy()
    
    def delete_proposal(self):
        """Удаляет выбранное КП из истории."""
        selection = self.proposals_listbox.curselection()
        if not selection or not hasattr(self, 'current_proposals'):
            messagebox.showwarning("Внимание", "Выберите предложение из списка.")
            return
        
        index = selection[0]
        if index >= len(self.current_proposals):
            return
        
        proposal = self.current_proposals[index]
        client_name = proposal.get('client', {}).get('name', 'Неизвестно')
        
        if messagebox.askyesno("Удаление", f"Удалить предложение для '{client_name}' из истории?"):
            history.delete_proposal(proposal.get('id'))
            self.load_history()
            messagebox.showinfo("Успех", "Предложение удалено.")


def open_history_window(parent, on_load_callback=None):
    """Открывает окно истории КП."""
    HistoryWindow(parent, on_load_callback)