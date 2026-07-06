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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
