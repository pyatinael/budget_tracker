# Импортируем все необходимые библиотеки:
# os - для работы с операционной системой (чтобы работать с файлами и проверять существование тестовой базы данных)
# sqlite3 - для работы с базой данных
# unittest - используется для написания тестов
import os
import sqlite3
import unittest

from core.database import DataBase


class DataBaseTest(unittest.TestCase):

    """
        Набор тестов для проверки функциональности класса DataBase

        Каждый тест использует отдельный тестовый файл SQLite, 
        который создаётся в setUp() и удаляется перед созданием нового
    """

    TEST_DB = "test_db.sqlite"

    def setUp(self):
        """
            Метод, выполняющийся перед каждым тестом

            - удаляет тестовую БД, если она осталась от предыдущего теста
            - создаёт новый экземпляр DataBase
            - создаёт таблицу transactions вызовом create_db()

        """

        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)
        
        self.db = DataBase(self.TEST_DB)
        self.db.create_db()

    def test_add_in_db(self):
        self.db.add_transaction(10000.06, "food", "15.11.2025", "доход")
        with sqlite3.connect(self.TEST_DB) as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM transactions")
            result = cursor.fetchall()
        expected = [(1, 10000.06, "food", "15.11.2025", "доход")]
        self.assertEqual(result, expected)

    def test_get_db(self):
        self.db.add_transaction(100, "transport", "05.05.2025", "расход")
        self.db.add_transaction(500, "salary", "20.03.2024", "доход")
        rows = self.db.get_all_transactions()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][2],"transport")
        self.assertEqual(rows[1][3],"20.03.2024")

    def test_get_transaction(self):
         self.db.add_transaction(320, "transport", "15.06.2022", "расход")
         self.db.add_transaction(10000, "salary", "11.07.2024", "доход")
         self.db.add_transaction(7000, "salary", "04.08.2024", "доход")
         rows = self.db.get_transaction(3)
         self.assertEqual(rows[1],7000)
         self.assertEqual(rows[2],"salary")
         self.assertEqual(rows[3],"04.08.2024")
         self.assertEqual(rows[4],"доход")

    def test_delete_transctions(self):
        self.db.add_transaction(1000, "food", "16.10.2025", "расход")
        self.db.add_transaction(15000, "salary", "13.03.2025", "доход")
        row = self.db.delete_transaction(1)
        self.assertIsNone(row)

    def test_update_transaction(self):
        self.db.add_transaction(1000, "food", "16.10.2025", "расход")
        self.db.update_transaction(1, 250, "cafe", "09.09.2023", "расход")
        updated_row = self.db.get_transaction(1)
        self.assertEqual(updated_row[1], 250)
        self.assertEqual(updated_row[2], "cafe")
        self.assertEqual(updated_row[3], "09.09.2023")
        self.assertEqual(updated_row[4], "расход")