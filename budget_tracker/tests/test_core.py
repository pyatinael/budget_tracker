import unittest
import sys
import os
from unittest.mock import Mock, patch

# Добавляем путь к папке core для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from main import BudgetApp


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
