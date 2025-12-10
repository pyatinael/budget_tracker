import sqlite3
from datetime import datetime
from database import DataBase, DataBaseForSavings


class Logic:
    def __init__(self, db_path="transactions.db", savings_db_path="savings.db"):
        """
        список транзакций хранится в виде кортежей:
        (type, amount, category, date)
        """
        # основная БД с транзакциями
        self.db = DataBase(db_path)
        self.db.create_db()
        self.transactions = []
        self.load_transactions()

        # БД с целями (копилки)
        self.savings_db = DataBaseForSavings(savings_db_path)
        self.savings_db.create_db()

        # баланс на старте
        self.balance = 0
        self._update_balance()

    # ---------- проверки ----------
    def date_validation(self, date_str):
        """
        Проверяем, записана ли дата в формате "%d.%m.%y".
        Если формат неверный, то возвращаем ValueError.
        """
        try:
            datetime.strptime(date_str, "%d.%m.%y")
        except ValueError:
            raise ValueError("Неправильная дата. Нужен формат '%d.%m.%y'")

    def amount_validation(self, summ):
        """
        Проверяем сумму:
        - должна быть числом больше 0
        """
        try:
            summ = float(summ)
        except (TypeError, ValueError):
            raise ValueError("Сумма должна быть числом")
        if summ <= 0:
            raise ValueError("Сумма должна быть больше 0")
        return summ

    def category_validation(self, category):
        """
        Проверяем категорию:
        - строка, не длиннее 50 символов (было 20)
        """
        if not isinstance(category, str):
            raise ValueError("Категория должна быть строкой")
        category = category.strip()
        if len(category) > 50:
            raise ValueError("Категория должна быть длиной до 50 символов")
        return category

    def type_validation(self, t_type):
        """
        Проверяем тип транзакции.
        Можно только 'income' или 'expense'.
        """
        if t_type not in ("income", "expense"):
            raise ValueError("Тип транзакции должен быть 'income' или 'expense'")
        return t_type

    # ---------- служебное ----------
    def _update_balance(self):
        """Пересчитываем баланс из транзакций."""
        _, _, balance = self.summarize_transactions()
        self.balance = balance

    def _find_goal_row(self, goal_id):
        """
        Ищем цель по id среди всех целей.
        Строка имеет вид: (id, name, target_amount, current_amount)
        """
        goals = self.savings_db.get_goal()
        for row in goals:
            if row[0] == goal_id:
                return row
        raise ValueError(f"Цель с ID {goal_id} не найдена")

    # ---------- работа с транзакциями ----------
    def add_transaction(self, t_type, summ, category, date):
        """
        Универсальный метод добавления транзакции.
        Через него проходят все добавления (и доходы, и расходы).
        """
        t_type = self.type_validation(t_type)
        summ = self.amount_validation(summ)
        category = self.category_validation(category)
        self.date_validation(date)
        self.db.add_transaction(summ, category, date, t_type)
        self.transactions.append((t_type, summ, category, date))
        # обновляем баланс после каждой операции
        self._update_balance()

    def add_income(self, summ, category, date):
        """Добавляем доход."""
        self.add_transaction("income", summ, category, date)

    def add_expenses(self, summ, category, date):
        """Добавляем расход."""
        self.add_transaction("expense", summ, category, date)

    def load_transactions(self):
        """
        Загружаем транзакции из базы данных.
        В базе строка имеет вид:
        (id, amount, category, date, type)
        В списке храним:
        (type, amount, category, date)
        """
        all_rows = self.db.get_all_transactions()
        self.transactions = []
        for row in all_rows:
            id_, amount, category, date, t_type = row
            self.transactions.append((t_type, amount, category, date))

    def summarize_transactions(self):
        """
        Возвращает общий доход, общие расходы, итоговый баланс.
        """
        income = 0
        expense = 0
        for t, a, _, _ in self.transactions:
            if t == "income":
                income += a
            else:
                expense += a
        return income, expense, income - expense

    def get_expenses_by_category(self):
        """
        Возвращает словарь: категория -> сумма расходов.
        Если расходов нет, возвращает строку "Расходов нет".
        """
        result = {}
        for t_type, amount, category, date in self.transactions:
            if t_type != "expense":
                continue
            if category not in result:
                result[category] = 0.0
            result[category] += amount
        if not result:
            return "Расходов нет"
        return result

    def get_balance_by_date(self):
        """
        Список (дата, накопленный баланс).
        """
        daily = {}
        for t_type, amount, category, date in self.transactions:
            if date not in daily:
                daily[date] = 0.0
            if t_type == "income":
                daily[date] += amount
            else:
                daily[date] -= amount

        if not daily:
            return "Нет данных"

        dates = sorted(daily.keys())
        result = []
        balance = 0.0
        for d in dates:
            balance += daily[d]
            result.append((d, balance))
        return result

    def translate_type(self, t_type):
        if t_type == "income":
            return "Доход"
        elif t_type == "expense":
            return "Расход"
        return t_type

    # ---------- цели (накопления) ----------
    def calculate_progress(self, goal):
        """
        goal — кортеж (id, name, target_amount, current_amount).
        Возвращает процент выполнения цели.
        """
        _, _, target_amount, current_amount = goal
        if target_amount <= 0:
            return 0.0
        progress = (current_amount / target_amount) * 100
        # На всякий случай не даём вылезти за 100%
        return min(progress, 100.0)

    def deposit_to_goal(self, goal_id, amount):
        """
        Добавляем деньги к цели (БЕЗ создания транзакции).
        """
        amount = self.amount_validation(amount)
        goal = self._find_goal_row(goal_id)
        id_, name, target_amount, current_amount = goal

        new_current = current_amount + amount
        self.savings_db.update_goal_amount(id_, name, target_amount, new_current)

    def withdraw_from_goal(self, goal_id, amount):
        """
        Забираем деньги из цели (БЕЗ создания транзакции).
        """
        amount = self.amount_validation(amount)
        goal = self._find_goal_row(goal_id)
        id_, name, target_amount, current_amount = goal

        if current_amount < amount:
            raise ValueError(
                f"В цели '{name}' недостаточно средств (сейчас {current_amount})"
            )

        new_current = current_amount - amount
        self.savings_db.update_goal_amount(id_, name, target_amount, new_current)

    def delete_goal_with_transactions(self, goal_id):
        """Удаляет копилку"""
        self.savings_db.delete_goal(goal_id)

    def update_goal_name_everywhere(self, goal_id, old_name, new_name, target_amount, current_amount):
        """Обновляет название и цель копилки"""
        self.savings_db.update_goal_amount(goal_id, new_name, target_amount, current_amount)

    # ---------- НОВЫЕ МЕТОДЫ ДЛЯ GUI ----------
    def get_transaction_by_id(self, transaction_id):
        """Возвращает транзакцию по ID для редактирования"""
        try:
            row = self.db.get_transaction(transaction_id)
            if row:
                return row  # (id, amount, category, date, type)
            return None
        except:
            return None

    def delete_transaction_by_id(self, transaction_id):
        """Удаляет транзакцию по ID и обновляет данные"""
        try:
            self.db.delete_transaction(transaction_id)
            self.load_transactions()
            self._update_balance()
        except Exception as e:
            raise ValueError(f"Ошибка удаления: {e}")

    def edit_transaction(self, transaction_id, t_type, summ, category, date):
        """Редактирует транзакцию по ID"""
        try:
            t_type = self.type_validation(t_type)
            summ = self.amount_validation(summ)
            category = self.category_validation(category)
            self.date_validation(date)

            self.db.update_transaction(transaction_id, summ, category, date, t_type)
            self.load_transactions()
            self._update_balance()
        except Exception as e:
            raise ValueError(f"Ошибка редактирования: {e}")

    def filter_transactions_by_date_range(self, start_date, end_date):
        """Фильтрует транзакции между start_date и end_date (DD.MM.YY)"""
        filtered = []
        for t_type, amount, category, date in self.transactions:
            if start_date <= date <= end_date:
                filtered.append((t_type, amount, category, date))
        return filtered

    def summarize_transactions_by_range(self, start_date, end_date):
        """Доход, расход, баланс за период"""
        filtered = self.filter_transactions_by_date_range(start_date, end_date)
        income, expense = 0, 0
        for t_type, amount, _, _ in filtered:
            if t_type == "income":
                income += amount
            else:
                expense += amount
        return income, expense, income - expense

    def get_balance_by_date_range(self, start_date, end_date):
        """График баланса за период"""
        filtered = self.filter_transactions_by_date_range(start_date, end_date)
        daily = {}
        for t_type, amount, _, date in filtered:
            if date not in daily:
                daily[date] = 0.0
            if t_type == "income":
                daily[date] += amount
            else:
                daily[date] -= amount

        if not daily:
            return "Нет данных"

        dates = sorted(daily.keys())
        result = []
        balance = 0.0
        for d in dates:
            balance += daily[d]
            result.append((d, balance))
        return result

    def get_expenses_by_category_range(self, start_date, end_date):
        """Расходы по категориям за период"""
        filtered = self.filter_transactions_by_date_range(start_date, end_date)
        result = {}
        for t_type, amount, category, _ in filtered:
            if t_type == "expense":
                if category not in result:
                    result[category] = 0.0
                result[category] += amount

        if not result:
            return "Расходов нет"
        return result
