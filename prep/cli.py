"""interview-prep command line.

    python3 -m prep categories            list the categories
    python3 -m prep list [--category C]   show questions (id + prompt)
    python3 -m prep show <id>             full question with follow-ups
    python3 -m prep due                   what's scheduled today
    python3 -m prep practice [-n N] [--category C] [--new]
                                          run a self-graded session
    python3 -m prep stats                 how the deck is going

Grading is honest self-grading (0-5, printed before each answer) - you
answer out loud, then tell it how it went. Nothing is auto-judged.
"""

import sys

from . import bank, sr

USAGE = __doc__

GRADE_GUIDE = """\
  5 instant and solid   4 right, with effort   3 right, barely
  2 wrong but familiar  1 wrong, faint memory  0 blank"""


def _load():
    return bank.load_bank()


def cmd_categories(args):
    payload = _load()
    counts = {}
    for q in payload["questions"]:
        counts[q["category"]] = counts.get(q["category"], 0) + 1
    for c in bank.categories(payload):
        print(f"{c:<16} {counts.get(c, 0)} questions")


def cmd_list(args):
    payload = _load()
    category = _flag(args, "--category")
    for q in bank.by_category(payload, category):
        print(f"{q['id']:<14} [{q['category']}] {q['question']}")


def cmd_show(args):
    if not args:
        sys.exit("show needs a question id, e.g. `show py-003`")
    payload = _load()
    try:
        q = bank.get(payload, args[0])
    except KeyError:
        sys.exit(f"no question {args[0]!r} (try `list`)")
    print(f"{q['id']}  [{q['category']}]")
    print(q["question"])
    if q.get("why"):
        print(f"\nwhy it matters: {q['why']}")
    if q.get("followups"):
        print("\nfollow-ups to expect:")
        for f in q["followups"]:
            print(f"  - {f}")


def cmd_due(args):
    payload = _load()
    state = sr.load_state()
    due = sr.due_cards(state, payload["questions"])
    if not due:
        print("nothing due right now - `practice --new` to add fresh cards")
        return
    print(f"{len(due)} cards due:")
    for q, card in due:
        label = "new" if q["id"] not in state["cards"] else f"due {card['due']}"
        print(f"  {q['id']:<14} [{q['category']}] {label:<12} {q['question'][:60]}")


def cmd_practice(args):
    payload = _load()
    category = _flag(args, "--category")
    count = int(_flag(args, "-n") or 10)
    questions = bank.by_category(payload, category)
    state = sr.load_state()

    if "--new" in args:
        queue = [(q, sr.card_for(state, q["id"]))
                 for q in sr.fresh_cards(state, questions)]
    else:
        queue = sr.due_cards(state, questions)
    queue = queue[:count]
    if not queue:
        print("nothing due right now - `practice --new` to add fresh cards")
        return

    print(f"{len(queue)} questions. Answer out loud, then grade yourself:")
    print(GRADE_GUIDE)
    state["sessions"] = state.get("sessions", 0) + 1
    graded = 0
    for q, card in queue:
        print(f"\n--- {q['id']} [{q['category']}] ---")
        print(q["question"])
        input("\n(answer out loud, then press enter)")
        if q.get("followups"):
            print("follow-ups an interviewer might ask:")
            for f in q["followups"][:2]:
                print(f"  - {f}")
        while True:
            raw = input("grade 0-5: ").strip()
            if raw.isdigit() and 0 <= int(raw) <= 5:
                break
            print("0-5 only")
        updated = sr.grade(state, q["id"], int(raw))
        print(f"  -> next review {updated['due']} "
              f"(interval {updated['interval']}d, ease {updated['ease']:.2f})")
        graded += 1
    sr.save_state(state)
    print(f"\nsession done: {graded} graded, "
          f"{len(sr.due_cards(state, questions))} still due")


def cmd_stats(args):
    payload = _load()
    s = sr.stats(sr.load_state(), payload["questions"])
    print(f"bank:      {s['total']} questions")
    print(f"seen:      {s['seen']} ({s['mature']} mature, interval 21d+)")
    print(f"due today: {s['due_today']} (new cards count as due)")
    print(f"sessions:  {s['sessions']}, grades given: {s['grades_given']}")


def _flag(args, name):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args) and not args[i + 1].startswith("-"):
            return args[i + 1]
        return ""
    return None


COMMANDS = {"categories": cmd_categories, "list": cmd_list, "show": cmd_show,
            "due": cmd_due, "practice": cmd_practice, "stats": cmd_stats}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd = COMMANDS.get(argv[0])
    if cmd is None:
        print(USAGE, file=sys.stderr)
        return 2
    cmd(argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
