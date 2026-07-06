"""CLI testing ground for PawPal+.

Builds an owner with two pets and a mix of care tasks, then exercises the
scheduling algorithms (sorting, filtering, conflict detection, recurrence) and
prints today's schedule to the terminal:

    python main.py
"""

from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Priority, Recurrence, Scheduler, Task


def build_demo_owner() -> Owner:
    owner = Owner("Jordan")

    biscuit = Pet("Biscuit", species="dog", breed="Golden Retriever", age_years=3)
    # Deliberately added out of time order to show sort_by_time works.
    owner.add_task(biscuit, Task("Evening walk", "exercise", 30, Priority.MEDIUM, preferred_time=time(17, 0)))
    owner.add_task(biscuit, Task("Morning walk", "exercise", 30, Priority.HIGH, preferred_time=time(8, 0)))
    owner.add_task(biscuit, Task("Breakfast", "feeding", 10, Priority.HIGH, preferred_time=time(9, 0)))

    mochi = Pet("Mochi", species="cat", breed="Tabby", age_years=5)
    # Note: same 09:00 preferred time as Biscuit's breakfast -> a conflict.
    owner.add_task(mochi, Task("Feed Mochi", "feeding", 10, Priority.HIGH, preferred_time=time(9, 0)))
    owner.add_task(mochi, Task("Litter box", "cleaning", 15, Priority.MEDIUM))
    owner.add_task(mochi, Task("Play session", "enrichment", 20, Priority.LOW, preferred_time=time(16, 0)))

    return owner


def hr(title: str) -> None:
    print(f"\n{title}\n" + "-" * len(title))


def main() -> None:
    owner = build_demo_owner()
    today = date.today()
    scheduler = Scheduler(available_minutes=90, day_start=time(8, 0))

    # 1. Sorting by time of day (tasks were added out of order).
    hr("All tasks sorted by time")
    for t in scheduler.sort_by_time(owner.all_tasks()):
        when = t.preferred_time.strftime("%H:%M") if t.preferred_time else "  —  "
        print(f"  {when}  {t.title}")

    # 2. Filtering by pet and by completion status.
    hr("Filtering")
    print("  Biscuit's tasks:", [t.title for t in scheduler.filter_by_pet(owner, "Biscuit")])
    incomplete = scheduler.filter_by_status(owner.all_tasks(), completed=False)
    print(f"  Incomplete tasks: {len(incomplete)} of {len(owner.all_tasks())}")

    # 3. Conflict detection (two tasks want 09:00).
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

    # 5. Today's schedule (completed morning walk is now excluded).
    hr(f"Today's Schedule — {owner.name}'s pets ({today:%A, %B %d})")
    print(f"(budget: {scheduler.available_minutes} min from {scheduler.day_start:%H:%M})\n")
    plan = scheduler.plan_for_owner(owner, today)
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    main()
