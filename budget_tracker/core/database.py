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
            Метод, отвечающий за создание таблицы transactions, при условии: что онв еще не создана

            В таблице есть поля:
            id: INTEGER PRIMARY KEY, AUTOINCREMENT,
            amount: REAL,
            category: TEXT,
            date: TEXT,
            type: TEXT

            Метод автоматически открывает и закрывает соединение
        """
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

    def add_transaction(self, amount, category, date, type_):
        """ 
            Добавляет новую запись в таблицу transactions

            amount: float сумма транзакции
            category: str категория, например, "food", "transport"
            date: str дата в формате DD.MM.YYYY
            type: str тип транзакции "доход", "расход"
             
        """
        with sqlite3.connect(self.path) as db:
            cursor = db.cursor()
            query = """
                INSERT INTO transactions (amount, category, date, type)
                VALUES (?, ?, ?, ?)
            """
            cursor.execute(query, (amount, category, date, type_))
            db.commit()

    def get_all_transactions(self):
        """
            Возвращает список всех транзакций(список кортежей, кортеж - строка таблицы) из таблицы transactions
        """
        with sqlite3.connect(self.path) as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM transactions")
            return cursor.fetchall()
    
        
    def get_transaction(self,id):
        """
            Возвращает одну транзакцию по ее ID (кортеж со значениями полей одной транзакции или None, если запись не найдена)

            id : int идентификатор записи
        """
        with sqlite3.connect(self.path) as db:
            cursor = db.cursor()
            cursor.execute(""" SELECT * FROM transactions WHERE id=? """, (id,))
            return cursor.fetchone()
        
    def delete_transaction(self,id):
        """
            Удаляет транзакцию по её ID

            id : int идентификатор записи, которую нужно удалить
        """
        with sqlite3.connect(self.path) as db:
            cursor = db.cursor()
            cursor.execute(""" DELETE FROM transactions WHERE id=?""",(id,))
            db.commit()
    
    def update_transaction(self, id, amount, category, date, type_):
        """
            Обновляет существующую транзакцию

            id : int идентификатор записи, которую нужно обновить
            amount : float новая сумма транзакции
            category : str новая категория
            date : str новая дата в формате DD.MM.YYYY
            type_ : str новый тип транзакции "доход", "расход"

        """
        with sqlite3.connect(self.path) as db:
            cursor = db.cursor()
            query = """ UPDATE transactions SET amount=?, category=?, date=?, type=? WHERE id=? """
            cursor.execute(query, (amount, category, date, type_, id ))
            db.commit()
