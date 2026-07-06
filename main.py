"""CLI testing ground for PawPal+.

Builds an owner with two pets and a mix of care tasks, then prints today's
schedule to the terminal. Verifies the backend logic end-to-end before it is
wired into the Streamlit UI:

    python main.py
"""

from datetime import date, time

from pawpal_system import Owner, Pet, Priority, Recurrence, Scheduler, Task


def build_demo_owner() -> Owner:
    owner = Owner("Jordan")

    biscuit = Pet("Biscuit", species="dog", breed="Golden Retriever", age_years=3)
    owner.add_task(biscuit, Task("Morning walk", "exercise", 30, Priority.HIGH, preferred_time=time(8, 0)))
    owner.add_task(biscuit, Task("Breakfast", "feeding", 10, Priority.HIGH, preferred_time=time(8, 30)))
    owner.add_task(biscuit, Task("Evening walk", "exercise", 30, Priority.MEDIUM, preferred_time=time(17, 0)))

    mochi = Pet("Mochi", species="cat", breed="Tabby", age_years=5)
    owner.add_task(mochi, Task("Feed Mochi", "feeding", 10, Priority.HIGH, preferred_time=time(9, 0)))
    owner.add_task(mochi, Task("Litter box", "cleaning", 15, Priority.MEDIUM))
    owner.add_task(mochi, Task("Play session", "enrichment", 20, Priority.LOW, preferred_time=time(16, 0)))

    return owner


def main() -> None:
    owner = build_demo_owner()
    today = date.today()
    scheduler = Scheduler(available_minutes=90, day_start=time(8, 0))

    plan = scheduler.plan_for_owner(owner, today)

    print(f"Today's Schedule — {owner.name}'s pets ({today:%A, %B %d})")
    print(f"(budget: {scheduler.available_minutes} min from {scheduler.day_start:%H:%M})\n")
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    main()
