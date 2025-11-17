from datetime import datetime

class Logic:
    def __init__(self):
        # список транзакций хранится в виде кортежей:
        # (type, amount, category, date)
        self.transactions = []

    def date_validation(self, date_str):
        """
        Проверяем, записана ли дата в формате "YYYY-MM-DD".
        Если формат неверный — возбуждаем ValueError.
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Неправильная дата")

    def add_income(self, summ, category, date):
        """
        Добавляем доход.
        summ — сумма
        category — категория
        date — дата
        """
        self.date_validation(date)
        self.transactions.append(("income", summ, category, date))

    def add_expenses(self, summ, category, date):
        """
        Добавляем расход.
        """
        self.date_validation(date)
        self.transactions.append(("expense", summ, category, date))

    def summarize_transactions(self):
        """
        Возвращает:
        (общий доход, общие расходы, итоговый баланс)
        """
        income = 0
        expense = 0

        for t, a, _, _ in self.transactions:
            if t == "income":
                income += a
            else:
                expense += a

        return income, expense, income - expense