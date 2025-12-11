import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from logic import Logic


class BudgetApp(tk.Tk):
    """Главное окно приложения Бюджет-трекер"""

    def __init__(self):
        super().__init__()
        self.title("Бюджет-трекер v2.0")
        self.geometry("1100x800")

        # Инициализация бизнес-логики
        self.logic = Logic()

        # Применяем стили
        self._apply_styles()

        # Переменные для фильтрации
        self.date_filter_start = None
        self.date_filter_end = None
        self.filtered_transactions = []
        self.current_transaction_ids = {}

        self._create_widgets()
        self._set_default_date_filter()
        self._load_transactions_to_table()
        self._refresh_savings()

    def _apply_styles(self):
        """Применяем стили для красивого интерфейса"""
        style = ttk.Style()

        # Стиль для Treeview (таблицы)
        style.configure('Treeview', rowheight=25, font=('Arial', 9))
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))

    def _create_widgets(self):
        """Создание всех элементов интерфейса"""

        # Основной контейнер с двумя колонками
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # ЛЕВАЯ КОЛОНКА - Транзакции
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Форма добавления
        form_frame = ttk.LabelFrame(left_frame, text="➕ Добавить транзакцию")
        form_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_frame, text="Тип:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.type_var = tk.StringVar(value="Доход")
        ttk.Combobox(form_frame, textvariable=self.type_var, values=["Доход", "Расход"],
                     state="readonly", width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Сумма:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_var, width=12).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Категория:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.category_var, width=25).grid(row=1, column=1, columnspan=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Дата:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.date_var = tk.StringVar(value=datetime.today().strftime("%d.%m.%y"))
        ttk.Entry(form_frame, textvariable=self.date_var, width=12).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(form_frame, text="Добавить", command=self._on_add).grid(row=2, column=3, padx=10, pady=5)

        # Статус
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(left_frame, textvariable=self.status_var,
                                      foreground="#1565C0", font=('Arial', 10))
        self.status_label.pack(fill="x", padx=5, pady=(0, 5))

        # Фильтр по периоду
        filter_frame = ttk.LabelFrame(left_frame, text="📅 Фильтр по периоду (DD.MM.YY)")
        filter_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(filter_frame, text="С:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.filter_start_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_start_var, width=12).grid(row=0, column=1, padx=5, pady=8)

        ttk.Label(filter_frame, text="По:").grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.filter_end_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_end_var, width=12).grid(row=0, column=3, padx=5, pady=8)

        ttk.Button(filter_frame, text="✅ Применить", command=self._apply_date_filter).grid(row=0, column=4, padx=10, pady=8)
        ttk.Button(filter_frame, text="🔄 Сброс", command=self._reset_date_filter).grid(row=0, column=5, padx=5, pady=8)

        # Таблица транзакций
        table_frame = ttk.Frame(left_frame)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("type", "amount", "category", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)

        for col, text, width, anchor in [
            ("type", "Тип", 70, "center"),
            ("amount", "Сумма", 90, "e"),
            ("category", "Категория", 200, "w"),
            ("date", "Дата", 100, "center")
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Контекстное меню
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="✏️ Редактировать", command=self._on_edit)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Удалить", command=self._on_delete)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Кнопки управления транзакциями
        bottom_frame = ttk.Frame(left_frame)
        bottom_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(bottom_frame, text="📊 Статистика", command=self._on_show_stats).pack(side="left", padx=3)
        ttk.Button(bottom_frame, text="🔄 Обновить", command=self._on_refresh).pack(side="left", padx=3)
        ttk.Button(bottom_frame, text="📈 Диаграмма", command=self.get_statistics).pack(side="left", padx=3)
        ttk.Button(bottom_frame, text="📉 График", command=self.get_info).pack(side="left", padx=3)

        # ПРАВАЯ КОЛОНКА - Копилки
        right_frame = ttk.LabelFrame(main_container, text="🎯 Копилки")
        right_frame.pack(side="right", fill="both", expand=False, padx=(5, 0))
        right_frame.config(width=400)

        # Таблица копилок
        savings_table_frame = ttk.Frame(right_frame)
        savings_table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("name", "current", "target", "progress")
        self.savings_tree = ttk.Treeview(savings_table_frame, columns=columns, show="headings", height=20)

        for col, text, width in [
            ("name", "Название", 150),
            ("current", "Есть", 70),
            ("target", "Цель", 70),
            ("progress", "%", 50)
        ]:
            self.savings_tree.heading(col, text=text)
            self.savings_tree.column(col, width=width, anchor="center" if col != "name" else "w")

        self.savings_tree.pack(side="left", fill="both", expand=True)

        savings_scrollbar = ttk.Scrollbar(savings_table_frame, orient="vertical", command=self.savings_tree.yview)
        self.savings_tree.configure(yscroll=savings_scrollbar.set)
        savings_scrollbar.pack(side="right", fill="y")

        # Кнопки управления копилками
        savings_btn_frame1 = ttk.Frame(right_frame)
        savings_btn_frame1.pack(fill="x", padx=10, pady=5)

        ttk.Button(savings_btn_frame1, text="➕ Создать", command=self._add_goal, width=15).pack(side="left", padx=2)
        ttk.Button(savings_btn_frame1, text="✏️ Изменить", command=self._edit_goal, width=15).pack(side="left", padx=2)

        savings_btn_frame2 = ttk.Frame(right_frame)
        savings_btn_frame2.pack(fill="x", padx=10, pady=5)

        ttk.Button(savings_btn_frame2, text="💰 Пополнить", command=self._deposit_money, width=15).pack(side="left", padx=2)
        ttk.Button(savings_btn_frame2, text="💸 Снять", command=self._withdraw_money, width=15).pack(side="left", padx=2)

        savings_btn_frame3 = ttk.Frame(right_frame)
        savings_btn_frame3.pack(fill="x", padx=10, pady=5)

        ttk.Button(savings_btn_frame3, text="🗑️ Удалить", command=self._delete_goal, width=15).pack(side="left", padx=2)
        ttk.Button(savings_btn_frame3, text="🔄 Обновить", command=self._refresh_savings, width=15).pack(side="left", padx=2)

    def _show_context_menu(self, event):
        """Контекстное меню при правом клике"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _set_default_date_filter(self):
        """Фильтр по умолчанию - последний месяц"""
        end_date = datetime.today()
        start_date = end_date - timedelta(days=30)
        self.date_filter_start = start_date.strftime("%d.%m.%y")
        self.date_filter_end = end_date.strftime("%d.%m.%y")
        self.filter_start_var.set(self.date_filter_start)
        self.filter_end_var.set(self.date_filter_end)

    def _apply_date_filter(self):
        """Применить фильтр"""
        start = self.filter_start_var.get().strip()
        end = self.filter_end_var.get().strip()

        if not start or not end:
            self.status_var.set("Введите обе даты!")
            return

        try:
            datetime.strptime(start, "%d.%m.%y")
            datetime.strptime(end, "%d.%m.%y")
            self.date_filter_start = start
            self.date_filter_end = end
            self._load_transactions_to_table()
            self.status_var.set(f"✅ Фильтр: {start} → {end}")
        except ValueError:
            self.status_var.set("❌ Формат даты: DD.MM.YY")

    def _reset_date_filter(self):
        """Сброс фильтра"""
        self.date_filter_start = None
        self.date_filter_end = None
        self.filter_start_var.set("")
        self.filter_end_var.set("")
        self._load_transactions_to_table()
        self.status_var.set("🔄 Показаны все транзакции")

    def _on_add(self):
        """Добавить транзакцию"""
        self.status_var.set("")
        t_type_ru = self.type_var.get()

        try:
            if t_type_ru == "Доход":
                self.logic.add_income(self.amount_var.get(), self.category_var.get(), self.date_var.get())
            else:
                self.logic.add_expenses(self.amount_var.get(), self.category_var.get(), self.date_var.get())

            self.amount_var.set("")
            self.category_var.set("")
            self._load_transactions_to_table()
            self.status_var.set("✅ Транзакция добавлена")
        except ValueError as e:
            self.status_var.set(f"❌ {str(e)}")
        except Exception as e:
            self.status_var.set(f"❌ Ошибка: {e}")

    def _load_transactions_to_table(self):
        """Загрузка с фильтрацией и цветным выделением"""
        self.logic.load_transactions()

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.current_transaction_ids.clear()

        # Получаем все транзакции из БД с ID
        all_db_transactions = self.logic.db.get_all_transactions()

        if self.date_filter_start and self.date_filter_end:
            # Фильтруем с сохранением ID
            filtered_with_ids = []
            for row in all_db_transactions:
                id_, amount, category, date, t_type = row
                if self.date_filter_start <= date <= self.date_filter_end:
                    filtered_with_ids.append(row)
        else:
            filtered_with_ids = all_db_transactions

        # Заполняем таблицу с цветами
        for row in filtered_with_ids:
            id_, amount, category, date, t_type = row
            display_type = "Доход" if t_type == "income" else "Расход"

            # ЦВЕТНОЕ ВЫДЕЛЕНИЕ
            tag = "income" if t_type == "income" else "expense"
            item_id = self.tree.insert("", "end",
                                       values=(display_type, f"{amount:.2f}", category, date),
                                       tags=(tag,))
            # Сохраняем РЕАЛЬНЫЙ ID из БД
            self.current_transaction_ids[item_id] = id_

        # Настраиваем цвета
        self.tree.tag_configure("income", foreground="#2E7D32")  # Зеленый для доходов
        self.tree.tag_configure("expense", foreground="#C62828")  # Красный для расходов

    def _on_refresh(self):
        self._load_transactions_to_table()
        self.status_var.set("🔄 Список обновлён")

    def _get_selected_transaction_id(self):
        """Получить реальный ID выбранной транзакции из БД"""
        selected = self.tree.selection()
        if not selected:
            return None
        item_id = selected[0]
        return self.current_transaction_ids.get(item_id)

    def _on_edit(self):
        """Редактировать транзакцию"""
        transaction_id = self._get_selected_transaction_id()
        if transaction_id is None:
            self.status_var.set("❌ Выберите транзакцию")
            return

        # Получаем данные транзакции из БД по реальному ID
        transaction = self.logic.get_transaction_by_id(transaction_id)
        if not transaction:
            self.status_var.set("❌ Транзакция не найдена")
            return

        # transaction = (id, amount, category, date, type)
        id_, amount, category, date, t_type = transaction

        dialog = EditTransactionDialog(self, (t_type, amount, category, date))
        self.wait_window(dialog)

        if dialog.result:
            try:
                self.logic.edit_transaction(
                    transaction_id,
                    dialog.result['type'],
                    dialog.result['amount'],
                    dialog.result['category'],
                    dialog.result['date']
                )
                self._load_transactions_to_table()
                self.status_var.set("✅ Транзакция обновлена")
            except Exception as e:
                self.status_var.set(f"❌ Ошибка: {e}")

    def _on_delete(self):
        """Удалить транзакцию"""
        transaction_id = self._get_selected_transaction_id()
        if transaction_id is None:
            self.status_var.set("❌ Выберите транзакцию")
            return

        if messagebox.askyesno("Подтверждение", "Удалить транзакцию?"):
            try:
                self.logic.delete_transaction_by_id(transaction_id)
                self._load_transactions_to_table()
                self.status_var.set("✅ Транзакция удалена")
            except Exception as e:
                self.status_var.set(f"❌ Ошибка: {e}")

    def _on_show_stats(self):
        """Статистика с балансом копилок"""
        if self.date_filter_start and self.date_filter_end:
            income, expense, balance = self.logic.summarize_transactions_by_range(
                self.date_filter_start, self.date_filter_end
            )
            period = f"\n(период: {self.date_filter_start} - {self.date_filter_end})"
        else:
            income, expense, balance = self.logic.summarize_transactions()
            period = ""

        # Считаем баланс копилок
        goals = self.logic.savings_db.get_goal()
        total_savings = sum(current for _, _, _, current in goals)
        savings_count = len(goals)

        messagebox.showinfo("📊 Статистика",
                            f"💰 Доход: {income:.2f}₽\n"
                            f"💸 Расходы: {expense:.2f}₽\n"
                            f"💳 Баланс: {balance:.2f}₽{period}\n"
                            f"\n"
                            f"🎯 Копилок: {savings_count}\n"
                            f"💎 В копилках: {total_savings:.2f}₽")

    def pie_chart(self, categories_dict, title="Расходы по категориям"):
        if not categories_dict or categories_dict == "Расходов нет":
            messagebox.showinfo("Статистика", "Нет расходов для отображения")
            return

        fig, ax = plt.subplots(figsize=(7, 6))
        ax.pie(categories_dict.values(), labels=categories_dict.keys(), autopct='%1.1f%%', startangle=90)
        ax.axis("equal")
        ax.set_title(title)

        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("600x500")

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def get_statistics(self):
        if self.date_filter_start and self.date_filter_end:
            categories = self.logic.get_expenses_by_category_range(self.date_filter_start, self.date_filter_end)
            title = f"Расходы ({self.date_filter_start} - {self.date_filter_end})"
        else:
            categories = self.logic.get_expenses_by_category()
            title = "Расходы по категориям"

        self.pie_chart(categories, title)

    def graph(self, dates_list, title="Баланс по дням"):
        if not dates_list or dates_list == "Нет данных":
            messagebox.showinfo("График", "Нет данных")
            return

        dates = [d for d, b in dates_list]
        balances = [b for d, b in dates_list]

        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("800x500")

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(dates, balances, marker='o', linewidth=2, markersize=6)
        ax.set_title(title)
        ax.set_xlabel("Дата")
        ax.set_ylabel("Баланс, ₽")
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def get_info(self):
        if self.date_filter_start and self.date_filter_end:
            daily = self.logic.get_balance_by_date_range(self.date_filter_start, self.date_filter_end)
            title = f"Баланс ({self.date_filter_start} - {self.date_filter_end})"
        else:
            daily = self.logic.get_balance_by_date()
            title = "Баланс по дням"

        self.graph(daily, title)

    # ========== МЕТОДЫ ДЛЯ КОПИЛОК ==========

    def _refresh_savings(self):
        """Обновить список копилок с цветным прогрессом"""
        for item in self.savings_tree.get_children():
            self.savings_tree.delete(item)

        goals = self.logic.savings_db.get_goal()
        for goal in goals:
            id_, name, target, current = goal
            progress = self.logic.calculate_progress(goal)

            # Определяем тег для цвета
            if progress >= 100:
                tag = "complete"
            elif progress >= 75:
                tag = "high"
            elif progress >= 50:
                tag = "medium"
            elif progress >= 25:
                tag = "low"
            else:
                tag = "verylow"

            self.savings_tree.insert("", "end", values=(
                name,
                f"{current:.0f}",
                f"{target:.0f}",
                f"{progress:.0f}%"
            ), tags=(str(id_), tag))

        # Настраиваем цвета прогресса
        self.savings_tree.tag_configure("complete", foreground="#1B5E20")  # Темно-зеленый (100%)
        self.savings_tree.tag_configure("high", foreground="#388E3C")      # Зеленый (75%+)
        self.savings_tree.tag_configure("medium", foreground="#F57C00")    # Оранжевый (50%+)
        self.savings_tree.tag_configure("low", foreground="#E64A19")       # Красно-оранжевый (25%+)
        self.savings_tree.tag_configure("verylow", foreground="#C62828")   # Красный (<25%)

    def _add_goal(self):
        """Создать новую копилку"""
        dialog = AddGoalDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            try:
                name = dialog.result['name']
                target = float(dialog.result['target'])
                self.logic.savings_db.add_goal(name, target, 0)
                self._refresh_savings()
                self.status_var.set(f"✅ Копилка '{name}' создана")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать копилку: {e}")

    def _edit_goal(self):
        """Редактировать копилку"""
        selected = self.savings_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите копилку")
            return

        goal_id = int(self.savings_tree.item(selected[0])['tags'][0])
        goal = self.logic._find_goal_row(goal_id)
        id_, old_name, target, current = goal

        dialog = EditGoalDialog(self, old_name, target)
        self.wait_window(dialog)

        if dialog.result:
            try:
                new_name = dialog.result['name']
                new_target = float(dialog.result['target'])

                self.logic.update_goal_name_everywhere(goal_id, old_name, new_name, new_target, current)
                self._refresh_savings()
                self.status_var.set(f"✅ Копилка обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")

    def _delete_goal(self):
        """Удалить копилку"""
        selected = self.savings_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите копилку")
            return

        goal_id = int(self.savings_tree.item(selected[0])['tags'][0])
        goal = self.logic._find_goal_row(goal_id)
        _, name, _, current = goal

        msg = f"Удалить копилку '{name}'?"
        if current > 0:
            msg += f"\n\nВ копилке {current:.2f}₽"

        if not messagebox.askyesno("Подтверждение", msg):
            return

        try:
            self.logic.delete_goal_with_transactions(goal_id)
            self._refresh_savings()
            self.status_var.set(f"✅ Копилка '{name}' удалена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    def _deposit_money(self):
        """Внести деньги в копилку"""
        selected = self.savings_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите копилку")
            return

        goal_id = int(self.savings_tree.item(selected[0])['tags'][0])
        goal = self.logic._find_goal_row(goal_id)
        _, name, _, _ = goal

        amount = simpledialog.askfloat("Пополнить копилку",
                                       f"Сколько внести в '{name}'?",
                                       parent=self,
                                       minvalue=0.01)
        if amount:
            try:
                self.logic.deposit_to_goal(goal_id, amount)
                self._refresh_savings()
                self.status_var.set(f"✅ Внесено {amount:.2f}₽ в '{name}'")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _withdraw_money(self):
        """Снять деньги из копилки"""
        selected = self.savings_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите копилку")
            return

        goal_id = int(self.savings_tree.item(selected[0])['tags'][0])
        goal = self.logic._find_goal_row(goal_id)
        _, name, _, current = goal

        if current <= 0:
            messagebox.showinfo("Информация", f"В копилке '{name}' нет денег")
            return

        amount = simpledialog.askfloat("Снять деньги",
                                       f"Сколько снять из '{name}'?\nДоступно: {current:.2f}₽",
                                       parent=self,
                                       minvalue=0.01,
                                       maxvalue=current)
        if amount:
            try:
                self.logic.withdraw_from_goal(goal_id, amount)
                self._refresh_savings()
                self.status_var.set(f"✅ Снято {amount:.2f}₽ из '{name}'")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))


class EditTransactionDialog(tk.Toplevel):
    def __init__(self, parent, transaction):
        super().__init__(parent)
        self.title("✏️ Редактировать транзакцию")
        self.geometry("450x350")
        self.transient(parent)
        self.grab_set()

        self.result = None

        # transaction = (t_type, amount, category, date)
        self.t_type, self.amount, self.category, self.date = transaction

        ttk.Label(self, text="Тип:", font=('Arial', 10)).pack(pady=5)
        self.type_var = tk.StringVar(value="Доход" if self.t_type == "income" else "Расход")
        ttk.Combobox(self, textvariable=self.type_var, values=["Доход", "Расход"], state="readonly", width=15).pack(pady=5)

        ttk.Label(self, text="Сумма:", font=('Arial', 10)).pack(pady=5)
        self.amount_var = tk.StringVar(value=str(self.amount))
        ttk.Entry(self, textvariable=self.amount_var, width=20, font=('Arial', 11)).pack(pady=5)

        ttk.Label(self, text="Категория:", font=('Arial', 10)).pack(pady=5)
        self.category_var = tk.StringVar(value=self.category)
        ttk.Entry(self, textvariable=self.category_var, width=30, font=('Arial', 11)).pack(pady=5)

        ttk.Label(self, text="Дата (DD.MM.YY):", font=('Arial', 10)).pack(pady=5)
        self.date_var = tk.StringVar(value=self.date)
        ttk.Entry(self, textvariable=self.date_var, width=20, font=('Arial', 11)).pack(pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="💾 Сохранить", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="❌ Отмена", command=self.destroy).pack(side="left", padx=10)

    def _save(self):
        t_type_en = "income" if self.type_var.get() == "Доход" else "expense"
        self.result = {
            'type': t_type_en,
            'amount': self.amount_var.get(),
            'category': self.category_var.get(),
            'date': self.date_var.get()
        }
        self.destroy()


class AddGoalDialog(tk.Toplevel):
    """Диалог создания новой копилки"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("➕ Создать копилку")
        self.geometry("400x250")
        self.transient(parent)
        self.grab_set()

        self.result = None

        ttk.Label(self, text="Название цели:", font=('Arial', 10)).pack(pady=10)
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, width=30, font=('Arial', 11)).pack(pady=5)

        ttk.Label(self, text="Целевая сумма (₽):", font=('Arial', 10)).pack(pady=10)
        self.target_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.target_var, width=20, font=('Arial', 11)).pack(pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="✅ Создать", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="❌ Отмена", command=self.destroy).pack(side="left", padx=10)

    def _save(self):
        name = self.name_var.get().strip()
        target = self.target_var.get().strip()

        if not name:
            messagebox.showwarning("Предупреждение", "Введите название")
            return

        if not target:
            messagebox.showwarning("Предупреждение", "Введите целевую сумму")
            return

        try:
            target_float = float(target)
            if target_float <= 0:
                messagebox.showwarning("Предупреждение", "Сумма должна быть больше 0")
                return
        except ValueError:
            messagebox.showwarning("Предупреждение", "Введите корректную сумму")
            return

        self.result = {'name': name, 'target': target}
        self.destroy()


