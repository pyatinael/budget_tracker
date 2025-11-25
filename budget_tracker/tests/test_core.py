import os
import tempfile
import unittest
from datetime import datetime

from core.logic import Logic


class TestLogic(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tx_db = os.path.join(self._tmp_dir.name, "transactions_test.db")
        self._sv_db = os.path.join(self._tmp_dir.name, "savings_test.db")
        self.logic = Logic(db_path=self._tx_db, savings_db_path=self._sv_db)

    def tearDown(self):
        self._tmp_dir.cleanup()

    def _create_goal(self, name="Ноутбук", target=1000.0, current=100.0):
        self.logic.savings_db.add_goal(name, target, current)
        goals = self.logic.savings_db.get_goal()
        return goals[-1][0]

    def _last_transaction_id(self):
        rows = self.logic.db.get_all_transactions()
        return rows[-1][0]

    #проверки

    def test_date_validation_ok(self):
        self.logic.date_validation("01.01.25")

    def test_date_validation_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.date_validation("2025-01-01")
        with self.assertRaises(ValueError):
            self.logic.date_validation("01/01/25")
        with self.assertRaises(ValueError):
            self.logic.date_validation("99.99.99")

    def test_amount_validation_ok(self):
        self.assertEqual(self.logic.amount_validation("10.5"), 10.5)
        self.assertEqual(self.logic.amount_validation(7), 7.0)

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Добавляем путь к папке core для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from core.main import BudgetApp


class TestBudgetApp(unittest.TestCase):
    """Тесты для графического интерфейса бюджет-трекера"""

    def test_1(self):
        """Положительный: успешное добавление дохода"""
        app = BudgetApp()
        app.logic.add_income = Mock()
        app.logic.get_transactions = Mock(return_value=[])

        app.type_var.set("Доход")
        app.amount_var.set("5000")
        app.category_var.set("Зарплата")
        app.date_var.set("11.12.25")
        app._on_add()

        # Проверяем что метод вызван с правильными параметрами
        app.logic.add_income.assert_called_once_with("5000", "Зарплата", "11.12.25")
        app.destroy()

    def test_2(self):
        """Отрицательный: добавление с невалидной суммой"""
        app = BudgetApp()
        app.logic.add_income = Mock(side_effect=ValueError("Ошибка"))

        app.type_var.set("Доход")
        app.amount_var.set("abc")
        app.category_var.set("Зарплата")
        app.date_var.set("11.12.25")
        app._on_add()

        # Проверяем что появилась ошибка в статусе
        self.assertIn("❌", app.status_var.get())
        app.destroy()

    def test_3(self):
        """Положительный: применение фильтра дат"""
        app = BudgetApp()
        app._load_transactions_to_table = Mock()

        app.filter_start_var.set("01.12.25")
        app.filter_end_var.set("31.12.25")
        app._apply_date_filter()

        # Проверяем что фильтр сохранился
        self.assertEqual(app.date_filter_start, "01.12.25")
        app.destroy()

    @patch('tkinter.messagebox.showwarning')
    def test_4(self, mock_warning):
        """Отрицательный: редактирование копилки без выбора"""
        app = BudgetApp()
        app._edit_goal()

        # Проверяем что показано предупреждение
        mock_warning.assert_called_once()
        app.destroy()


if __name__ == "__main__":
    unittest.main()

    def test_amount_validation_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.amount_validation("abc")
        with self.assertRaises(ValueError):
            self.logic.amount_validation(0)
        with self.assertRaises(ValueError):
            self.logic.amount_validation(-3)

    def test_category_validation_ok(self):
        self.assertEqual(self.logic.category_validation("  Еда  "), "Еда")

    def test_category_validation_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.category_validation(123)
        with self.assertRaises(ValueError):
            self.logic.category_validation("x" * 51)

    def test_type_validation_ok(self):
        self.assertEqual(self.logic.type_validation("income"), "income")
        self.assertEqual(self.logic.type_validation("expense"), "expense")

    def test_type_validation_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.type_validation("profit")
        with self.assertRaises(ValueError):
            self.logic.type_validation("")
        with self.assertRaises(ValueError):
            self.logic.type_validation(None)

    #служебное

    def test_translate_type_ok(self):
        self.assertEqual(self.logic.translate_type("income"), "Доход")
        self.assertEqual(self.logic.translate_type("expense"), "Расход")
        self.assertEqual(self.logic.translate_type("other"), "other")

    #транзакции

    def test_add_transaction_income_updates_balance(self):
        self.logic.add_transaction("income", 100, "ЗП", "01.01.25")
        self.assertEqual(len(self.logic.transactions), 1)
        self.assertEqual(self.logic.balance, 100.0)

    def test_add_transaction_expense_updates_balance(self):
        self.logic.add_transaction("expense", 40, "Еда", "01.01.25")
        self.assertEqual(len(self.logic.transactions), 1)
        self.assertEqual(self.logic.balance, -40.0)

    def test_add_transaction_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.add_transaction("income", "abc", "ЗП", "01.01.25")
        with self.assertRaises(ValueError):
            self.logic.add_transaction("profit", 10, "ЗП", "01.01.25")
        with self.assertRaises(ValueError):
            self.logic.add_transaction("income", 10, "ЗП", "2025-01-01")

    def test_add_income_ok(self):
        self.logic.add_income(50, "Подарок", "02.01.25")
        self.assertEqual(self.logic.balance, 50.0)
        self.assertEqual(self.logic.transactions[-1][0], "income")

    def test_add_expenses_ok(self):
        self.logic.add_expenses(20, "Кофе", "02.01.25")
        self.assertEqual(self.logic.balance, -20.0)
        self.assertEqual(self.logic.transactions[-1][0], "expense")

    def test_load_transactions_casts_amount_to_float(self):
        self.logic.add_income("10", "ЗП", "01.01.25")
        other = Logic(db_path=self._tx_db, savings_db_path=self._sv_db)
        self.assertEqual(len(other.transactions), 1)
        self.assertIsInstance(other.transactions[0][1], float)
        self.assertEqual(other.transactions[0][1], 10.0)

    def test_summarize_transactions_ok(self):
        self.logic.add_income(100, "ЗП", "01.01.25")
        self.logic.add_expenses(30, "Еда", "01.01.25")
        income, expense, balance = self.logic.summarize_transactions()
        self.assertEqual(income, 100.0)
        self.assertEqual(expense, 30.0)
        self.assertEqual(balance, 70.0)

    def test_get_expenses_by_category_ok(self):
        self.logic.add_income(100, "ЗП", "01.01.25")
        self.logic.add_expenses(10, "Еда", "01.01.25")
        self.logic.add_expenses(5, "Еда", "02.01.25")
        self.logic.add_expenses(7, "Транспорт", "02.01.25")
        result = self.logic.get_expenses_by_category()
        self.assertEqual(result["Еда"], 15.0)
        self.assertEqual(result["Транспорт"], 7.0)

    def test_get_expenses_by_category_empty(self):
        self.logic.add_income(100, "ЗП", "01.01.25")
        self.assertEqual(self.logic.get_expenses_by_category(), "Расходов нет")

    def test_get_balance_by_date_ok(self):
        self.logic.add_income(100, "ЗП", "02.01.25")
        self.logic.add_expenses(10, "Еда", "01.01.25")
        self.logic.add_expenses(5, "Еда", "02.01.25")
        history = self.logic.get_balance_by_date()
        self.assertEqual(history[0][0], "01.01.25")
        self.assertEqual(history[-1][1], 85.0)

    def test_get_balance_by_date_empty(self):
        self.assertEqual(self.logic.get_balance_by_date(), "Нет данных")

    def test_get_transaction_by_id_ok(self):
        self.logic.add_income(10, "ЗП", "01.01.25")
        tid = self._last_transaction_id()
        self.assertIsNotNone(self.logic.get_transaction_by_id(tid))

    def test_get_transaction_by_id_not_found(self):
        self.assertIsNone(self.logic.get_transaction_by_id(999999))

    def test_delete_transaction_by_id_ok(self):
        self.logic.add_income(10, "ЗП", "01.01.25")
        tid = self._last_transaction_id()
        self.logic.delete_transaction_by_id(tid)
        self.assertIsNone(self.logic.get_transaction_by_id(tid))
        self.assertEqual(len(self.logic.transactions), 0)

    def test_delete_transaction_alias_ok(self):
        self.logic.add_income(10, "ЗП", "01.01.25")
        tid = self._last_transaction_id()
        self.logic.delete_transaction(tid)
        self.assertIsNone(self.logic.get_transaction_by_id(tid))

    def test_delete_transaction_by_id_bad_raises(self):
            self.logic.add_income(10, "ЗП", "01.01.25")
            before = len(self.logic.db.get_all_transactions())

            self.logic.delete_transaction_by_id(999999)

            after = len(self.logic.db.get_all_transactions())
            self.assertEqual(before, after)

    def test_edit_transaction_ok(self):
        self.logic.add_income(10, "ЗП", "01.01.25")
        tid = self._last_transaction_id()
        self.logic.edit_transaction(tid, "expense", 3, "Еда", "02.01.25")
        row = self.logic.get_transaction_by_id(tid)
        self.assertEqual(float(row[1]), 3.0)
        self.assertEqual(row[2], "Еда")
        self.assertEqual(row[3], "02.01.25")
        self.assertEqual(row[4], "expense")

    def test_edit_transaction_bad_raises(self):
        self.logic.add_income(10, "ЗП", "01.01.25")
        tid = self._last_transaction_id()
        with self.assertRaises(ValueError):
            self.logic.edit_transaction(tid, "profit", 3, "Еда", "02.01.25")
        with self.assertRaises(ValueError):
            self.logic.edit_transaction(tid, "income", "abc", "Еда", "02.01.25")
        with self.assertRaises(ValueError):
            self.logic.edit_transaction(tid, "income", 3, "Еда", "2025-01-01")

    #копилки

    def test_calculate_progress_ok(self):
        goal = (1, "Ноутбук", 1000.0, 250.0)
        self.assertEqual(self.logic.calculate_progress(goal), 25.0)

    def test_calculate_progress_target_zero(self):
        goal = (1, "Ноутбук", 0.0, 250.0)
        self.assertEqual(self.logic.calculate_progress(goal), 0.0)

    def test_deposit_to_goal_ok(self):
        gid = self._create_goal(current=100.0)
        start_balance = self.logic.balance
        self.logic.deposit_to_goal(gid, 50)
        goal = self.logic._find_goal_row(gid)
        self.assertEqual(goal[3], 150.0)
        self.assertEqual(self.logic.transactions[-1][0], "expense")
        self.assertEqual(self.logic.balance, start_balance - 50.0)

    def test_deposit_to_goal_bad_goal_raises(self):
        with self.assertRaises(ValueError):
            self.logic.deposit_to_goal(999999, 10)

    def test_withdraw_from_goal_ok(self):
        gid = self._create_goal(current=200.0)
        start_balance = self.logic.balance
        self.logic.withdraw_from_goal(gid, 50)
        goal = self.logic._find_goal_row(gid)
        self.assertEqual(goal[3], 150.0)
        self.assertEqual(self.logic.transactions[-1][0], "income")
        self.assertEqual(self.logic.balance, start_balance + 50.0)

    def test_withdraw_from_goal_not_enough_raises(self):
        gid = self._create_goal(current=10.0)
        with self.assertRaises(ValueError):
            self.logic.withdraw_from_goal(gid, 50)

    def test_update_goal_info_ok(self):
        gid = self._create_goal()
        self.logic.update_goal_info(gid, "Ноут", 1500.0, 200.0)
        goal = self.logic._find_goal_row(gid)
        self.assertEqual(goal[1], "Ноут")
        self.assertEqual(goal[2], 1500.0)
        self.assertEqual(goal[3], 200.0)


    def test_delete_goal_with_transactions_ok(self):
        gid = self._create_goal()
        self.logic.delete_goal_with_transactions(gid)
        with self.assertRaises(ValueError):
            self.logic._find_goal_row(gid)

    #фильтрация

    def test_filter_transactions_by_date_range_ok(self):
        self.logic.add_income(100, "ЗП", "01.01.25")
        self.logic.add_expenses(10, "Еда", "05.01.25")
        filtered = self.logic.filter_transactions_by_date_range("01.01.25", "05.01.25")
        self.assertEqual(len(filtered), 2)

    def test_summarize_transactions_by_range_ok(self):
        self.logic.add_income(100, "ЗП", "01.01.25")
        self.logic.add_expenses(10, "Еда", "05.01.25")
        income, expense, balance = self.logic.summarize_transactions_by_range(
            "01.01.25", "05.01.25"
        )
        self.assertEqual(balance, 90.0)

    def test_get_expenses_by_category_range_empty(self):
        self.logic.add_income(100, "ЗП", "01.01.25")
        result = self.logic.get_expenses_by_category_range("01.01.25", "10.01.25")
        self.assertEqual(result, "Расходов нет")


if __name__ == "__main__":
    unittest.main()

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

        # Проверяем, что во 2 строке(1 индекс) и 4 столбце(3 индекс, столбец считается 4, 
        # т.к поле ID стоящее на 0 индексе подразумевается, но не прописывается) 
        # соответствует дате - "2024-05-10"
        self.assertEqual(rows[1][3],"2024-05-10")
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
