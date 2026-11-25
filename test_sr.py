"""SM-2 scheduling math tests with fixed dates (no wall-clock dependence)."""

import unittest
from datetime import date, timedelta

from prep import sr

DAY0 = date(2026, 11, 25)
D = str(DAY0)


def fresh_state():
    return {"cards": {}, "sessions": 0}


class TestGrade(unittest.TestCase):
    def test_first_pass_interval_one(self):
        state = fresh_state()
        card = sr.grade(state, "q1", 5, today=D)
        self.assertEqual(card["interval"], 1)
        self.assertEqual(card["reps"], 1)
        self.assertEqual(card["due"], str(DAY0 + timedelta(days=1)))

    def test_second_pass_interval_three(self):
        state = fresh_state()
        sr.grade(state, "q1", 5, today=D)
        card = sr.grade(state, "q1", 4, today=D)
        self.assertEqual(card["interval"], 3)
        self.assertEqual(card["due"], str(DAY0 + timedelta(days=3)))

    def test_third_pass_scales_by_ease(self):
        state = fresh_state()
        sr.grade(state, "q1", 5, today=D)   # interval 1, ease 2.6
        sr.grade(state, "q1", 5, today=D)   # interval 3, ease 2.7
        card = sr.grade(state, "q1", 5, today=D)
        self.assertEqual(card["interval"], round(3 * card["ease"]))
        self.assertGreater(card["ease"], 2.5)

    def test_lapse_resets_to_tomorrow(self):
        state = fresh_state()
        sr.grade(state, "q1", 5, today=D)
        before = sr.grade(state, "q1", 5, today=D)
        card = sr.grade(state, "q1", 2, today=D)
        self.assertEqual(card["reps"], 0)
        self.assertEqual(card["lapses"], 1)
        self.assertEqual(card["interval"], 1)
        self.assertEqual(card["due"], str(DAY0 + timedelta(days=1)))
        self.assertLess(card["ease"], before["ease"])

    def test_ease_floor(self):
        state = fresh_state()
        for _ in range(20):
            card = sr.grade(state, "q1", 0, today=D)
        self.assertEqual(card["ease"], sr.MIN_EASE)

    def test_bad_grade_rejected(self):
        with self.assertRaises(ValueError):
            sr.grade(fresh_state(), "q1", 6, today=D)
        with self.assertRaises(ValueError):
            sr.grade(fresh_state(), "q1", -1, today=D)

    def test_history_recorded(self):
        state = fresh_state()
        sr.grade(state, "q1", 4, today=D)
        sr.grade(state, "q1", 2, today=D)
        self.assertEqual(state["cards"]["q1"]["history"], [[D, 4], [D, 2]])


class TestDueOrdering(unittest.TestCase):
    def test_new_and_overdue_first(self):
        state = fresh_state()
        sr.grade(state, "old", 5, today="2026-11-01")   # due 2026-11-02
        sr.grade(state, "mid", 5, today="2026-11-20")   # due 2026-11-21
        questions = [{"id": "mid"}, {"id": "new"}, {"id": "old"}]
        due = sr.due_cards(state, questions, today=D)
        self.assertEqual([q["id"] for q, _ in due], ["old", "mid", "new"])

    def test_future_cards_not_due(self):
        state = fresh_state()
        sr.grade(state, "later", 5, today=D)  # due tomorrow
        due = sr.due_cards(state, [{"id": "later"}], today=D)
        self.assertEqual(due, [])


class TestStats(unittest.TestCase):
    def test_stats_counts(self):
        state = fresh_state()
        sr.grade(state, "a", 5, today=D)
        sr.grade(state, "a", 5, today=D)
        sr.grade(state, "a", 5, today=D)  # interval now 21d+? no - check below
        questions = [{"id": "a"}, {"id": "b"}]
        s = sr.stats(state, questions)
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["seen"], 1)
        self.assertEqual(s["grades_given"], 3)

    def test_state_roundtrip(self, tmp="/tmp/test_sr_state.json"):
        import os
        state = fresh_state()
        sr.grade(state, "a", 3, today=D)
        sr.save_state(state, path=tmp)
        loaded = sr.load_state(path=tmp)
        self.assertEqual(loaded, state)
        os.remove(tmp)


if __name__ == "__main__":
    unittest.main()