class EditGoalDialog(tk.Toplevel):
    """Диалог редактирования копилки"""

    def __init__(self, parent, name, target):
        super().__init__(parent)
        self.title("✏️ Редактировать копилку")
        self.geometry("400x250")
        self.transient(parent)
        self.grab_set()

        self.result = None

        ttk.Label(self, text="Название цели:", font=('Arial', 10)).pack(pady=10)
        self.name_var = tk.StringVar(value=name)
        ttk.Entry(self, textvariable=self.name_var, width=30, font=('Arial', 11)).pack(pady=5)

        ttk.Label(self, text="Целевая сумма (₽):", font=('Arial', 10)).pack(pady=10)
        self.target_var = tk.StringVar(value=str(target))
        ttk.Entry(self, textvariable=self.target_var, width=20, font=('Arial', 11)).pack(pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="💾 Сохранить", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="❌ Отмена", command=self.destroy).pack(side="left", padx=10)

    def _save(self):
        name = self.name_var.get().strip()
        target = self.target_var.get().strip()

        if not name:
            messagebox.showwarning("Предупреждение", "Введите название")
            return

        if not target:
            messagebox.showwarning("Предупреждение", "Введите целевую сумму")
            return

        try:
            target_float = float(target)
            if target_float <= 0:
                messagebox.showwarning("Предупреждение", "Сумма должна быть больше 0")
                return
        except ValueError:
            messagebox.showwarning("Предупреждение", "Введите корректную сумму")
            return

        self.result = {'name': name, 'target': target}
        self.destroy()


if __name__ == "__main__":
    app = BudgetApp()
    app.mainloop()
