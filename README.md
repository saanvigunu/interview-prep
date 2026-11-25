# interview-prep

A spaced-repetition CLI for practicing interview questions. 48 questions
across behavioral, python, data-structures, sql, ml and product - you
answer out loud, grade yourself honestly, and it schedules each card to
come back right before you'd forget it.

I built this because my interview prep was "scroll a giant doc and hope".
What's actually due today, and what I'm about to forget, are better
questions than "what should I read next".

## usage

```bash
python3 -m prep categories              # the six categories
python3 -m prep list --category python  # browse questions
python3 -m prep show ds-001             # one question, with follow-ups
python3 -m prep due                     # what's scheduled today
python3 -m prep practice -n 10          # run a self-graded session
python3 -m prep practice --new -n 5     # only fresh cards
python3 -m prep stats                   # how the deck is going
```

stdlib only, nothing to install. Tests:

```bash
python3 -m unittest discover    # 27 tests, no network
```

## how it works

Each practice question shows the prompt, waits while you answer out loud,
shows two follow-ups an interviewer might ask, then asks for a 0-5 grade:

```
5 instant and solid   4 right, with effort   3 right, barely
2 wrong but familiar  1 wrong, faint memory  0 blank
```

Grades of 3+ pass and stretch the interval (1 day, 3 days, then ease x
interval); grades below 3 reset the card to tomorrow with an ease penalty.
It's a straightforward SM-2 variant - the algorithm SuperMemo published,
same floor of 1.3 on the ease factor.

Progress lives in `~/.local/share/interview-prep/state.json` as plain,
readable JSON (override with `PREP_STATE`). Nothing leaves your machine.

## honesty notes

- Grading is self-grading on purpose. There is no AI judge pretending to
  score your answer; the point is saying it out loud and being honest
  about how it went.
- The questions in `data/questions.json` are hand-written standard
  interview prompts. None of them claims to come from a specific company.
- The scheduler is real SM-2, not a marketing word: the math is in
  `prep/sr.py` with the intervals pinned in `test_sr.py`.
