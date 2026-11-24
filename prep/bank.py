"""Load and filter the question bank.

The bank is data/questions.json - real questions with honest categories,
written for SWE/ML/PM internship interviews at the undergrad level. No
question in the bank claims to come from a specific company; they are the
standard prompts that come up constantly.
"""

import json
import os

BANK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    os.pardir, "data", "questions.json")


def load_bank(path=BANK):
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    questions = payload["questions"]
    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"duplicate question ids in bank: {dupes}")
    for q in questions:
        if q["category"] not in payload["categories"]:
            raise ValueError(f"{q['id']}: unknown category {q['category']!r}")
    return payload


def categories(payload):
    return list(payload["categories"])


def by_category(payload, category=None):
    questions = payload["questions"]
    if category is None:
        return list(questions)
    key = category.strip().lower()
    return [q for q in questions if q["category"] == key]


def get(payload, question_id):
    for q in payload["questions"]:
        if q["id"] == question_id:
            return q
    raise KeyError(question_id)
