"""Tests for the PawPal+ core logic layer.

Covers the behaviors that matter most: the required completion/task-count
checks, plus recurrence filtering, priority ordering, time-budget enforcement,
conflict detection, and explanations.
"""

from datetime import date, time, timedelta

from pawpal_system import (
    DailyPlan,
    Owner,
    Pet,
    Priority,
    Recurrence,
    ScheduledItem,
    Scheduler,
    Task,
)

# A Wednesday and a Monday, for weekly-recurrence tests.
WEDNESDAY = date(2026, 7, 8)
MONDAY = date(2026, 7, 6)


# --- Required Phase 2 tests ------------------------------------------------


def test_mark_complete_changes_status():
    task = Task("Walk")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Biscuit")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Walk"))
    assert len(pet.tasks) == 1


# --- Data model ------------------------------------------------------------


def test_owner_add_task_registers_pet_and_task():
    owner = Owner("Jordan")
    pet = Pet("Mochi", species="cat")
    task = Task("Feeding")

    owner.add_task(pet, task)

    assert pet in owner.pets
    assert owner.all_tasks() == [task]


def test_add_pet_is_idempotent():
    owner = Owner("Jordan")
    pet = Pet("Mochi")
    owner.add_pet(pet)
    owner.add_pet(pet)
    assert owner.pets == [pet]


def test_add_pet_keeps_distinct_pets_with_equal_fields():
    # Two different pets that happen to share a name/species must both be kept.
    owner = Owner("Jordan")
    owner.add_pet(Pet("Rex"))
    owner.add_pet(Pet("Rex"))
    assert len(owner.pets) == 2


def test_all_tasks_spans_multiple_pets():
    owner = Owner("Jordan")
    dog, cat = Pet("Biscuit"), Pet("Mochi")
    owner.add_task(dog, Task("Walk"))
    owner.add_task(cat, Task("Litter"))
    assert len(owner.all_tasks()) == 2


def test_pet_with_no_tasks_is_handled():
    # Edge case: an owner with a pet but no tasks should plan cleanly, not crash.
    owner = Owner("Jordan")
    owner.add_pet(Pet("Biscuit"))
    assert owner.all_tasks() == []
    plan = Scheduler().plan_for_owner(owner, WEDNESDAY)
    assert plan.items == [] and plan.total_minutes == 0


def test_owner_with_no_pets_plans_cleanly():
    plan = Scheduler().plan_for_owner(Owner("Jordan"), WEDNESDAY)
    assert plan.items == [] and plan.skipped == []


# --- Recurrence ------------------------------------------------------------


def test_daily_and_once_always_due():
    assert Task("Walk", recurrence=Recurrence.DAILY).is_due_on(WEDNESDAY)
    assert Task("Vet", recurrence=Recurrence.ONCE).is_due_on(WEDNESDAY)


def test_weekly_due_only_on_matching_weekday():
    # day_of_week defaults to Monday (0)
    weekly = Task("Bath", recurrence=Recurrence.WEEKLY)
    assert weekly.is_due_on(MONDAY)
    assert not weekly.is_due_on(WEDNESDAY)


def test_weekly_respects_explicit_day_of_week():
    weekly = Task("Nail trim", recurrence=Recurrence.WEEKLY, day_of_week=2)  # Wed
    assert weekly.is_due_on(WEDNESDAY)
    assert not weekly.is_due_on(MONDAY)


# --- Sorting ---------------------------------------------------------------


def test_sort_orders_by_priority_high_first():
    low = Task("A", priority=Priority.LOW)
    high = Task("B", priority=Priority.HIGH)
    med = Task("C", priority=Priority.MEDIUM)
    ordered = Scheduler().sort_tasks([low, high, med])
    assert [t.priority for t in ordered] == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


