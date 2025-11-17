import unittest
from core.logic import Logic

class FinanceTest(unittest.TestCase):

    def setUp(self):
        self.logic = Logic()
        # очищаем список перед каждым тестом
        self.logic.transactions.clear()

    def test_date_validation_ok(self):
        # формат корректный
        self.logic.date_validation("2025-01-10")

    def test_date_validation_wrong(self):
        # некорректная дата
        with self.assertRaises(ValueError):
            self.logic.date_validation("10-01-2025")

    def test_add_income_adds_item(self):
        self.logic.add_income(1000, "salary", "2025-01-10")
        self.assertEqual(len(self.logic.transactions), 1)
        self.assertEqual(
            self.logic.transactions[0],
            ("income", 1000, "salary", "2025-01-10")
        )

    def test_add_expenses_adds_item(self):
        self.logic.add_expenses(200, "food", "2025-01-11")
        self.assertEqual(len(self.logic.transactions), 1)
        self.assertEqual(
            self.logic.transactions[0],
            ("expense", 200, "food", "2025-01-11")
        )

    def test_add_income_bad_date(self):
        with self.assertRaises(ValueError):
            self.logic.add_income(500, "gift", "2025/01/10")

    def test_add_expenses_bad_date(self):
        with self.assertRaises(ValueError):
            self.logic.add_expenses(300, "taxi", "2025.01.11")

    def test_summarize_empty(self):
        self.assertEqual(self.logic.summarize_transactions(), (0, 0, 0))

    def test_summarize_only_income(self):
        self.logic.add_income(1000, "salary", "2025-01-10")
        self.logic.add_income(500, "gift", "2025-01-11")
        self.assertEqual(self.logic.summarize_transactions(), (1500, 0, 1500))

    def test_summarize_income_and_expenses(self):
        self.logic.add_income(1000, "salary", "2025-01-10")
        self.logic.add_income(500, "gift", "2025-01-11")
        self.logic.add_expenses(300, "food", "2025-01-12")
        self.logic.add_expenses(100, "transport", "2025-01-13")
        self.assertEqual(self.logic.summarize_transactions(), (1500, 400, 1100))

