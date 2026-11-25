"""CLI tests: scripted end-to-end runs against a temp state file."""

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock

from prep import cli, sr


class CliCase(unittest.TestCase):
    def setUp(self):
        self.state_file = "/tmp/test_cli_state.json"
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
        patcher = mock.patch.dict(os.environ, {"PREP_STATE": self.state_file})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: os.path.exists(self.state_file)
                        and os.remove(self.state_file))

    def run_cli(self, *argv, inputs=()):
        buf = io.StringIO()
        with mock.patch("builtins.input", side_effect=list(inputs)):
            with redirect_stdout(buf):
                code = cli.main(list(argv))
        return code, buf.getvalue()


class TestReadCommands(CliCase):
    def test_categories(self):
        code, out = self.run_cli("categories")
        self.assertEqual(code, 0)
        for cat in ("behavioral", "python", "data-structures",
                    "sql", "ml", "product"):
            self.assertIn(cat, out)

    def test_list_filter(self):
        code, out = self.run_cli("list", "--category", "ml")
        self.assertEqual(code, 0)
        self.assertIn("ml-001", out)
        self.assertNotIn("py-001", out)

    def test_show(self):
        code, out = self.run_cli("show", "ds-001")
        self.assertIn("linked list", out)
        self.assertIn("why it matters", out)
        self.assertIn("follow-ups", out)

    def test_show_unknown_exits(self):
        with self.assertRaises(SystemExit):
            self.run_cli("show", "nope-999")

    def test_help(self):
        code, out = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("practice", out)

    def test_due_all_new(self):
        code, out = self.run_cli("due")
        self.assertIn("48 cards due", out)


class TestPractice(CliCase):
    def test_practice_session_updates_state(self):
        # answer two questions, grade 5 then 2
        code, out = self.run_cli("practice", "-n", "2",
                                 inputs=["", "5", "", "2"])
        self.assertIn("session done: 2 graded", out)
        state = sr.load_state(self.state_file)
        self.assertEqual(len(state["cards"]), 2)
        self.assertEqual(state["sessions"], 1)
        grades = [g for c in state["cards"].values() for _, g in c["history"]]
        self.assertEqual(grades, [5, 2])

    def test_practice_rejects_bad_grade_then_accepts(self):
        code, out = self.run_cli("practice", "-n", "1",
                                 inputs=["", "9", "abc", "4"])
        self.assertIn("0-5 only", out)
        state = sr.load_state(self.state_file)
        grades = [g for c in state["cards"].values() for _, g in c["history"]]
        self.assertEqual(grades, [4])

    def test_stats_after_session(self):
        self.run_cli("practice", "-n", "3", inputs=["", "5", "", "4", "", "3"])
        code, out = self.run_cli("stats")
        self.assertIn("seen:      3", out)
        self.assertIn("sessions:  1", out)


if __name__ == "__main__":
    unittest.main()