def test_sort_tiebreaks_by_preferred_time_then_duration():
    early = Task("early", priority=Priority.HIGH, preferred_time=time(7, 0))
    late = Task("late", priority=Priority.HIGH, preferred_time=time(9, 0))
    no_time_short = Task("short", priority=Priority.HIGH, duration_minutes=5)
    ordered = Scheduler().sort_tasks([no_time_short, late, early])
    # Tasks with a preferred time come before those without; earlier first.
    assert [t.title for t in ordered] == ["early", "late", "short"]


def test_sort_does_not_mutate_input():
    tasks = [Task("A", priority=Priority.LOW), Task("B", priority=Priority.HIGH)]
    Scheduler().sort_tasks(tasks)
    assert [t.title for t in tasks] == ["A", "B"]


# --- Plan generation -------------------------------------------------------


def test_plan_places_tasks_back_to_back_from_day_start():
    sched = Scheduler(available_minutes=240, day_start=time(8, 0))
    plan = sched.generate_plan(
        [
            Task("Walk", duration_minutes=30, priority=Priority.HIGH),
            Task("Feed", duration_minutes=10, priority=Priority.MEDIUM),
        ],
        WEDNESDAY,
    )
    assert plan.items[0].start == time(8, 0)
    assert plan.items[0].end == time(8, 30)
    assert plan.items[1].start == time(8, 30)
    assert plan.items[1].end == time(8, 40)
    assert plan.total_minutes == 40


def test_plan_respects_time_budget_and_skips_overflow():
    sched = Scheduler(available_minutes=30)
    high = Task("Meds", duration_minutes=20, priority=Priority.HIGH)
    low = Task("Long enrichment", duration_minutes=20, priority=Priority.LOW)
    plan = sched.generate_plan([low, high], WEDNESDAY)
    # High priority fits first; the low-priority one no longer fits.
    assert [i.task.title for i in plan.items] == ["Meds"]
    assert low in plan.skipped
    assert plan.total_minutes == 20


def test_plan_filters_tasks_not_due():
    sched = Scheduler()
    weekly_wrong_day = Task("Bath", recurrence=Recurrence.WEEKLY, day_of_week=2)
    plan = sched.generate_plan([weekly_wrong_day], MONDAY)
    assert plan.items == []
    assert plan.skipped == []  # filtered out entirely, not "skipped for time"


def test_plan_excludes_completed_tasks():
    sched = Scheduler()
    done = Task("Walk", duration_minutes=15)
    done.mark_complete()
    plan = sched.generate_plan([done], WEDNESDAY)
    assert plan.items == [] and plan.skipped == []


def test_empty_task_list_yields_empty_plan():
    plan = Scheduler().generate_plan([], WEDNESDAY)
    assert plan.items == [] and plan.skipped == [] and plan.total_minutes == 0


def test_plan_for_owner_gathers_all_pets():
    owner = Owner("Jordan")
    owner.add_task(Pet("Biscuit"), Task("Walk", duration_minutes=15))
    owner.add_task(Pet("Mochi"), Task("Feed", duration_minutes=10))
    plan = Scheduler().plan_for_owner(owner, WEDNESDAY)
    assert len(plan.items) == 2


# --- Sort by time / filtering (Phase 4) ------------------------------------


def test_sort_by_time_orders_earliest_first_with_untimed_last():
    a = Task("late", preferred_time=time(17, 0))
    b = Task("early", preferred_time=time(8, 0))
    c = Task("untimed")
    ordered = Scheduler().sort_by_time([a, c, b])
    assert [t.title for t in ordered] == ["early", "late", "untimed"]


def test_filter_by_status():
    done = Task("done")
    done.mark_complete()
    todo = Task("todo")
    sched = Scheduler()
    assert sched.filter_by_status([done, todo], completed=False) == [todo]
    assert sched.filter_by_status([done, todo], completed=True) == [done]


def test_filter_by_pet():
    owner = Owner("Jordan")
    owner.add_task(Pet("Biscuit"), Task("Walk"))
    owner.add_task(Pet("Mochi"), Task("Litter"))
    tasks = Scheduler().filter_by_pet(owner, "Mochi")
    assert [t.title for t in tasks] == ["Litter"]


