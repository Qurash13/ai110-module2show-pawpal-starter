"""CLI testing ground for PawPal+.

Builds an owner with two pets and a mix of care tasks, then exercises the
scheduling algorithms (priority sorting, filtering, conflict detection,
recurrence) and prints a professionally formatted schedule to the terminal:

    python main.py
"""

from datetime import date, time

from tabulate import tabulate

from pawpal_system import Owner, Pet, Priority, Recurrence, Scheduler, Task

# --- Output formatting helpers (Challenge 4) -------------------------------
# Emoji per task category and a colored dot per priority level so the CLI
# output is scannable at a glance.
CATEGORY_EMOJI = {
    "exercise": "🐕",
    "feeding": "🍽️",
    "meds": "💊",
    "grooming": "🛁",
    "enrichment": "🧸",
    "cleaning": "🧹",
    "general": "📌",
}
PRIORITY_BADGE = {
    Priority.HIGH: "🔴 High",
    Priority.MEDIUM: "🟡 Medium",
    Priority.LOW: "🟢 Low",
}


def task_label(task: Task) -> str:
    """Task title prefixed with an emoji for its category."""
    return f"{CATEGORY_EMOJI.get(task.category, '📌')} {task.title}"


def build_demo_owner() -> Owner:
    owner = Owner("Jordan")

    biscuit = Pet("Biscuit", species="dog", breed="Golden Retriever", age_years=3)
    # Deliberately added out of time/priority order to show sorting works.
    owner.add_task(biscuit, Task("Evening walk", "exercise", 30, Priority.MEDIUM, preferred_time=time(17, 0)))
    owner.add_task(biscuit, Task("Morning walk", "exercise", 30, Priority.HIGH, preferred_time=time(8, 0)))
    owner.add_task(biscuit, Task("Breakfast", "feeding", 10, Priority.HIGH, preferred_time=time(9, 0)))

    mochi = Pet("Mochi", species="cat", breed="Tabby", age_years=5)
    # Multi-time feeding: the same task added once at two times of day. Note the
    # 09:00 feeding also clashes with Biscuit's breakfast -> a conflict.
    for feed_time in (time(9, 0), time(17, 0)):
        owner.add_task(mochi, Task("Feed Mochi", "feeding", 10, Priority.HIGH, preferred_time=feed_time))
    owner.add_task(mochi, Task("Litter box", "cleaning", 15, Priority.MEDIUM))
    owner.add_task(mochi, Task("Play session", "enrichment", 20, Priority.LOW, preferred_time=time(16, 0)))

    return owner


def hr(title: str) -> None:
    print(f"\n{title}\n" + "-" * len(title))


def main() -> None:
    owner = build_demo_owner()
    today = date.today()
    scheduler = Scheduler(available_minutes=90, day_start=time(8, 0))

    # 1. Priority scheduling (Challenge 3): priority first, then time of day.
    #    "Morning walk" (high, 08:00) beats "Breakfast"/"Feed Mochi" (high, later),
    #    and all high-priority tasks come before medium, then low.
    hr("Tasks ordered by priority, then time")
    prio_rows = [
        [PRIORITY_BADGE[t.priority],
         t.preferred_time.strftime("%H:%M") if t.preferred_time else "—",
         task_label(t)]
        for t in scheduler.sort_tasks(owner.all_tasks())
    ]
    print(tabulate(prio_rows, headers=["Priority", "Time", "Task"], tablefmt="rounded_outline"))

    # 2. Filtering by pet and by completion status.
    hr("Filtering")
    print("  Biscuit's tasks:", [t.title for t in scheduler.filter_by_pet(owner, "Biscuit")])
    incomplete = scheduler.filter_by_status(owner.all_tasks(), completed=False)
    print(f"  Incomplete tasks: {len(incomplete)} of {len(owner.all_tasks())}")

    # 3. Conflict detection (two tasks want the same time).
    hr("Conflict detection")
    conflicts = scheduler.find_time_conflicts(owner.all_tasks())
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No time conflicts found.")

    # 4. Recurring tasks: completing a daily task spawns tomorrow's instance.
    hr("Recurring tasks")
    biscuit = owner.pets[0]
    morning_walk = next(t for t in biscuit.tasks if t.title == "Morning walk")
    follow_up = biscuit.complete_task(morning_walk, on_date=today)
    print(f"  Completed '{morning_walk.title}' (daily).")
    if follow_up:
        print(f"  Auto-created next occurrence due {follow_up.due_date} "
              f"(today + {(follow_up.due_date - today).days} day).")

    # 5. Today's schedule as a formatted table (Challenge 4). The completed
    #    morning walk is now excluded; tasks are placed in priority order.
    hr(f"Today's Schedule — {owner.name}'s pets ({today:%A, %B %d})")
    print(f"(budget: {scheduler.available_minutes} min from {scheduler.day_start:%H:%M})\n")
    plan = scheduler.plan_for_owner(owner, today)

    if plan.items:
        rows = [
            [f"{item.start:%H:%M}–{item.end:%H:%M}",
             task_label(item.task),
             f"{item.task.duration_minutes} min",
             PRIORITY_BADGE[item.task.priority]]
            for item in plan.items
        ]
        print(tabulate(rows, headers=["When", "Task", "Length", "Priority"], tablefmt="rounded_outline"))
        print(f"\n✅ {plan.total_minutes} min scheduled across {len(plan.items)} task(s).")
    else:
        print("Nothing could be scheduled.")

    if plan.skipped:
        print("\n⏭️  Skipped (not enough time):")
        for t in plan.skipped:
            print(f"   {task_label(t)} — {t.duration_minutes} min ({PRIORITY_BADGE[t.priority]})")


if __name__ == "__main__":
    main()
