import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from logic import Logic


class BudgetApp(tk.Tk):
    """Главное окно приложения Бюджет-трекер"""

    def __init__(self):
        super().__init__()
        self.title("Бюджет-трекер")
        self.geometry("800x500")

        # Инициализация бизнес-логики (работа с БД и валидация)
        self.logic = Logic()
        if hasattr(self.logic, "init"):
            self.logic.init()

        self._create_widgets()
        self._load_transactions_to_table()

    def _create_widgets(self):
        """Создание всех элементов интерфейса"""

        # Форма для ввода новой транзакции
        form_frame = ttk.LabelFrame(self, text="Добавление транзакции")
        form_frame.pack(fill="x", padx=10, pady=10)

        # Тип транзакции (доход/расход)
        ttk.Label(form_frame, text="Тип:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.type_var = tk.StringVar(value="Доход")
        ttk.Combobox(form_frame, textvariable=self.type_var, values=["Доход", "Расход"],
                     state="readonly", width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Сумма транзакции
        ttk.Label(form_frame, text="Сумма:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_var, width=12).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Категория (15-20 символов согласно требованиям Logic)
        ttk.Label(form_frame, text="Категория (15–20 символов):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.category_var, width=30).grid(row=1, column=1, columnspan=3, padx=5,
                                                                             pady=5, sticky="w")

        # Дата в формате YYYY-MM-DD (по умолчанию - сегодня)
        ttk.Label(form_frame, text="Дата (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        ttk.Entry(form_frame, textvariable=self.date_var, width=15).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(form_frame, text="Добавить", command=self._on_add).grid(row=2, column=3, padx=5, pady=5, sticky="e")

        # Строка статуса для вывода ошибок и уведомлений
        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, foreground="red").pack(fill="x", padx=10, pady=(0, 5))

        # Таблица для отображения всех транзакций
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("type", "amount", "category", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

        # Настройка колонок таблицы (название, ширина, выравнивание)
        for col, text, width, anchor in [
            ("type", "Тип", 80, "center"),
            ("amount", "Сумма", 100, "e"),
            ("category", "Категория", 300, "w"),
            ("date", "Дата", 120, "center")
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.pack(side="left", fill="both", expand=True)

        # Вертикальная прокрутка для таблицы
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Панель с кнопками управления
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(bottom_frame, text="Показать статистику", command=self._on_show_stats).pack(side="left")
        ttk.Button(bottom_frame, text="Обновить список", command=self._on_refresh).pack(side="left", padx=5)

    def _on_add(self):
        """Обработка добавления новой транзакции"""
        self.status_var.set("")
        t_type, amount, category, date_str = (
            self.type_var.get(),
            self.amount_var.get(),
            self.category_var.get(),
            self.date_var.get()
        )

        try:
            # Добавление через Logic (там происходит валидация)
            if t_type == "Доход":
                self.logic.add_income(amount, category, date_str)
            else:
                self.logic.add_expenses(amount, category, date_str)

            # Очистка полей после успешного добавления
            self.amount_var.set("")
            self.category_var.set("")

            # Обновление таблицы и вывод уведомления
            self._load_transactions_to_table()
            self.status_var.set("Транзакция добавлена")

        except ValueError as e:
            # Ошибка валидации (неверный формат данных)
            self.status_var.set(str(e))
        except Exception as e:
            # Любая другая ошибка
            self.status_var.set(f"Ошибка: {e}")

    def _load_transactions_to_table(self):
        """Загрузка всех транзакций из БД в таблицу"""
        self.logic.load_transactions()

        # Очистка текущего содержимого таблицы
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Заполнение таблицы данными из logic.transactions
        for t_type, amount, category, date_str in self.logic.transactions:
            self.tree.insert("", "end", values=(t_type, amount, category, date_str))

    def _on_refresh(self):
        """Обновление списка транзакций из БД"""
        self._load_transactions_to_table()
        self.status_var.set("Список обновлён")

    def _on_show_stats(self):
        """Показ окна со статистикой (доходы, расходы, баланс)"""
        income, expense, balance = self.logic.summarize_transactions()
        messagebox.showinfo(
            "Статистика",
            f"Общий доход: {income:.2f}\n"
            f"Общие расходы: {expense:.2f}\n"
            f"Баланс: {balance:.2f}"
        )


if __name__ == "__main__":
    app = BudgetApp()
    app.mainloop()
