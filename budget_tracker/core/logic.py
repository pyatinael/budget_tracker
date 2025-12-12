import sqlite3
from datetime import datetime
from budget_tracker.core.database import DataBase, DataBaseForSavings


class Logic:
    def __init__(self, db_path="transactions.db", savings_db_path="savings.db"):
        """
        Инициализирует основной класс логики приложения.

        Создаёт базы данных, загружает транзакции
        и рассчитывает стартовый баланс.

        :param db_path: Путь к базе данных транзакций
        :type db_path: str
        :param savings_db_path: Путь к базе данных копилок
        :type savings_db_path: str
        :returns: None
        :rtype: NoneType
        """
        self.db = DataBase(db_path)
        self.db.create_db()

        self.transactions = []
        self.load_transactions()

        self.savings_db = DataBaseForSavings(savings_db_path)
        self.savings_db.create_db()

        self.balance = 0
        self._update_balance()

    # ---------- проверки ----------

    def date_validation(self, date_str):
        """
        Проверяет корректность даты в формате ``"%d.%m.%y"``.

        :param date_str: Дата в формате "dd.mm.yy"
        :type date_str: str
        :raises ValueError: Если дата имеет неверный формат
        """
        try:
            datetime.strptime(date_str, "%d.%m.%y")
        except ValueError:
            raise ValueError("Неправильная дата. Нужен формат '%d.%m.%y'")

    def amount_validation(self, summ):
        """
        Проверяет корректность суммы.

        :param summ: Значение суммы
        :type summ: int or float or str
        :returns: Корректная сумма
        :rtype: float
        :raises ValueError:
            Если сумма не является числом;
            Если сумма меньше или равна нулю.
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
        Проверяет корректность категории.

        :param category: Название категории
        :type category: str
        :returns: Нормализованная категория
        :rtype: str
        :raises ValueError:
            Если категория не строка;
            Если длина превышает 50 символов.
        """
        if not isinstance(category, str):
            raise ValueError("Категория должна быть строкой")

        category = category.strip()

        if len(category) > 50:
            raise ValueError("Категория должна быть длиной до 50 символов")

        return category

    def type_validation(self, t_type):
        """
        Проверяет корректность типа транзакции.

        :param t_type: Тип транзакции
        :type t_type: str
        :returns: Тип транзакции
        :rtype: str
        :raises ValueError: Если тип некорректен
        """
        if t_type not in ("income", "expense"):
            raise ValueError("Тип транзакции должен быть 'income' или 'expense'")
        return t_type

    # ---------- служебное ----------

    def _update_balance(self):
        """
        Пересчитывает текущий баланс.

        :returns: None
        :rtype: NoneType
        """
        _, _, balance = self.summarize_transactions()
        self.balance = balance

    def _find_goal_row(self, goal_id):
        """
        Ищет копилку по её идентификатору.

        :param goal_id: Идентификатор цели
        :type goal_id: int
        :returns: Кортеж цели
        :rtype: tuple
        :raises ValueError: Если цель не найдена
        """
        goals = self.savings_db.get_goal()
        for row in goals:
            if row[0] == goal_id:
                return row
        raise ValueError(f"Цель с ID {goal_id} не найдена")

    # ---------- транзакции ----------

    def add_transaction(self, t_type, summ, category, date):
        """
        Добавляет новую транзакцию.

        :param t_type: Тип транзакции
        :type t_type: str
        :param summ: Сумма
        :type summ: int or float or str
        :param category: Категория
        :type category: str
        :param date: Дата
        :type date: str
        """
        t_type = self.type_validation(t_type)
        summ = self.amount_validation(summ)
        category = self.category_validation(category)
        self.date_validation(date)

        self.db.add_transaction(summ, category, date, t_type)
        self.transactions.append((t_type, summ, category, date))
        self._update_balance()

    def add_income(self, summ, category, date):
        """Добавляет доход."""
        self.add_transaction("income", summ, category, date)

    def add_expenses(self, summ, category, date):
        """Добавляет расход."""
        self.add_transaction("expense", summ, category, date)

    def load_transactions(self):
        """
        Загружает все транзакции из базы данных.

        :returns: None
        :rtype: NoneType
        """
        rows = self.db.get_all_transactions()
        self.transactions = []

        for row in rows:
            _, amount, category, date, t_type = row
            self.transactions.append((t_type, float(amount), category, date))


    def summarize_transactions(self):
        """
        Подсчитывает доходы, расходы и баланс.

        :returns: income, expense, balance
        :rtype: tuple
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
        Группирует расходы по категориям.

        :returns: Словарь или строка
        :rtype: dict or str
        """
        result = {}

        for t_type, amount, category, _ in self.transactions:
            if t_type != "expense":
                continue

            result[category] = result.get(category, 0.0) + amount

        if not result:
            return "Расходов нет"

        return result

    def get_balance_by_date(self):
        """
        Строит историю баланса по датам.

        :returns: Список (date, balance) или строка
        :rtype: list or str
        """
        daily = {}

        for t_type, amount, _, date in self.transactions:
            if date not in daily:
                daily[date] = 0.0

            if t_type == "income":
                daily[date] += amount
            else:
                daily[date] -= amount

        if not daily:
            return "Нет данных"

        dates = sorted(
            daily.keys(),
            key=lambda d: datetime.strptime(d, "%d.%m.%y")
        )

        result = []
        balance = 0.0

        for d in dates:
            balance += daily[d]
            result.append((d, balance))

        return result


    def translate_type(self, t_type):
        """
        Переводит тип транзакции на русский язык.

        :param t_type: тип транзакции (``"income"`` или ``"expense"``).
        :type t_type: str
        :returns: строковое представление типа.
        :rtype: str
    """
        if t_type == "income":
            return "Доход"
        if t_type == "expense":
            return "Расход"
        return t_type

    def delete_transaction(self, trans_id):
        """
        Удаляет транзакцию по её идентификатору.

        Это алиас метода :meth:`delete_transaction_by_id`.

        :param trans_id: идентификатор транзакции.
        :type trans_id: int
        :returns: None
        :rtype: NoneType
        """
        return self.delete_transaction_by_id(trans_id)


    # ---------- копилки ----------

    def calculate_progress(self, goal):
        """
        Вычисляет процент выполнения цели.

        :param goal: Кортеж цели
        :type goal: tuple
        :returns: Процент выполнения
        :rtype: float
        """
        _, _, target_amount, current_amount = goal

        if target_amount <= 0:
            return 0.0

        return min((current_amount / target_amount) * 100, 100.0)

    def deposit_to_goal(self, goal_id, amount):
        """
        Переводит указанную сумму в выбранную копилку.

        Метод уменьшает общий баланс, увеличивает накопление цели
        и записывает операцию как расход с текущей датой.

        :param goal_id: идентификатор цели, в которую вносятся средства.
        :type goal_id: int
        :param amount: сумма пополнения копилки.
        :type amount: int | float | str

        :returns: None
        :rtype: NoneType

        :raises ValueError:
            если сумма некорректна;
            если цель с указанным ``goal_id`` не найдена.
        """

        amount = self.amount_validation(amount)
        goal = self._find_goal_row(goal_id)

        id_, name, target_amount, current_amount = goal
        new_current = current_amount + amount

        self.savings_db.update_goal_amount(id_, name, target_amount, new_current)

        today = datetime.now().strftime("%d.%m.%y")
        self.add_expenses(amount, f"Копилка: {name[:35]}", today)

    def withdraw_from_goal(self, goal_id, amount):
        """
        Извлекает указанную сумму из копилки и добавляет её в общий баланс.

        Метод уменьшает накопление цели и записывает операцию
        как доход с текущей датой.

        :param goal_id: идентификатор цели, из которой извлекаются средства.
        :type goal_id: int
        :param amount: сумма вывода из копилки.
        :type amount: int | float | str

        :returns: None
        :rtype: NoneType

        :raises ValueError:
            если сумма некорректна;
            если цель с указанным ``goal_id`` не найдена;
            если в копилке недостаточно средств.
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

        today = datetime.now().strftime("%d.%m.%y")
        self.add_income(amount, f"Из копилки: {name[:36]}", today)

    # ---------- фильтрация ----------

    def filter_transactions_by_date_range(self, start_date, end_date):
        """
        Фильтрует транзакции по заданному диапазону дат (включительно).

        Метод возвращает только те транзакции, дата которых
        находится между ``start_date`` и ``end_date``.

        :param start_date: дата начала диапазона в формате ``"dd.mm.yy"``.
        :type start_date: str
        :param end_date: дата конца диапазона в формате ``"dd.mm.yy"``.
        :type end_date: str

        :returns: список транзакций вида ``(type, amount, category, date)``.
        :rtype: list[tuple[str, float, str, str]]
        """

        try:
            start = datetime.strptime(start_date, "%d.%m.%y")
            end = datetime.strptime(end_date, "%d.%m.%y")
        except ValueError:
            return []

        result = []

        for t_type, amount, category, date in self.transactions:
            try:
                current = datetime.strptime(date, "%d.%m.%y")
                if start <= current <= end:
                    result.append((t_type, amount, category, date))
            except ValueError:
                continue

        return result

    def summarize_transactions_by_range(self, start_date, end_date):
        """
        Подсчитывает доходы, расходы и баланс за указанный период.

        :param start_date: дата начала периода в формате ``"dd.mm.yy"``.
        :type start_date: str
        :param end_date: дата конца периода в формате ``"dd.mm.yy"``.
        :type end_date: str

        :returns: кортеж ``(income, expense, balance)`` за период.
        :rtype: tuple[float, float, float]
        """

        filtered = self.filter_transactions_by_date_range(start_date, end_date)

        income = 0
        expense = 0

        for t_type, amount, _, _ in filtered:
            if t_type == "income":
                income += amount
            else:
                expense += amount

        return income, expense, income - expense

    def get_balance_by_date_range(self, start_date, end_date):
        """
        Строит историю изменения накопленного баланса за период.

        Баланс считается последовательно по датам
        в хронологическом порядке.

        :param start_date: дата начала периода в формате ``"dd.mm.yy"``.
        :type start_date: str
        :param end_date: дата конца периода в формате ``"dd.mm.yy"``.
        :type end_date: str

        :returns:
            список кортежей ``(date, balance)``;
            либо строку ``"Нет данных"``, если транзакций нет.
        :rtype: list[tuple[str, float]] | str
        """
        filtered = self.filter_transactions_by_date_range(start_date, end_date)

        daily = {}

        for t_type, amount, _, date in filtered:
            daily.setdefault(date, 0.0)
            daily[date] += amount if t_type == "income" else -amount

        if not daily:
            return "Нет данных"

        result = []
        balance = 0.0

        dates = sorted(daily.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%y"))

        for d in dates:
            balance += daily[d]
            result.append((d, balance))

        return result

    def get_expenses_by_category_range(self, start_date, end_date):
        """
        Группирует расходы по категориям за указанный период.

        :param start_date: дата начала периода в формате ``"dd.mm.yy"``.
        :type start_date: str
        :param end_date: дата конца периода в формате ``"dd.mm.yy"``.
        :type end_date: str

        :returns:
            словарь формата ``{category: total_expense}``;
            либо строку ``"Расходов нет"``, если расходов нет.
        :rtype: dict[str, float] | str
        """

        filtered = self.filter_transactions_by_date_range(start_date, end_date)
        result = {}

        for t_type, amount, category, _ in filtered:
            if t_type == "expense":
                result[category] = result.get(category, 0.0) + amount

        if not result:
            return "Расходов нет"

        return result

    def get_transaction_by_id(self, transaction_id):
        """
        Возвращает транзакцию по её идентификатору.

        :param transaction_id: идентификатор транзакции.
        :type transaction_id: int

        :returns: строку транзакции из базы данных или ``None``.
        :rtype: tuple | None
        """
        try:
            return self.db.get_transaction(transaction_id)
        except Exception:
            return None

    def delete_transaction_by_id(self, transaction_id):
        """
        Удаляет транзакцию по её идентификатору.

        После удаления обновляет список транзакций
        и пересчитывает баланс.

        :param transaction_id: идентификатор транзакции.
        :type transaction_id: int

        :returns: None
        :rtype: NoneType

        :raises ValueError: если произошла ошибка при удалении транзакции.
        """
        try:
            self.db.delete_transaction(transaction_id)
            self.load_transactions()
            self._update_balance()
        except Exception as e:
            raise ValueError(f"Ошибка удаления транзакции: {e}")

    def edit_transaction(self, transaction_id, t_type, summ, category, date):
        """
        Редактирует существующую транзакцию.

        Перед обновлением выполняется валидация
        типа, суммы, категории и даты.

        :param transaction_id: идентификатор транзакции.
        :type transaction_id: int
        :param t_type: тип транзакции (``"income"`` или ``"expense"``).
        :type t_type: str
        :param summ: сумма транзакции.
        :type summ: int | float | str
        :param category: категория транзакции.
        :type category: str
        :param date: дата транзакции в формате ``"dd.mm.yy"``.
        :type date: str

        :returns: None
        :rtype: NoneType

        :raises ValueError: если редактирование завершилось ошибкой.
        """
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

    def update_goal_info(self, goal_id, new_name, new_target, current_amount):
        """
        Обновляет название, целевую сумму и текущее накопление копилки.

        :param goal_id: идентификатор цели.
        :type goal_id: int
        :param new_name: новое название цели.
        :type new_name: str
        :param new_target: новая целевая сумма.
        :type new_target: float
        :param current_amount: текущее накопление.
        :type current_amount: float

        :returns: None
        :rtype: NoneType
        """
        self.savings_db.update_goal_amount(goal_id, new_name, new_target, current_amount)


    def delete_goal_with_transactions(self, goal_id):
        """
        Удаляет копилку по её идентификатору.

        :param goal_id: идентификатор цели.
        :type goal_id: int

        :returns: None
        :rtype: NoneType

        :raises ValueError: если произошла ошибка при удалении копилки.
        """

        try:
            self.savings_db.delete_goal(goal_id)
        except Exception as e:
            raise ValueError(f"Ошибка удаления копилки: {e}")