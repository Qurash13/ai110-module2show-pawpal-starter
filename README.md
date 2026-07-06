# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
$ python main.py
Today's Schedule — Jordan's pets (Monday, July 06)
(budget: 90 min from 08:00)

Daily plan:
  08:00 — Morning walk (30 min) [priority: high]
  08:30 — Breakfast (10 min) [priority: high]
  08:40 — Feed Mochi (10 min) [priority: high]
  08:50 — Evening walk (30 min) [priority: medium]
Total: 80 min scheduled across 4 task(s).

Skipped (not enough time):
  - Litter box (15 min) [priority: medium]
  - Play session (20 min) [priority: low]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
$ pytest -q
....................                                                     [100%]
20 passed in 0.05s
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks` | Priority (high→low), then preferred time (set before unset, earlier first), then shortest duration as tiebreak so more tasks fit |
| Filtering | `Scheduler.generate_plan`, `Task.is_due_on` | Tasks not due today are filtered out; tasks that don't fit the time budget go to `DailyPlan.skipped` |
| Conflict handling | `Scheduler.detect_conflicts` | Flags overlapping time slots; greedy back-to-back placement never creates them, so this guards edited/hand-built plans |
| Recurring tasks | `Task.is_due_on`, `Recurrence` | `DAILY`/`ONCE` always due; `WEEKLY` due only on its `day_of_week` |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
