import os
import tempfile
import unittest

from budget_tracker.core.logic import Logic


class TestLogic(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tx_db = os.path.join(self._tmp_dir.name, "transactions_test.db")
        self._sv_db = os.path.join(self._tmp_dir.name, "savings_test.db")

        self.logic = Logic(db_path=self._tx_db, savings_db_path=self._sv_db)

    def tearDown(self):
        self._tmp_dir.cleanup()

    # ---------- helpers for savings ----------
    def _create_goal(self, name="Ноутбук", target=1000.0, current=100.0):
        self.logic.savings_db.add_goal(name, target, current)
        goals = self.logic.savings_db.get_goal()
        return goals[-1][0] 

    # ---------- validations ----------

    def test_amount_validation_ok(self):
        self.assertEqual(self.logic.amount_validation("10.5"), 10.5)

    def test_amount_validation_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.amount_validation("abc")
        with self.assertRaises(ValueError):
            self.logic.amount_validation(0)
        with self.assertRaises(ValueError):
            self.logic.amount_validation(-3)

    def test_date_validation_ok(self):
        self.logic.date_validation("12.12.25")  

    def test_date_validation_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.date_validation("2025-12-12")
        with self.assertRaises(ValueError):
            self.logic.date_validation("31.02.25")

    def test_category_validation_ok_strips(self):
        self.assertEqual(self.logic.category_validation("  Еда  "), "Еда")

    def test_category_validation_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.category_validation(123)
        with self.assertRaises(ValueError):
            self.logic.category_validation("a" * 51)

    def test_type_validation_ok(self):
        self.assertEqual(self.logic.type_validation("income"), "income")
        self.assertEqual(self.logic.type_validation("expense"), "expense")

    def test_type_validation_bad_raises(self):
        with self.assertRaises(ValueError):
            self.logic.type_validation("INC")

    # ---------- transactions core ----------

    def test_add_income_and_expense_updates_balance(self):
        self.logic.add_income(1000, "ЗП", "10.12.25")
        self.logic.add_expenses(250, "Еда", "11.12.25")

        self.assertEqual(self.logic.balance, 750.0)

        income, expense, balance = self.logic.summarize_transactions()
        self.assertEqual(income, 1000.0)
        self.assertEqual(expense, 250.0)
        self.assertEqual(balance, 750.0)

    def test_get_expenses_by_category_no_expenses(self):
        self.logic.add_income(500, "Подарок", "10.12.25")
        self.assertEqual(self.logic.get_expenses_by_category(), "Расходов нет")

    def test_get_expenses_by_category_ok(self):
        self.logic.add_expenses(100, "Еда", "11.12.25")
        self.logic.add_expenses(50, "Еда", "12.12.25")
        self.logic.add_expenses(20, "Транспорт", "12.12.25")

        grouped = self.logic.get_expenses_by_category()
        self.assertIsInstance(grouped, dict)
        self.assertEqual(grouped["Еда"], 150.0)
        self.assertEqual(grouped["Транспорт"], 20.0)

    # ---------- balance history ----------

    def test_get_balance_by_date_no_data(self):
        self.assertEqual(self.logic.get_balance_by_date(), "Нет данных")

    def test_get_balance_by_date_ok(self):
        self.logic.add_income(100, "ЗП", "10.12.25")
        self.logic.add_expenses(30, "Еда", "10.12.25")
        self.logic.add_expenses(10, "Еда", "11.12.25")

        hist = self.logic.get_balance_by_date()
        self.assertIsInstance(hist, list)
        self.assertEqual(hist[0][0], "10.12.25")
        self.assertEqual(hist[0][1], 70.0)
        self.assertEqual(hist[1][0], "11.12.25")
        self.assertEqual(hist[1][1], 60.0)

    # ---------- translate_type ----------

    def test_translate_type(self):
        self.assertEqual(self.logic.translate_type("income"), "Доход")
        self.assertEqual(self.logic.translate_type("expense"), "Расход")
        self.assertEqual(self.logic.translate_type("other"), "other")

    # ---------- calculate_progress ----------

    def test_calculate_progress_ok(self):
        goal = (1, "Цель", 1000.0, 250.0)
        self.assertEqual(self.logic.calculate_progress(goal), 25.0)

    def test_calculate_progress_caps_at_100(self):
        goal = (1, "Цель", 100.0, 250.0)
        self.assertEqual(self.logic.calculate_progress(goal), 100.0)

    def test_calculate_progress_target_zero(self):
        goal = (1, "Цель", 0.0, 50.0)
        self.assertEqual(self.logic.calculate_progress(goal), 0.0)

    # ---------- deposit_to_goal ----------

    def test_deposit_to_goal_ok(self):
        goal_id = self._create_goal(name="Ноутбук", target=1000.0, current=100.0)

        self.logic.deposit_to_goal(goal_id, 50)

        goal_row = [g for g in self.logic.savings_db.get_goal() if g[0] == goal_id][0]
        self.assertEqual(goal_row[3], 150.0)

        expenses = [t for t in self.logic.transactions if t[0] == "expense"]
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0][1], 50.0)
        self.assertIn("Копилка:", expenses[0][2])

    def test_deposit_to_goal_bad_amount_raises(self):
        goal_id = self._create_goal()
        with self.assertRaises(ValueError):
            self.logic.deposit_to_goal(goal_id, 0)

    def test_deposit_to_goal_goal_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.logic.deposit_to_goal(999999, 10)

    # ---------- withdraw_from_goal ----------

    def test_withdraw_from_goal_ok(self):
        goal_id = self._create_goal(name="Поездка", target=500.0, current=200.0)

        self.logic.withdraw_from_goal(goal_id, 50)

        goal_row = [g for g in self.logic.savings_db.get_goal() if g[0] == goal_id][0]
        self.assertEqual(goal_row[3], 150.0)

        incomes = [t for t in self.logic.transactions if t[0] == "income"]
        self.assertEqual(len(incomes), 1)
        self.assertEqual(incomes[0][1], 50.0)
        self.assertIn("Из копилки:", incomes[0][2])

    def test_withdraw_from_goal_not_enough_money_raises(self):
        goal_id = self._create_goal(current=10.0)
        with self.assertRaises(ValueError):
            self.logic.withdraw_from_goal(goal_id, 50)

    def test_withdraw_from_goal_goal_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.logic.withdraw_from_goal(999999, 10)


if __name__ == "__main__":
    unittest.main()