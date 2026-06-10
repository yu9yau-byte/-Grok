# -*- coding: utf-8 -*-
"""
Окно редактирования списка клиентов.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import config


class ClientEditorWindow(ctk.CTkToplevel):
    """Окно управления списком клиентов."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Управление клиентами")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        self.transient(parent)
        self.grab_set()
        
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 450
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 300
        self.geometry(f"+{x}+{y}")
        
        self.selected_client_id = None
        
        self.setup_ui()
        self.load_clients()
    
    def setup_ui(self):
        """Настраиваем интерфейс."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Заголовок
        title_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1C222E")
        title_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            title_frame, 
            text="Управление клиентами",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00A8C5"
        ).pack(pady=12, padx=15, anchor="w")
        
        # Две колонки
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=2)
        content_frame.columnconfigure(1, weight=3)
        
        # ===== ЛЕВАЯ ПАНЕЛЬ - СПИСОК КЛИЕНТОВ =====
        list_frame = ctk.CTkFrame(content_frame, corner_radius=10, fg_color="#1C222E")
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(list_frame, text="Список клиентов", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(12, 5), padx=10, anchor="w")
        
        # Listbox
        listbox_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.client_listbox = tk.Listbox(
            listbox_frame,
            bg="#141923",
            fg="white",
            selectbackground="#00A8C5",
            selectforeground="white",
            relief="flat",
            font=("Segoe UI", 11),
            highlightthickness=0
        )
        self.client_listbox.pack(fill="both", expand=True)
        self.client_listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        
        # Кнопка удаления
        btn_delete_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        btn_delete_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            btn_delete_frame,
            text="Удалить выбранного",
            command=self.delete_selected_client,
            fg_color="#8B0000",
            hover_color="#B00000",
            height=30
        ).pack(fill="x")
        
        # ===== ПРАВАЯ ПАНЕЛЬ - ФОРМА =====
        form_frame = ctk.CTkFrame(content_frame, corner_radius=10, fg_color="#1C222E")
        form_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Заголовок формы
        ctk.CTkLabel(form_frame, text="Данные клиента", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(12, 10), padx=15, anchor="w")
        
        # Поля ввода (прокручиваемая область)
        self.fields = {}
        
        form_scroll = ctk.CTkScrollableFrame(form_frame, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=15)
        
        # Все поля - CTkEntry
        field_configs = [
            ("name", "Организация / Заказчик *"),
            ("contact_person", "Контактное лицо"),
            ("phone", "Телефон"),
            ("email", "Email"),
            # ("address", "Адрес"),  - убран, обрабатывается как Text виджет
            ("object_name", "Объект / Проект"),
        ]
        
        for key, label in field_configs:
            ctk.CTkLabel(form_scroll, text=label, text_color="#7C8BA0", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(8, 2))
            
            entry = ctk.CTkEntry(form_scroll, fg_color="#141923", text_color="white")
            entry.pack(fill="x", pady=(0, 5))
            self.fields[key] = entry
        
        # Адрес - многострочное поле с переносом
        ctk.CTkLabel(form_scroll, text="Адрес", text_color="#7C8BA0", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(8, 2))
        
        address_container = ctk.CTkFrame(form_scroll, fg_color="#141923", corner_radius=6, border_width=0)
        address_container.pack(fill="x", pady=(0, 5), ipady=3)
        
        self.address_text = tk.Text(
            address_container,
            bg="#141923",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 11),
            wrap="word",
            height=3,
            padx=8,
            pady=8
        )
        self.address_text.pack(side="left", fill="x", expand=True)
        
        address_scroll = tk.Scrollbar(address_container, command=self.address_text.yview, orient="vertical")
        address_scroll.pack(side="right", fill="y")
        self.address_text.config(yscrollcommand=address_scroll.set)
        
        self.fields["address"] = self.address_text
        
        # Заметки - многострочное поле с прокруткой
        ctk.CTkLabel(form_scroll, text="Заметки", text_color="#7C8BA0", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(8, 2))
        
        notes_container = ctk.CTkFrame(form_scroll, fg_color="#141923", corner_radius=6, border_width=0)
        notes_container.pack(fill="x", pady=(0, 5), ipady=3)
        
        self.notes_text = tk.Text(
            notes_container,
            bg="#141923",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 11),
            wrap="word",
            height=4,
            padx=8,
            pady=8
        )
        self.notes_text.pack(side="left", fill="x", expand=True)
        
        notes_scroll = tk.Scrollbar(notes_container, command=self.notes_text.yview, orient="vertical")
        notes_scroll.pack(side="right", fill="y")
        self.notes_text.config(yscrollcommand=notes_scroll.set)
        
        self.fields["notes"] = self.notes_text
        
        # ===== КНОПКИ СОХРАНИТЬ/ОЧИСТИТЬ - ВНЕ ПРОКРУТКИ =====
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=15)
        
        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=self.save_client,
            fg_color="#2C9B7A",
            hover_color="#3DB892",
            font=ctk.CTkFont(weight="bold"),
            height=40
        )
        self.btn_save.pack(fill="x", pady=(0, 8))
        
        self.btn_clear = ctk.CTkButton(
            btn_frame,
            text="Очистить (новый клиент)",
            command=self.clear_form,
            fg_color="#2C3E50",
            hover_color="#3E5A6F",
            height=35
        )
        self.btn_clear.pack(fill="x")
        
        # Кнопка закрытия
        ctk.CTkButton(
            main_frame,
            text="Закрыть",
            command=self.destroy,
            fg_color="#2C3E50",
            hover_color="#3E5A6F",
            height=35
        ).pack(pady=(15, 0))
    
    def load_clients(self):
        """Загружает список клиентов."""
        self.client_listbox.delete(0, tk.END)
        
        clients = config.load_clients()
        
        if not clients:
            self.client_listbox.insert(0, "(Нет клиентов)")
            return
        
        for client in clients:
            name = client.get('name', 'Без названия')
            phone = client.get('phone', '')
            if phone:
                display_text = f"{name} | {phone}"
            else:
                display_text = name
            self.client_listbox.insert(tk.END, display_text)
    
    def on_listbox_select(self, event):
        """Обработчик выбора клиента из списка."""
        selection = self.client_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        clients = config.load_clients()
        
        if index >= len(clients):
            return
        
        client = clients[index]
        self.selected_client_id = client.get('id')
        
        # Заполняем поля
        for key, entry in self.fields.items():
            value = str(client.get(key, '') or '')
            if key in ("notes", "address"):
                # Для текстовых виджетов используем другой метод
                entry.delete("1.0", tk.END)
                entry.insert("1.0", value)
            else:
                entry.delete(0, tk.END)
                entry.insert(0, value)
    
    def get_form_data(self):
        """Получает данные из формы."""
        data = {}
        for key, entry in self.fields.items():
            if key in ("notes", "address"):
                # Получаем текст из виджета Text
                value = entry.get("1.0", "end-1c").strip()
                data[key] = value
            else:
                value = entry.get().strip()
                data[key] = value
        return data
    
    def clear_form(self):
        """Очищает форму."""
        self.selected_client_id = None
        self.client_listbox.selection_clear(0, tk.END)
        for key, entry in self.fields.items():
            if key in ("notes", "address"):
                entry.delete("1.0", tk.END)
            else:
                entry.delete(0, tk.END)
    
    def save_client(self):
        """Сохраняет клиента."""
        data = self.get_form_data()
        
        if not data.get('name'):
            messagebox.showwarning("Ошибка", "Поле 'Организация / Заказчик' обязательно!")
            return
        
        if self.selected_client_id:
            # Обновляем существующего
            success = config.update_client(self.selected_client_id, data)
            if success:
                messagebox.showinfo("Успех", "Клиент обновлён!")
                self.load_clients()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить клиента.")
        else:
            # Добавляем нового
            new_id = config.add_client(data)
            self.selected_client_id = new_id
            messagebox.showinfo("Успех", "Клиент добавлен!")
            self.load_clients()
    
    def delete_selected_client(self):
        """Удаляет выбранного клиента."""
        selection = self.client_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите клиента из списка, кликнув по нему.")
            return
        
        index = selection[0]
        clients = config.load_clients()
        
        if index >= len(clients):
            messagebox.showwarning("Внимание", "Невозможно определить клиента.")
            return
        
        client = clients[index]
        client_id = client.get('id')
        client_name = client.get('name', 'Без названия')
        
        if messagebox.askyesno("Удаление", f"Удалить клиента '{client_name}'?"):
            try:
                config.delete_client(client_id)
                self.clear_form()
                self.load_clients()
                messagebox.showinfo("Успех", "Клиент удалён.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить клиента:\n{str(e)}")


def open_client_editor(parent):
    """Открывает окно редактирования клиентов."""
    ClientEditorWindow(parent)