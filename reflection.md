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

I used an AI coding assistant across every phase, but for different kinds of work:

- **Design brainstorming** — early on, to turn the scenario into a set of classes and a Mermaid UML diagram, and to sanity-check relationships ("does an Owner *have* Pets, or should the Scheduler own them?").
- **Scaffolding** — generating the dataclass skeletons and empty method stubs from the UML so I had a consistent starting structure.
- **Implementation** — fleshing out the scheduling algorithms (sorting keys, the greedy time-budget loop, `timedelta`-based recurrence) with the assistant's editing/agent mode.
- **Testing** — drafting the pytest suite, including edge cases I might not have thought of (a pet with no tasks, two tasks at the same time).
- **Documentation** — drafting docstrings, the README Features/Smarter Scheduling tables, and this reflection.

The most helpful prompts were **specific and grounded in my files** — e.g., "based on my skeletons, how should the Scheduler retrieve tasks from the Owner's pets?" and "what edge cases matter for a scheduler with sorting and recurrence?" Open-ended prompts ("write my scheduler") produced generic code; scoped prompts that referenced my actual class names produced code that fit the design.

**b. Judgment and verification**

The clearest example of *not* accepting a suggestion as-is came with recurring tasks. The assignment's model assumed each task carried an explicit due date, but my design already used a `Recurrence` enum plus `is_due_on()`. A naive merge would have created two competing ways to decide whether a task is "due." Instead of accepting that, I kept `is_due_on` as the single source of truth and had `due_date` act as an optional override that `is_due_on` checks first — so regenerated recurring instances pin to a date without breaking the existing recurrence rules (or the tests that covered them).

I also rejected a suggested `main.py` ordering that assumed tasks were added in time order; my sort tiebreak (shortest-duration-first) actually reordered them, so a test assertion failed. I verified which side was wrong by reading the failure, confirmed the *code* was behaving correctly and the *test's assumption* was wrong, and fixed the test rather than the logic.

I verified AI output three ways throughout: running `python -m pytest` after every change, running `python main.py` to eyeball realistic output, and driving the Streamlit UI headlessly with `AppTest` to confirm the full add-pet → add-task → generate flow ran without exceptions.

---

## 4. Testing and Verification

**a. What you tested**

The test suite in `tests/test_pawpal.py` (33 tests) covers the behaviors most likely to break the app if they were wrong:

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

I'm most satisfied with the clean separation between the logic layer (`pawpal_system.py`) and the two front-ends (`main.py` CLI and `app.py` Streamlit). Building and verifying the "brain" first, CLI-first, meant that by the time I wired up the UI, the hard part was already tested — the UI just calls `Scheduler` methods and renders results. That separation also made the whole thing testable: 33 pytest cases run in a fraction of a second because they exercise plain Python objects, not the UI.

**b. What you would improve**

The scheduler's handling of *time* is the weakest area. Right now `preferred_time` only affects ordering, not actual placement, and conflict detection only catches exact same-time matches, not duration overlaps. In another iteration I'd make the scheduler slot-aware: honor preferred times as real bookings, use the existing `detect_conflicts` (duration overlap) logic at the task level, and handle plans that cross midnight. I'd also add persistence so an owner's pets/tasks survive between sessions instead of living only in `st.session_state`.

**c. Key takeaway**

The biggest lesson was what it actually means to be the "lead architect" with a powerful AI: the AI is fast at *producing* code, but it doesn't own the *design*. It will happily follow a prompt into an inconsistent model (like two competing ways to decide if a task is due) because it optimizes for the local request, not the coherence of the whole system. My job was to hold the design in my head, reject or reshape suggestions that didn't fit it, and verify every change with tests I could reason about. AI made me much faster, but the judgment about *what "good" looks like* had to stay human.

**Using separate chat sessions per phase** helped keep that judgment focused — a fresh session for testing, for example, meant the assistant wasn't anchored on the implementation choices from an earlier conversation and could think about edge cases with fresh eyes, while I carried the through-line of the design across all of them.
