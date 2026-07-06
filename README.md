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

All tasks sorted by time
------------------------
  08:00  Morning walk
  09:00  Breakfast
  09:00  Feed Mochi
  16:00  Play session
  17:00  Evening walk
    —    Litter box

Filtering
---------
  Biscuit's tasks: ['Evening walk', 'Morning walk', 'Breakfast']
  Incomplete tasks: 6 of 6

Conflict detection
------------------
  ⚠️ Conflict at 09:00: Breakfast, Feed Mochi

Recurring tasks
---------------
  Completed 'Morning walk' (daily).
  Auto-created next occurrence due 2026-07-07 (today + 1 day).

Today's Schedule — Jordan's pets (Monday, July 06)
--------------------------------------------------
(budget: 90 min from 08:00)

Daily plan:
  08:00 — Breakfast (10 min) [priority: high]
  08:10 — Feed Mochi (10 min) [priority: high]
  08:20 — Evening walk (30 min) [priority: medium]
  08:50 — Litter box (15 min) [priority: medium]
  09:05 — Play session (20 min) [priority: low]
Total: 85 min scheduled across 5 task(s).
```

## 🧪 Testing PawPal+

Run the full suite from the project root:

```bash
python -m pytest
```

**What the tests cover** (`tests/test_pawpal.py`, 33 tests):

- **Data model** — adding a task increases a pet's task count, `mark_complete()` flips status, `Owner.add_task` registers the pet, and `all_tasks()` spans multiple pets.
- **Sorting correctness** — `sort_by_time` returns tasks in chronological order (untimed last); `sort_tasks` orders by priority with correct tiebreaks and doesn't mutate its input.
- **Filtering** — by completion status and by pet name.
- **Recurrence logic** — completing a daily task creates a new task due the following day (`+1`), weekly `+7`, one-off tasks don't repeat; `due_date` pins an instance to an exact day.
- **Conflict detection** — flags tasks that share the exact same time, and generated plans have no duration overlaps.
- **Scheduling** — back-to-back placement from `day_start`, time-budget enforcement (overflow skipped), and filtering of not-due/completed tasks.
- **Edge cases** — empty task list, a pet with no tasks, and an owner with no pets all plan cleanly instead of crashing.

Sample test output:

```
$ python -m pytest
============================= test session starts ==============================
collected 33 items

tests/test_pawpal.py .................................                   [100%]

============================== 33 passed in 0.08s ==============================
```

**Confidence Level: ★★★★☆ (4/5).** The core logic — sorting, filtering, recurrence, budget enforcement, and conflict detection — is well covered and all green. One star withheld because a few deliberate simplifications aren't yet exercised end-to-end (preferred time isn't used for real placement, weekly recurrence assumes a single `day_of_week`, and plans assume a single day that doesn't cross midnight). See `reflection.md` §4 for the edge cases I'd test next.

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sort by priority | `Scheduler.sort_tasks` | Priority (high→low), then preferred time (set before unset, earlier first), then shortest duration as tiebreak so more tasks fit. Used when building the plan. |
| Sort by time | `Scheduler.sort_by_time` | Orders tasks by `preferred_time` (earliest first); untimed tasks sort last. Used for displaying a timeline view. |
| Filter by status | `Scheduler.filter_by_status` | Returns tasks matching a completion status (e.g., only outstanding tasks). |
| Filter by pet | `Scheduler.filter_by_pet`, `Owner.tasks_for_pet` | Returns the tasks belonging to a named pet. |
| Due / budget filtering | `Scheduler.generate_plan`, `Task.is_due_on` | Tasks not due on the target day (and completed tasks) are filtered out; tasks that don't fit the time budget go to `DailyPlan.skipped`. |
| Conflict detection | `Scheduler.find_time_conflicts` | Lightweight check that returns warning strings when tasks share the exact same `preferred_time` (doesn't crash). `Scheduler.detect_conflicts` additionally flags duration overlaps in a built plan. |
| Recurring tasks | `Task.next_occurrence`, `Pet.complete_task`, `Recurrence` | Completing a `DAILY`/`WEEKLY` task auto-creates its next occurrence (`today + 1 day` / `+ 7 days` via `timedelta`), pinned to that date; `ONCE` tasks don't repeat. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
