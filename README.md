# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## ✨ Features

- **Multi-pet management** — one owner can track several pets, each with its own list of care tasks (`Owner`, `Pet`).
- **Rich tasks** — every task carries a title, category, duration, priority, recurrence, and an optional preferred time (`Task`).
- **Priority-first daily planning** — the scheduler places tasks high→low by priority within a fixed time budget, packing in as many as fit and clearly listing what was skipped (`Scheduler.generate_plan`).
- **Sorting** — order tasks by priority for planning, or chronologically by preferred time for a timeline view (`Scheduler.sort_tasks`, `Scheduler.sort_by_time`).
- **Filtering** — narrow tasks by pet or by completion status (`Scheduler.filter_by_pet`, `Scheduler.filter_by_status`).
- **Conflict warnings** — a lightweight check flags tasks that want the exact same time and returns a friendly warning instead of crashing (`Scheduler.find_time_conflicts`).
- **Recurring tasks** — completing a daily or weekly task automatically regenerates its next occurrence (`today + 1 day` / `+ 7 days`); one-off tasks don't repeat (`Task.next_occurrence`, `Pet.complete_task`).
- **Explainable plans** — the app describes *why* the plan looks the way it does, including which tasks were skipped and why (`Scheduler.explain_plan`).
- **Streamlit UI + CLI** — the same logic layer (`pawpal_system.py`) powers both an interactive web app (`app.py`) and a terminal demo (`main.py`).

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

**What the tests cover** (`tests/test_pawpal.py`, 34 tests):

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
collected 34 items

tests/test_pawpal.py ..................................                  [100%]

============================== 34 passed in 0.04s ==============================
```

**Confidence Level: ★★★★☆ (4/5).** The core logic — sorting, filtering, recurrence, budget enforcement, and conflict detection — is well covered and all green. One star withheld because a few deliberate simplifications aren't yet exercised end-to-end (preferred time isn't used for real placement, weekly recurrence assumes a single `day_of_week`, and plans assume a single day that doesn't cross midnight). See `reflection.md` §4 for the edge cases I'd test next.

## 📐 Smarter Scheduling

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

Launch the web app with:

```bash
streamlit run app.py
```

### What the UI lets you do

- **Owner** — set the owner's name, or hit **Reset everything** to start fresh (clears the persisted session state).
- **Add a pet** — enter a name, species, breed, and age; the pet is stored on the `Owner` and persists across reruns.
- **Add a task** — pick which pet it's for, then set title, duration, priority, recurrence (daily/weekly/once), an optional weekly day, and an optional preferred time.
- **Current tasks** — see conflict warnings, filter the list by pet, view tasks sorted chronologically, and **mark a task complete** (recurring tasks regenerate automatically).
- **Build schedule** — choose the day, start time, and available minutes, then generate a prioritized plan with an explanation.

### Example workflow

1. Set the owner name to **Jordan**.
2. Under **Add a pet**, add `Biscuit` (dog).
3. Under **Add a task**, add two tasks for Biscuit — `Morning walk` (30 min, high, preferred **09:00**) and `Breakfast` (10 min, high, preferred **09:00**).
4. In **Current tasks**, a warning appears: *⚠️ Conflict at 09:00: Morning walk, Breakfast* — because both want the same time. The table shows them sorted by time.
5. Expand **Mark a task complete**, complete `Morning walk`; since it's daily, PawPal+ reports the next occurrence is scheduled for tomorrow.
6. Under **Build schedule**, set available minutes to `90` and click **Generate schedule** to see the ordered plan, a "skipped" list if anything didn't fit, and a **Why this plan?** explanation.

### Key Scheduler behaviors shown

- **Sorting** — the current-tasks table is chronological; the generated plan is priority-ordered.
- **Conflict warnings** — surfaced both while editing tasks and when generating a plan.
- **Recurrence** — completing a daily/weekly task creates its next occurrence.
- **Budget + explanation** — tasks that don't fit the available minutes are listed as skipped, and the plan explains itself.

### Sample CLI output (`python main.py`)

```
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

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
