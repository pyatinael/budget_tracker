import sqlite3
from datetime import datetime
from .database import DataBase, DataBaseForSavings


class Logic:
    def __init__(self, db_path="transactions.db", savings_db_path="savings.db"):
        """
        Инициализирует основной класс логики приложения.

        Создаёт две базы данных:
        — базу транзакций;
        — базу целей (копилок).

        Загружает существующие транзакции, создаёт структуры хранения
        и рассчитывает стартовый баланс.

        :param db_path: путь к файлу базы данных с транзакциями.
        :type db_path: str
        :param savings_db_path: путь к файлу базы данных с целями.
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

    def date_validation(self, date_str):
        """
        Проверяет корректность даты в формате ``"%d.%m.%y"``.

        :param date_str: строка с датой.
        :type date_str: str

        :returns: None, если дата корректна.
        :rtype: NoneType

        :raises ValueError: если дата имеет неверный формат или не существует.
        """
        try:
            datetime.strptime(date_str, "%d.%m.%y")
        except ValueError:
            raise ValueError("Неправильная дата. Нужен формат '%d.%m.%y'")

    def amount_validation(self, summ):
        """
        Проверяет корректность суммы и преобразует её к числу с плавающей точкой.

        :param summ: значение, представляющее сумму. Может быть числом или строкой.
        :type summ: any

        :returns: корректная сумма в виде числа с плавающей точкой.
        :rtype: float

        :raises ValueError:
            если значение нельзя преобразовать в число;
            если сумма меньше или равна нулю.
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
        Проверяет корректность категории и возвращает её нормализованное значение.

        :param category: строка с названием категории.
        :type category: str

        :returns: категорию без лишних пробелов по краям.
        :rtype: str

        :raises ValueError:
            если ``category`` не является строкой;
            если длина категории после обрезки пробелов превышает 50 символов.
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

        :param t_type: тип транзакции. Допустимые значения: ``"income"`` или ``"expense"``.
        :type t_type: str

        :returns: тот же тип транзакции, если он корректен.
        :rtype: str

        :raises ValueError: если ``t_type`` не равен ``"income"`` или ``"expense"``.
        """
        if t_type not in ("income", "expense"):
            raise ValueError("Тип транзакции должен быть 'income' или 'expense'")
        return t_type

    # ---------- служебное ----------

    def _update_balance(self):
        """
        Пересчитывает текущий баланс на основе всех загруженных транзакций.

        :returns: None
        :rtype: NoneType
        """
        _, _, balance = self.summarize_transactions()
        self.balance = balance

    def _find_goal_row(self, goal_id):
        """
        Ищет цель по её идентификатору среди всех сохранённых целей.

        :param goal_id: идентификатор цели, которую требуется найти.
        :type goal_id: int

        :returns: кортеж вида ``(id, name, target_amount, current_amount)``.
        :rtype: tuple

        :raises ValueError:
            если цель с указанным ``goal_id`` не найдена.
        """
        goals = self.savings_db.get_goal()
        for row in goals:
            if row[0] == goal_id:
                return row
        raise ValueError(f"Цель с ID {goal_id} не найдена")

    # ---------- работа с транзакциями ----------

    def add_transaction(self, t_type, summ, category, date):
        """
        Добавляет новую транзакцию в систему и сохраняет её в базе данных.

        Метод универсален, через него проходят как доходы,
        так и расходы. Перед добавлением выполняется полная валидация всех
        переданных данных.

        :param t_type: тип транзакции. Допустимые значения: ``"income"`` или ``"expense"``.
        :type t_type: str

        :param summ: сумма транзакции. Может быть числом или строкой, но должна
            представлять собой положительное число.
        :type summ: float | int | str

        :param category: категория транзакции (краткое текстовое описание).
        :type category: str

        :param date: дата транзакции в формате ``"dd.mm.yy"``.
        :type date: str

        :returns: None
        :rtype: NoneType

        :raises ValueError:
            если тип транзакции некорректен;
            если сумма не является числом или меньше либо равна нулю;
            если категория некорректна или превышает допустимую длину;
            если дата имеет неправильный формат или не существует.

        """
        t_type = self.type_validation(t_type)
        summ = self.amount_validation(summ)
        category = self.category_validation(category)
        self.date_validation(date)
        self.db.add_transaction(summ, category, date, t_type)
        self.transactions.append((t_type, summ, category, date))
        self._update_balance()

    def add_income(self, summ, category, date):
        """
        Добавляет новую транзакцию типа ``income``.

        :param summ: сумма дохода.
        :type summ: float | int | str
        :param category: категория дохода.
        :type category: str
        :param date: дата в формате ``"dd.mm.yy"``.
        :type date: str
        """
        self.add_transaction("income", summ, category, date)

    def add_expenses(self, summ, category, date):
        """
        Добавляет новую транзакцию типа ``expense``.

        :param summ: сумма расхода.
        :type summ: float | int | str
        :param category: категория расхода.
        :type category: str
        :param date: дата в формате ``"dd.mm.yy"``.
        :type date: str
        """
        self.add_transaction("expense", summ, category, date)

    def load_transactions(self):
        """
        Загружает все транзакции из базы данных в память.

        Метод получает список строк из таблицы ``transactions`` и пересобирает
        атрибут ``self.transactions`` в список кортежей вида:
        ``(type, amount, category, date)``.

        :returns: None
        :rtype: NoneType

        :raises Exception: ошибки, возникающие при обращении к базе данных.
        """
        all_rows = self.db.get_all_transactions()
        self.transactions = []

        for row in all_rows:
            id_, amount, category, date, t_type = row
            self.transactions.append((t_type, amount, category, date))

    def summarize_transactions(self):
        """
        Подсчитывает суммарный доход, расход и текущий баланс на основе
        всех загруженных транзакций.

        :returns: кортеж из трёх чисел:
            - ``income`` — общая сумма доходов;
            - ``expense`` — общая сумма расходов;
            - ``balance`` — разница между доходами и расходами.
        :rtype: tuple[float, float, float]
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
        Группирует расходы по категориям и подсчитывает итоговые суммы.

        Метод перебирает все транзакции в ``self.transactions`` и выбирает только
        те, у которых тип равен ``"expense"``. Для каждой категории вычисляется
        суммарный расход.

        :returns:
            - словарь формата ``{category: total_expense}``, если расходы найдены;
            - строку ``"Расходов нет"``, если расходов нет вовсе.
        :rtype: dict[str, float] | str
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
        Строит историю изменения баланса по датам.

        Метод агрегирует все транзакции по датам, вычисляет ежедневный
        доход/убыль и формирует список накопленного баланса в
        хронологическом порядке.

        :returns:
            - список кортежей ``(date, balance)`` — баланс на каждую дату;
            - строку ``"Нет данных"``, если транзакций нет.
        :rtype: list[tuple[str, float]] | str
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

        dates = sorted(daily.keys())

        result = []
        balance = 0.0

        for d in dates:
            balance += daily[d]
            result.append((d, balance))

        return result

    def translate_type(self, t_type):
        """
        Преобразует внутренний тип транзакции в человекочитаемый формат.

        :param t_type: тип транзакции (``"income"`` или ``"expense"``).
        :type t_type: str

        :returns:
            - ``"Доход"``, если тип равен ``"income"``;
            - ``"Расход"``, если тип равен ``"expense"``;
            - исходное значение ``t_type`` во всех остальных случаях.
        :rtype: str
        """
        if t_type == "income":
            return "Доход"
        elif t_type == "expense":
            return "Расход"
        return t_type

    def delete_transaction(self, trans_id):
        """
        Удаляет транзакцию по её идентификатору.

        Метод передаёт указанный ``trans_id`` в объект базы данных и пытается
        удалить соответствующую запись. Если база данных сообщает об ошибке
        (например, транзакции с таким идентификатором нет), генерируется
        ``ValueError``. После успешного удаления метод обновляет локальный список
        транзакций и пересчитывает текущий баланс.

        :param trans_id: идентификатор транзакции.
        :type trans_id: int

        :returns: None
        :rtype: NoneType

        :raises ValueError: если транзакция с указанным идентификатором не найдена.
        """
        # пробуем удалить в базе
        try:
            self.db.delete_transaction(trans_id)
        except Exception:
            raise ValueError(f"Транзакция с id {trans_id} не найдена")

        # перезагружаем список
        self.load_transactions()

        # пересчёт баланса
        self._update_balance()
        
    # ---------- цели (накопления) ----------

    def calculate_progress(self, goal):
        """
        Вычисляет процент выполнения указанной цели.

        Процент рассчитывается как ``(current_amount / target_amount) * 100``.
        Итоговое значение ограничено сверху значением ``100.0``.

        :param goal: кортеж вида ``(id, name, target_amount, current_amount)``.
        :type goal: tuple

        :returns: процент выполнения цели в диапазоне от ``0.0`` до ``100.0``.
        :rtype: float
        """
        _, _, target_amount, current_amount = goal

        if target_amount <= 0:
            return 0.0

        progress = (current_amount / target_amount) * 100
        # На всякий случай не даём вылезти за 100%
        return min(progress, 100.0)

    def deposit_to_goal(self, goal_id, amount):
        """
        Переводит указанную сумму из общего баланса в цель (копилку).

        Сначала сумма проходит проверку через ``amount_validation``. Затем метод
        находит цель по идентификатору, увеличивает её текущее накопление и
        записывает расход в таблицу транзакций с текущей датой.

        :param goal_id: идентификатор цели, в которую вносятся средства.
        :type goal_id: int
        :param amount: сумма пополнения. Должна корректно преобразовываться
            в положительное число.
        :type amount: float | int | str

        :returns: None
        :rtype: NoneType

        :raises ValueError:
            если сумма некорректна;
            если цель с указанным ``goal_id`` не найдена.
        """
        amount = self.amount_validation(amount)

        # находим цель
        goal = self._find_goal_row(goal_id)
        id_, name, target_amount, current_amount = goal

        # обновляем накопление в таблице savings
        new_current = current_amount + amount
        self.savings_db.update_goal_amount(id_, name, target_amount, new_current)

        # пишем расход в обычную таблицу transactions
        today = datetime.now().strftime("%d.%m.%y")
        category = f"Копилка: {name[:35]}"  
        self.add_expenses(amount, category, today)
        # баланс пересчитается внутри add_expenses

        

    def withdraw_from_goal(self, goal_id, amount):
        """
        Извлекает указанную сумму из цели (копилки) и добавляет её
        в общий баланс как доход.

        Сначала сумма проходит проверку через ``amount_validation``.
        Затем метод находит цель по идентификатору и проверяет, достаточно ли
        в ней средств. Если средств достаточно, накопление уменьшается, а в
        таблицу транзакций добавляется доходная запись с текущей датой.

        :param goal_id: идентификатор цели, из которой выводятся средства.
        :type goal_id: int

        :param amount: сумма вывода. Должна корректно преобразовываться
            в положительное число.
        :type amount: float | int | str

        :returns: None
        :rtype: NoneType

        :raises ValueError:
            если сумма некорректна;
            если цель с указанным ``goal_id`` не найдена;
            если доступных накоплений меньше требуемой суммы.
        """
        amount = self.amount_validation(amount)

        goal = self._find_goal_row(goal_id)
        id_, name, target_amount, current_amount = goal

        if current_amount < amount:
            raise ValueError(
                f"В цели '{name}' недостаточно средств (сейчас {current_amount})"
            )

        # уменьшаем накопление
        new_current = current_amount - amount
        self.savings_db.update_goal_amount(id_, name, target_amount, new_current)

        # закидываем доход на счёт
        today = datetime.now().strftime("%d.%m.%y")
        category = f"Из копилки: {name[:36]}"
        self.add_income(amount, category, today)