# --- Time-conflict warnings (Phase 4) --------------------------------------


def test_find_time_conflicts_warns_on_same_time():
    tasks = [
        Task("Breakfast", preferred_time=time(9, 0)),
        Task("Feed cat", preferred_time=time(9, 0)),
        Task("Walk", preferred_time=time(8, 0)),
    ]
    warnings = Scheduler().find_time_conflicts(tasks)
    assert len(warnings) == 1
    assert "09:00" in warnings[0]
    assert "Breakfast" in warnings[0] and "Feed cat" in warnings[0]


def test_find_time_conflicts_empty_when_none():
    tasks = [Task("A", preferred_time=time(8, 0)), Task("B", preferred_time=time(9, 0)), Task("C")]
    assert Scheduler().find_time_conflicts(tasks) == []


# --- Recurring task regeneration (Phase 4) ---------------------------------


def test_next_occurrence_daily_advances_one_day():
    nxt = Task("Walk", recurrence=Recurrence.DAILY).next_occurrence(MONDAY)
    assert nxt is not None
    assert nxt.due_date == MONDAY + timedelta(days=1)
    assert nxt.completed is False


def test_next_occurrence_weekly_advances_seven_days():
    nxt = Task("Bath", recurrence=Recurrence.WEEKLY).next_occurrence(MONDAY)
    assert nxt.due_date == MONDAY + timedelta(weeks=1)


def test_next_occurrence_once_returns_none():
    assert Task("Vet", recurrence=Recurrence.ONCE).next_occurrence(MONDAY) is None


def test_complete_task_marks_done_and_adds_next():
    pet = Pet("Biscuit")
    walk = Task("Walk", recurrence=Recurrence.DAILY)
    pet.add_task(walk)
    follow_up = pet.complete_task(walk, on_date=MONDAY)

    assert walk.completed is True
    assert follow_up in pet.tasks
    assert follow_up.due_date == MONDAY + timedelta(days=1)
    assert len(pet.tasks) == 2


def test_complete_once_task_adds_nothing():
    pet = Pet("Biscuit")
    vet = Task("Vet", recurrence=Recurrence.ONCE)
    pet.add_task(vet)
    assert pet.complete_task(vet, on_date=MONDAY) is None
    assert len(pet.tasks) == 1


def test_due_date_pins_task_to_exact_day():
    task = Task("Walk", recurrence=Recurrence.DAILY, due_date=WEDNESDAY)
    assert task.is_due_on(WEDNESDAY)
    assert not task.is_due_on(MONDAY)


# --- Conflict detection ----------------------------------------------------


def test_detect_conflicts_finds_overlap():
    a = ScheduledItem(Task("A"), time(8, 0), time(8, 30))
    b = ScheduledItem(Task("B"), time(8, 15), time(8, 45))  # overlaps A
    conflicts = Scheduler().detect_conflicts(DailyPlan(items=[a, b]))
    assert a in conflicts and b in conflicts


def test_generated_plan_has_no_conflicts():
    sched = Scheduler()
    plan = sched.generate_plan(
        [Task("A", duration_minutes=30), Task("B", duration_minutes=30)], WEDNESDAY
    )
    assert sched.detect_conflicts(plan) == []


# --- Explanation -----------------------------------------------------------


def test_explain_plan_lists_scheduled_and_skipped():
    sched = Scheduler(available_minutes=15)
    plan = sched.generate_plan(
        [
            Task("Walk", duration_minutes=15, priority=Priority.HIGH),
            Task("Groom", duration_minutes=30, priority=Priority.LOW),
        ],
        WEDNESDAY,
    )
    text = sched.explain_plan(plan)
    assert "Walk" in text
    assert "Skipped" in text and "Groom" in text
    assert "08:00" in text
