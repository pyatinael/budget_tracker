import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Добавляем путь к папке core для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from main import BudgetApp


class TestBudgetApp(unittest.TestCase):
    """Тесты критичного функционала бюджет-трекера"""

    def test_add_transaction_success(self):
        """
        Положительный тест: успешное добавление транзакции

        Проверяет:
        - Корректный вызов метода добавления дохода
        - Установку правильного статуса успеха
        - Очистку полей ввода после добавления
        """
        app = BudgetApp()

        # Мокируем логику
        app.logic.add_income = Mock()
        app.logic.get_transactions = Mock(return_value=[])

        # Заполняем форму валидными данными
        app.type_var.set("Доход")
        app.amount_var.set("5000")
        app.category_var.set("Зарплата")
        app.date_var.set("11.12.25")

        # Выполняем добавление
        app._on_add()

        # Проверяем результат
        app.logic.add_income.assert_called_once_with("5000", "Зарплата", "11.12.25")
        self.assertIn("✅", app.status_var.get())
        self.assertIn("добавлена", app.status_var.get())
        self.assertEqual(app.amount_var.get(), "")  # Поле очищено
        self.assertEqual(app.category_var.get(), "")  # Поле очищено

        app.destroy()

    def test_add_transaction_invalid_amount(self):
        """
        Отрицательный тест: попытка добавить транзакцию с невалидной суммой

        Проверяет:
        - Обработку исключения ValueError
        - Установку сообщения об ошибке в статусе
        """
        app = BudgetApp()

        # Мокируем логику с исключением
        app.logic.add_income = Mock(side_effect=ValueError("Некорректная сумма"))

        # Заполняем форму с невалидной суммой
        app.type_var.set("Доход")
        app.amount_var.set("abc123")  # Текст вместо числа
        app.category_var.set("Зарплата")
        app.date_var.set("11.12.25")

        # Пытаемся добавить
        app._on_add()

        # Проверяем обработку ошибки
        self.assertIn("❌", app.status_var.get())
        self.assertTrue(
            "Некорректная сумма" in app.status_var.get() or 
            "Ошибка" in app.status_var.get()
        )

        app.destroy()

    def test_date_filter_valid_format(self):
        """
        Положительный тест: применение фильтра дат с корректным форматом

        Проверяет:
        - Успешную валидацию формата DD.MM.YY
        - Сохранение выбранного периода
        - Установку статуса успеха
        """
        app = BudgetApp()

        # Мокируем метод загрузки транзакций
        app._load_transactions_to_table = Mock()

        # Устанавливаем валидный период
        app.filter_start_var.set("01.12.25")
        app.filter_end_var.set("31.12.25")

        # Применяем фильтр
        app._apply_date_filter()

        # Проверяем результат
        self.assertEqual(app.date_filter_start, "01.12.25")
        self.assertEqual(app.date_filter_end, "31.12.25")
        self.assertIn("✅", app.status_var.get())
        self.assertIn("Фильтр", app.status_var.get())

        app.destroy()

    @patch('tkinter.messagebox.showwarning')
    def test_edit_goal_without_selection(self, mock_warning):
        """
        Отрицательный тест: попытка редактирования копилки без выбора

        Проверяет:
        - Предотвращение операции при отсутствии выбора
        - Показ предупреждающего сообщения пользователю
        - Корректный текст сообщения
        """
        app = BudgetApp()

        # Пытаемся редактировать без выбора копилки
        app._edit_goal()

        # Проверяем, что показано предупреждение
        mock_warning.assert_called_once()
        call_args = mock_warning.call_args[0]
        self.assertEqual(call_args[0], "Предупреждение")
        self.assertIn("Выберите копилку", call_args[1])

        app.destroy()


if __name__ == "__main__":
    unittest.main(verbosity=2)
