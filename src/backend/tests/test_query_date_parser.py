import sys
import unittest
from datetime import date
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.date_parser import iter_dates, parse_date_scope


class QueryDateParserTests(unittest.TestCase):
    def test_defaults_to_today(self):
        scope = parse_date_scope("Did my cat eat?", today="2026-07-06")
        self.assertEqual(scope.start_date, date(2026, 7, 6))
        self.assertEqual(scope.end_date, date(2026, 7, 6))

    def test_understands_yesterday(self):
        scope = parse_date_scope("Did my cat jump yesterday?", today="2026-07-06")
        self.assertEqual(scope.start_date, date(2026, 7, 5))

    def test_understands_last_n_days(self):
        scope = parse_date_scope("Did my cat run in the last 3 days?", today="2026-07-06")
        self.assertEqual(scope.start_date, date(2026, 7, 4))
        self.assertEqual(scope.end_date, date(2026, 7, 6))
        self.assertEqual(len(list(iter_dates(scope))), 3)

    def test_understands_explicit_range(self):
        scope = parse_date_scope(
            "Did my cat eat from 2026-07-01 to 2026-07-06?"
        )
        self.assertEqual(scope.start_date, date(2026, 7, 1))
        self.assertEqual(scope.end_date, date(2026, 7, 6))

    def test_explicit_arguments_override_question(self):
        scope = parse_date_scope(
            "Did my cat eat today?",
            start_date="2026-06-01",
            end_date="2026-06-02",
            today="2026-07-06",
        )
        self.assertEqual(scope.start_date, date(2026, 6, 1))
        self.assertEqual(scope.end_date, date(2026, 6, 2))

    def test_rejects_reversed_range(self):
        with self.assertRaises(ValueError):
            parse_date_scope(
                "Did my cat eat?",
                start_date="2026-07-06",
                end_date="2026-07-01",
            )


if __name__ == "__main__":
    unittest.main()

