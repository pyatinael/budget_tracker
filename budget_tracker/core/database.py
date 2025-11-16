# Импортируем необходимую библиотеку sqlite3 для работы с базой данных
import sqlite3

# Определяем класс Базы данных, который инкапсулирует(объединяет, упаковывает) 
# всю работу связанную с базой данных SQL 
class DataBase:
    # Метод __init__ - конструктор класса, передаем в него переменную отвечающую за путь к файлу базы данных
    def __init__(self, path):
        # Сохраняем путь к атрибуту объекта, чтобы использовать его в других методах
        self.path = path

    # Создаем метод, отвечающий за создание таблицы в базе данных
    def create_db(self):
        # Вручную открываем подключение к базе данных по пути self.path (и сразу закрываем подключение)
        with sqlite3.connect(self.path) as db:
            # Создаем курсор - объект, который позволяет выполнять команды SQL
            cursor = db.cursor()
            # Создаем SQL-запрос для создания таблицы transactions, при условии, что она еще не создана
            query = """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL,
                    category TEXT,
                    date TEXT,
                    type TEXT
                )
            """          
            # Выполняем SQL-запрос
            cursor.execute(query)
            # Сохраняем изменения в базе данных, обновляем ее
            db.commit()

    # Создаем метод, добавляющий информацию в таблицу, принимает данные транзакций
    def add_transaction(self, amount, category, date, type_):
        # Вручную открываем подключение к базе данных по пути self.path (и сразу закрываем подключение)
        with sqlite3.connect(self.path) as db:
            # Создаем курсор - объект, который позволяет выполнять команды SQL
            cursor = db.cursor()
            # Создаем SQL-запрос для добавления строки в таблицу transactions
            query = """
                INSERT INTO transactions (amount, category, date, type)
                VALUES (?, ?, ?, ?)
            """
            # Выполняем SQL-запрос с подставленными значениями
            cursor.execute(query, (amount, category, date, type_))
            # Сохраняем изменения в базе данных, обновляем ее
            db.commit()

    # Создаем метод, получающий информацию из таблицы базы данных   
    def get_all_transactions(self):
        # Вручную открываем подключение к базе данных по пути self.path (и сразу закрываем подключение)
        with sqlite3.connect(self.path) as db:
            # Создаем курсор - объект, который позволяет выполнять команды SQL
            cursor = db.cursor()
            # Получаем все строки из таблицы базы данных
            cursor.execute("SELECT * FROM transactions")
            # Возвращаем все записи из таблицы базы данных в виде кортежа
            return cursor.fetchall()