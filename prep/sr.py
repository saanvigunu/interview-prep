"""Spaced repetition: a straightforward SM-2 variant.

Each question is self-graded 0-5 after you answer out loud:
    5 instant and solid   4 right, with effort   3 right, barely
    2 wrong but familiar  1 wrong, faint memory  0 blank

Grades >= 3 pass and stretch the interval by the ease factor; grades < 3
fail and reset the card to relearn tomorrow (with a small ease penalty,
floor 1.3 - same rule as SM-2). State lives in a plain JSON file you can
read and delete; nothing leaves your machine.
"""

import json
import os
from datetime import date, timedelta

DEFAULT_STATE = os.path.join(os.path.expanduser("~"),
                             ".local", "share", "interview-prep", "state.json")
MIN_EASE = 1.3
START_EASE = 2.5


def state_path():
    return os.environ.get("PREP_STATE", DEFAULT_STATE)


def load_state(path=None):
    path = path or state_path()
    if not os.path.exists(path):
        return {"cards": {}, "sessions": 0}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_state(state, path=None):
    path = path or state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def card_for(state, question_id):
    return state["cards"].get(question_id, {
        "ease": START_EASE, "interval": 0, "reps": 0, "lapses": 0,
        "due": str(date.today()), "history": [],
    })


def due_cards(state, questions, today=None):
    today = str(today or date.today())
    due = []
    for q in questions:
        card = card_for(state, q["id"])
        if card["due"] <= today:
            due.append((q, card))
    # most overdue first, then never-seen cards
    due.sort(key=lambda qc: (qc[1]["due"], -qc[1]["reps"]))
    return due


def fresh_cards(state, questions):
    return [q for q in questions if q["id"] not in state["cards"]]


def grade(state, question_id, score, today=None):
    """Apply one self-grade (0-5) and return the updated card."""
    if not 0 <= score <= 5:
        raise ValueError("grade must be 0-5")
    today = str(today or date.today())
    card = card_for(state, question_id)
    card = dict(card, history=card["history"] + [[today, score]])

    if score < 3:
        card["lapses"] += 1
        card["reps"] = 0
        card["interval"] = 1
        card["ease"] = max(MIN_EASE, card["ease"] - 0.2)
    else:
        card["reps"] += 1
        if card["reps"] == 1:
            card["interval"] = 1
        elif card["reps"] == 2:
            card["interval"] = 3
        else:
            card["interval"] = round(card["interval"] * card["ease"])
        card["ease"] = max(MIN_EASE,
                           card["ease"] + 0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
    card["due"] = str(date.fromisoformat(today) + timedelta(days=card["interval"]))
    state["cards"][question_id] = card
    return card


def stats(state, questions):
    seen = [card_for(state, q["id"]) for q in questions if q["id"] in state["cards"]]
    today = str(date.today())
    mature = [c for c in seen if c["interval"] >= 21]
    return {
        "total": len(questions),
        "seen": len(seen),
        "mature": len(mature),
        "due_today": len([c for c in seen if c["due"] <= today])
        + len([q for q in questions if q["id"] not in state["cards"]]),
        "sessions": state.get("sessions", 0),
        "grades_given": sum(len(c["history"]) for c in seen),
    }
