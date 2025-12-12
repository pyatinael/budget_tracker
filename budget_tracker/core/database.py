# Импортируем необходимую библиотеку sqlite3 для работы с базой данных
import sqlite3

class DataBase:

    """ 
        Класс для работы с базой данных SQLite, содержащий таблицу transactions
        path: str путь к файлу базы данных SQLite
    """

    def __init__(self, path):
        """ 
            Конструктор класса 
            path: str путь к файлу базы данных SQLite
        """
        self.path = path

    def create_db(self):
        """ 
            Метод, отвечающий за создание таблицы transactions, при условии: что она еще не создана

            В таблице есть поля:
            id: INTEGER PRIMARY KEY, AUTOINCREMENT,
            amount: REAL,
            category: TEXT,
            date: TEXT,
            type: TEXT

            Метод автоматически открывает и закрывает соединение
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                query = """
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount REAL,
                        category TEXT,
                        date TEXT,
                        type TEXT
                    )
                """          
                cursor.execute(query)
                db.commit()
        except sqlite3.Error as error:
            print("Ошибка при создании таблицы",error)
        except OSError as error:
            print("Ошибка файлов", error)  

    def add_transaction(self, amount, category, date, type_):
        """ 
            Добавляет новую запись в таблицу transactions

            amount: float сумма транзакции
            category: str категория, например, "food", "transport"
            date: str дата в формате DD.MM.YYYY
            type: str тип транзакции "доход", "расход"
             
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                query = """
                    INSERT INTO transactions (amount, category, date, type)
                    VALUES (?, ?, ?, ?)
                """
                cursor.execute(query, (amount, category, date, type_))
                db.commit()
        except sqlite3.Error as error:
            print("Ошибка при при попытке добавления транзакции:",error)
        except OSError as error:
            print("Ошибка файлов", error)

    def get_all_transactions(self):
        """
            Возвращает список всех транзакций(список кортежей, кортеж - строка таблицы) из таблицы transactions
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM transactions")
                return cursor.fetchall()
        except sqlite3.Error as error:
            print("Ошибка при попытке прочтения транзакций:",error)
        except OSError as error:
            print("Ошибка файлов", error)
        
    def get_transaction(self,id):
        """
            Возвращает одну транзакцию по ее ID (кортеж со значениями полей одной транзакции или None, если запись не найдена)

            id : int идентификатор записи
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                cursor.execute(""" SELECT * FROM transactions WHERE id=? """, (id,))
                return cursor.fetchone()
        except sqlite3.Error as error:
            print("Ошибка при попытке прочтения транзакции:",error)
        except OSError as error:
            print("Ошибка файлов", error)
        
    def delete_transaction(self,id):
        """
            Удаляет транзакцию по её ID

            id : int идентификатор записи, которую нужно удалить
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                cursor.execute(""" DELETE FROM transactions WHERE id=?""",(id,))
                db.commit()
        except sqlite3.Error as error:
            print("Ошибка при попытке удалить транзакцию",error)
        except OSError as error:
            print("Ошибка файлов", error)
    
    def update_transaction(self, id, amount, category, date, type_):
        """
            Обновляет существующую транзакцию

            id : int идентификатор записи, которую нужно обновить
            amount : float новая сумма транзакции
            category : str новая категория
            date : str новая дата в формате DD.MM.YYYY
            type_ : str новый тип транзакции "доход", "расход"

        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                query = """ UPDATE transactions SET amount=?, category=?, date=?, type=? WHERE id=? """
                cursor.execute(query, (amount, category, date, type_, id ))
                db.commit()
        except sqlite3.Error as error:
            print("Ошибка при попытке обновить таблицу с транзакциями",error)
        except OSError as error:
            print("Ошибка файлов", error)


class DataBaseForSavings:
    """ 
        Класс для работы с базой данных SQLite, содержащий таблицу savings
        path: str путь к файлу базы данных SQLite
    """
    def __init__(self, path):
        """ 
            Конструктор класса 
            path: str путь к файлу базы данных SQLite
        """
        self.path = path

    def create_db(self):
        """ 
            Метод, отвечающий за создание таблицы savings, при условии: что она еще не создана

            В таблице есть поля:
            id: INTEGER PRIMARY KEY, AUTOINCREMENT,
            name: TEXT,
            target_amount: REAL,
            current_amount: REAL

            Метод автоматически открывает и закрывает соединение
        """
        with sqlite3.connect(self.path) as db:
            cursor = db.cursor()
            query = """
                CREATE TABLE IF NOT EXISTS savings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    target_amount REAL,
                    current_amount REAL
                )
            """          
            cursor.execute(query)
            db.commit()

    def add_goal(self, name, target_amount, current_amount):
        """ 
            Добавляет новую запись в таблицу savings

            name: str название цели
            target_amount: float сколько нужно накопить
            current_amount: float сколько накоплено
           
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                query = """
                    INSERT INTO savings (name, target_amount, current_amount)
                    VALUES (?, ?, ?)
                """
                cursor.execute(query, (name, target_amount, current_amount))
                db.commit()
        except sqlite3.Error as error:
            print("Ошибка при попытке добавления новой цели или суммы в существующую цель",error)
        except OSError as error:
            print("Ошибка файлов", error)

    def get_goal(self):
        """
            Возвращает список всех целей (список кортежей, кортеж - строка таблицы) из таблицы savings
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM savings")
                return cursor.fetchall()
        except sqlite3.Error as error:
            print("Ошибка при попытке получения списка целей",error)
        except OSError as error:
            print("Ошибка файлов", error)
        
    def delete_goal(self,id):
        """
            Удаляет цель по её ID

            id : int идентификатор записи, которую нужно удалить
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                cursor.execute(""" DELETE FROM savings WHERE id=?""",(id,))
                db.commit()
        except sqlite3.Error as error:
            print("Ошибка при попытке удаления цели",error)
        except OSError as error:
            print("Ошибка файлов", error)
    
    def update_goal_amount(self, id, name, target_amount, current_amount):
        """
        Обновляет данные цели (копилки) в базе данных.

        :param id: идентификатор цели, которую нужно обновить.
        :type id: int
        :param name: новое название цели.
        :type name: str
        :param target_amount: требуемая сумма для достижения цели.
        :type target_amount: float
        :param current_amount: текущая накопленная сумма.
        :type current_amount: float

        :returns: None
        :rtype: NoneType

        :raises sqlite3.Error: при ошибках выполнения SQL-запроса.
        :raises OSError: при ошибках, связанных с файловой системой.
        """
        try:
            with sqlite3.connect(self.path) as db:
                cursor = db.cursor()
                query = """ UPDATE savings SET name=?, target_amount=?, current_amount=? WHERE id=? """
                cursor.execute(query, (name, target_amount, current_amount, id ))
                db.commit()
        except sqlite3.Error as error:
            print("Ошибка при попытке обновления списка целей", error)
        except OSError as error:
            print("Ошибка файлов", error)