"""Question bank integrity tests: the content is the product, so pin it."""

import unittest

from prep import bank


class TestBank(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = bank.load_bank()

    def test_size_and_categories(self):
        self.assertEqual(len(self.payload["questions"]), 48)
        self.assertEqual(bank.categories(self.payload),
                         ["behavioral", "python", "data-structures",
                          "sql", "ml", "product"])

    def test_every_category_has_questions(self):
        for cat in bank.categories(self.payload):
            qs = bank.by_category(self.payload, cat)
            self.assertGreaterEqual(len(qs), 8, cat)

    def test_every_question_complete(self):
        for q in self.payload["questions"]:
            self.assertTrue(q["id"], q)
            self.assertTrue(q["question"].strip(), q["id"])
            self.assertTrue(q["why"].strip(), q["id"])
            self.assertGreaterEqual(len(q["followups"]), 2, q["id"])

    def test_no_duplicate_ids(self):
        ids = [q["id"] for q in self.payload["questions"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_company_attributions(self):
        # the bank must not claim questions came from specific companies
        for q in self.payload["questions"]:
            blob = (q["question"] + " " + q["why"]).lower()
            for word in ("asked at", "google asks", "meta asks", "from amazon"):
                self.assertNotIn(word, blob, q["id"])

    def test_get_roundtrip(self):
        q = bank.get(self.payload, "py-001")
        self.assertIn("list", q["question"].lower())
        with self.assertRaises(KeyError):
            bank.get(self.payload, "nope-000")

    def test_filter(self):
        self.assertEqual(len(bank.by_category(self.payload, "sql")), 8)
        self.assertEqual(len(bank.by_category(self.payload)), 48)
        self.assertEqual(bank.by_category(self.payload, "SQL"),
                         bank.by_category(self.payload, "sql"))


if __name__ == "__main__":
    unittest.main()
