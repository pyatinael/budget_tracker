from datetime import datetime
from database import DataBase


class Logic:
    def __init__(self, db_path="transactions.db"):
        """
        список транзакций хранится в виде кортежей:
        (type, amount, category, date)
        """
        self.db = DataBase(db_path)
        self.db.create_db()
        self.transactions = []
        self.load_transactions()

    def date_validation(self, date_str):
        """
        Проверяем, записана ли дата в формате 'YYYY-MM-DD'.
        Если формат неверный, то возвращаеи ValueError.
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Неправильная дата. Нужен формат YYYY-MM-DD")

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
        - строка длиной от 15 до 20 символов
        """
        if not isinstance(category, str):
            raise ValueError("Категория должна быть строкой")

        category = category.strip()

        if len(category) > 20:
            raise ValueError("Категория должна быть длиной от 15 до 20 символов")

        return category

    def type_validation(self, t_type):
        """
        Проверяем тип транзакции.
        Можно только 'income' или 'expense'.
        """
        if t_type not in ("income", "expense"):
            raise ValueError("Тип транзакции должен быть 'income' или 'expense'")
        return t_type

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

    def add_income(self, summ, category, date):
        """
        Добавляем доход.
        """
        self.add_transaction("income", summ, category, date)

    def add_expenses(self, summ, category, date):
        """
        Добавляем расход.
        """
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
        Возвращает общий доход, общие расходы, итоговый баланс
        """
        income = 0
        expense = 0

        for t, a, _, _ in self.transactions:
            if t == "income":
                income += a
            else:
                expense += a

        return income, expense, income - expense