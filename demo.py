"""CLI demo for PawPal+.

Builds a sample owner/pet with a realistic mix of care tasks, generates a plan
for today, and prints the explanation. Run before touching the UI to verify the
backend logic works end-to-end:

    python demo.py
"""

from datetime import date, time

from pawpal_system import Owner, Pet, Priority, Recurrence, Scheduler, Task


def build_demo_owner() -> Owner:
    owner = Owner("Jordan")
    biscuit = Pet("Biscuit", species="dog", breed="Golden Retriever", age_years=3)
    owner.add_task(biscuit, Task("Morning walk", "exercise", 30, Priority.HIGH, preferred_time=time(8, 0)))
    owner.add_task(biscuit, Task("Breakfast", "feeding", 10, Priority.HIGH, preferred_time=time(8, 30)))
    owner.add_task(biscuit, Task("Joint medication", "meds", 5, Priority.HIGH))
    owner.add_task(biscuit, Task("Midday enrichment", "enrichment", 20, Priority.MEDIUM))
    owner.add_task(biscuit, Task("Evening walk", "exercise", 30, Priority.MEDIUM))
    owner.add_task(biscuit, Task("Weekly bath", "grooming", 45, Priority.LOW, Recurrence.WEEKLY, day_of_week=0))
    return owner


def main() -> None:
    owner = build_demo_owner()
    today = date.today()
    scheduler = Scheduler(available_minutes=90, day_start=time(8, 0))

    plan = scheduler.generate_plan(owner.all_tasks(), today)

    print(f"PawPal+ — plan for {owner.name}'s pets on {today:%A, %B %d}")
    print(f"(budget: {scheduler.available_minutes} min from {scheduler.day_start:%H:%M})\n")
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    main()
