import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.query_layer.response_storage import store_query_response


class QueryResponseStorageTests(unittest.TestCase):
    def test_separates_proof_and_non_proof_responses_by_day(self):
        with tempfile.TemporaryDirectory() as directory:
            now = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)
            proof = store_query_response(
                {"proof": True},
                include_proof=True,
                response_root=directory,
                now=now,
                response_id="proof-one",
            )
            no_proof = store_query_response(
                {"proof": False},
                include_proof=False,
                response_root=directory,
                now=now,
                response_id="plain-one",
            )

            self.assertEqual(proof.parent.name, "proof_requested")
            self.assertEqual(no_proof.parent.name, "proof_not_requested")
            self.assertEqual(proof.parent.parent.name, "2026-07-06")
            self.assertEqual(json.loads(proof.read_text())["proof"], True)

    def test_multiple_queries_never_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            now = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)
            first = store_query_response(
                {"query": 1}, False, directory, now, response_id="same-id"
            )
            second = store_query_response(
                {"query": 2}, False, directory, now, response_id="same-id"
            )

            self.assertNotEqual(first, second)
            self.assertEqual(json.loads(first.read_text())["query"], 1)
            self.assertEqual(json.loads(second.read_text())["query"], 2)


if __name__ == "__main__":
    unittest.main()
