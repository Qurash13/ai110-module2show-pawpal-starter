# PawPal+ Project Reflection

## 1. System Design

**Three core actions a user can perform**

1. **Add a pet** — enter an owner and register a pet (name, species, breed, age) so tasks have something to belong to.
2. **Add a care task** — schedule a walk, feeding, medication, etc. for a pet, giving it a duration and a priority (and optionally a preferred time and how often it repeats).
3. **Generate today's plan** — build an ordered daily schedule that fits the owner's available time, then see the plan and an explanation of why each task was chosen and placed where it was.

**a. Initial design**

I split the system into four core classes plus a couple of small supporting types:

- **Owner** — the person doing the planning. Holds their name, preferences, and the list of pets they own. Acts as the entry point for adding pets/tasks and for gathering every task across all pets (`all_tasks()`).
- **Pet** — a pet that tasks belong to. Holds basic info (name, species, breed, age) and its own list of `Task`s. A dataclass, since it's mostly a data container with `add_task()`.
- **Task** — one unit of pet care (walk, feeding, meds). Holds a title, category, duration, `Priority`, `Recurrence`, and an optional preferred time. A dataclass with `is_due_on(day)` to decide whether it belongs in a given day's plan. `Priority` and `Recurrence` are enums so the values are constrained and sortable.
- **Scheduler** — the algorithmic core. It knows the day's constraints (`available_minutes`, `day_start`) and is responsible for `sort_tasks()`, `detect_conflicts()`, `generate_plan()`, and `explain_plan()`. Keeping this separate from the data classes means the scheduling logic can be tested and swapped independently.
- **ScheduledItem / DailyPlan** — small result types. `ScheduledItem` wraps a `Task` with a concrete start/end time; `DailyPlan` collects the placed items, any skipped tasks, and total minutes used. Making the plan its own object (rather than a raw list) leaves room to explain what was left out and why.

Relationships: an Owner owns many Pets, a Pet has many Tasks, and the Scheduler consumes Tasks and produces a DailyPlan of ScheduledItems. Kept deliberately simple — no calendar/persistence layer yet.

**b. Design changes**

Reviewing the skeleton surfaced one gap in the scheduler's interface: `Task` has an `is_due_on(day)` method for handling recurrence, but `Scheduler.generate_plan(tasks)` originally took no date, so it had no `day` value to pass in. A plan is always *for a specific day*, so I changed the signature to `generate_plan(tasks, day)` and updated the UML to match. Without this, recurring tasks (daily vs. weekly) couldn't be filtered correctly before scheduling.

One thing I considered but deliberately did **not** change: adding a back-reference from `Task` to its `Pet`. It would make explanations easier ("walk *for Mochi*"), but it couples the data classes and risks a circular structure. For now the pet context can be passed in where needed, keeping `Task` decoupled. I'll revisit this in Phase 6 if the explanation logic actually needs it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler considers four things when building a day's plan:

- **A time budget** — `Scheduler.available_minutes`, the total time the owner has. Tasks are placed only while there's room left; anything that doesn't fit goes into `DailyPlan.skipped` instead of being dropped silently.
- **Priority** — the primary sort key. `HIGH` tasks are placed before `MEDIUM`, which come before `LOW`, so the most important care always claims the limited time first.
- **Preferred time** — a soft signal used as a tiebreak within a priority level: tasks that have a preferred time are ordered before those without, earliest first.
- **Recurrence and completion** — before anything is scheduled, tasks that aren't due today (`Task.is_due_on`) and tasks already marked complete are filtered out.

I decided priority mattered most because the scenario is explicitly about a *busy* owner who can't do everything — when time is scarce, the guarantee that matters is "the important stuff happens." Time budget is the hard constraint that makes that decision necessary in the first place; preferred time is genuinely nice-to-have, so I demoted it to a tiebreak rather than letting it override importance.

**b. Tradeoffs**

The biggest tradeoff is that the scheduler places tasks **back-to-back starting at `day_start` in priority order, and does not honor `preferred_time` as an actual placement slot** — it only uses it for ordering. So a task with a preferred time of 5:00 PM might be scheduled at 8:40 AM if that's where it falls in the sorted list.

This is reasonable for the scenario because the primary goal is deciding *what* gets done with limited time and *in what order of importance*, not producing a minute-perfect calendar. Back-to-back placement also means the plan is guaranteed conflict-free by construction (no overlaps to resolve), which keeps the logic simple and predictable. Honoring fixed time slots would introduce gaps, conflicts, and a much harder packing problem — a worthwhile future iteration, but not what this scenario needs first. (`detect_conflicts` already exists so a future slot-aware version can be validated.)

A second, related tradeoff is in conflict detection. `Scheduler.find_time_conflicts` only flags tasks that share the **exact same `preferred_time`** (e.g., two tasks both at 09:00). It does *not* detect overlaps caused by duration — a 30-minute task at 09:00 and another at 09:15 don't share a start time, so they aren't flagged even though they'd collide on a real calendar. I kept the exact-match version because it's cheap (one pass, group by start time), easy to read, and matches how the preferred-time field is actually used here (a rough "when I'd like this to happen" hint, not a booked slot). Duration-aware overlap detection already exists for *scheduled* items in `detect_conflicts`; if preferred times ever became hard bookings, I'd promote that logic into the task-level check too.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

The test suite in `tests/test_pawpal.py` (20 tests) covers the behaviors most likely to break the app if they were wrong:

- **Data model** — `mark_complete()` flips a task's status, adding a task increases a pet's task count, `Owner.add_task` registers the pet, `all_tasks()` spans multiple pets, and `add_pet` is idempotent.
- **Recurrence filtering** — daily/once tasks are always due; weekly tasks are due only on their `day_of_week`.
- **Sorting** — priority (high first) with correct preferred-time/duration tiebreaks, and that sorting doesn't mutate the caller's list.
- **Plan generation** — tasks are placed back-to-back from `day_start`, the time budget is respected (overflow tasks are skipped), and not-due/completed tasks are filtered out entirely.
- **Conflict detection** — overlaps are caught, and a normally generated plan has none.
- **Explanation** — the output lists both scheduled and skipped tasks.

These matter because the scheduler's correctness is what the whole app rests on — if priority ordering or the time budget were wrong, the owner would get a plan that quietly does the wrong things, and that's hard to notice by eye. I verified the behavior end-to-end two ways: `python main.py` for a realistic CLI run, and Streamlit's `AppTest` harness to confirm the UI's generate flow runs without errors.

**b. Confidence**

I'm fairly confident in the core logic: the ordering, budget enforcement, recurrence, and completion filtering are all covered by tests and match the CLI/UI output I've eyeballed. My confidence is lower on the parts I deliberately kept simple — preferred time isn't used for real placement, and weekly recurrence assumes a single `day_of_week`.

Edge cases I'd test next with more time: tasks whose duration exceeds the entire budget, a preferred time that falls before `day_start`, plans that would run past midnight (the current time math assumes a single day), and multiple pets competing for the same scarce budget to confirm priority still wins across pets.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
