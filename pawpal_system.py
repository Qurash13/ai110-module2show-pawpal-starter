"""PawPal+ core logic layer.

Implements the data model (Owner, Pet, Task) and the scheduling engine
(Scheduler) that turns a set of care tasks + constraints into an ordered daily
plan. Designed to be driven from a CLI/demo script or the Streamlit UI in
``app.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import Enum, IntEnum
from typing import Optional


class Priority(IntEnum):
    """How important a task is. Higher value sorts first."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Recurrence(str, Enum):
    """How often a task repeats."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


def _add_minutes(start: time, minutes: int) -> time:
    """Return the wall-clock time ``minutes`` after ``start`` (same day)."""
    base = datetime.combine(date.min, start) + timedelta(minutes=minutes)
    return base.time()


@dataclass
class Task:
    """A single unit of pet care (a walk, a feeding, a medication, etc.)."""

    title: str
    category: str = "general"
    duration_minutes: int = 15
    priority: Priority = Priority.MEDIUM
    recurrence: Recurrence = Recurrence.DAILY
    preferred_time: Optional[time] = None
    # Legacy single-day field for WEEKLY tasks: 0 = Monday ... 6 = Sunday.
    day_of_week: Optional[int] = None
    # Preferred way to say "which weekdays": a set of 0=Mon..6=Sun. When set, it
    # defines exactly which days the task is due (e.g. {0, 2, 4} = Mon/Wed/Fri).
    days_of_week: Optional[frozenset[int]] = None
    completed: bool = False
    # Set when a recurring task regenerates: pins the instance to one date.
    due_date: Optional[date] = None

    def mark_complete(self) -> None:
        """Mark this task as done so it drops out of future plans."""
        self.completed = True

    def next_occurrence(self, completed_on: Optional[date] = None) -> Optional[Task]:
        """Return a fresh, uncompleted copy of this task for its next due date.

        ONCE tasks don't repeat and return ``None``. When the task runs on a set
        of weekdays, the next date is the soonest of those weekdays after the
        base date. Otherwise DAILY advances one day and WEEKLY advances seven.
        The base date is this instance's ``due_date`` if set, else ``completed_on``
        (today by default).
        """
        if self.recurrence == Recurrence.ONCE:
            return None
        base = self.due_date or completed_on or date.today()
        if self.days_of_week:
            for offset in range(1, 8):
                candidate = base + timedelta(days=offset)
                if candidate.weekday() in self.days_of_week:
                    return replace(self, completed=False, due_date=candidate)
        step = timedelta(days=1) if self.recurrence == Recurrence.DAILY else timedelta(weeks=1)
        return replace(self, completed=False, due_date=base + step)

    def is_due_on(self, day: date) -> bool:
        """Return True if this task should appear in the plan for ``day``.

        - A task pinned to a ``due_date`` is due only on that exact date.
        - A task with an explicit ``days_of_week`` set is due on those weekdays.
        - Otherwise DAILY and ONCE tasks are always due (a one-off is scheduled
          for whatever day the owner is planning).
        - A WEEKLY task with no day set falls back to its legacy ``day_of_week``
          (Monday if none was set).
        """
        if self.due_date is not None:
            return day == self.due_date
        if self.days_of_week:
            return day.weekday() in self.days_of_week
        if self.recurrence in (Recurrence.DAILY, Recurrence.ONCE):
            return True
        target = self.day_of_week if self.day_of_week is not None else 0
        return day.weekday() == target


@dataclass
class Pet:
    """A pet that care tasks belong to."""

    name: str
    species: str = "dog"
    breed: str = ""
    age_years: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def complete_task(self, task: Task, on_date: Optional[date] = None) -> Optional[Task]:
        """Mark ``task`` done and auto-add its next occurrence if it recurs.

        Returns the newly created follow-up task, or ``None`` for one-off tasks.
        """
        task.mark_complete()
        nxt = task.next_occurrence(on_date)
        if nxt is not None:
            self.add_task(nxt)
        return nxt


@dataclass
class Owner:
    """The person planning care for one or more pets."""

    name: str
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner, ignoring a re-add of the same object.

        Dedupe is by identity, not value, so two distinct pets that happen to
        share a name/species (e.g. two dogs both named "Rex") are both kept.
        """
        if not any(p is pet for p in self.pets):
            self.pets.append(pet)

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a care task to one of the owner's pets, registering it if needed."""
        self.add_pet(pet)
        pet.add_task(task)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return the tasks belonging to the pet(s) with ``pet_name``."""
        return [t for pet in self.pets if pet.name == pet_name for t in pet.tasks]


@dataclass
class ScheduledItem:
    """One task placed at a concrete start/end time in the day's plan."""

    task: Task
    start: time
    end: time


@dataclass
class DailyPlan:
    """The result of scheduling: what got placed, what got skipped."""

    items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)
    total_minutes: int = 0


@dataclass
class Scheduler:
    """Turns a set of tasks + constraints into an ordered daily plan.

    The scheduler places tasks back-to-back starting at ``day_start`` in priority
    order, fitting as many as it can within ``available_minutes``. Tasks that
    don't fit are recorded in ``DailyPlan.skipped`` rather than dropped silently.
    """

    available_minutes: int = 240
    day_start: time = time(8, 0)

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (high first), then preferred time, then
        shortest duration as a tiebreak so more tasks fit."""
        return sorted(
            tasks,
            key=lambda t: (
                -int(t.priority),
                0 if t.preferred_time is not None else 1,
                t.preferred_time or time.min,
                t.duration_minutes,
            ),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by preferred time of day (earliest first).

        Tasks with no preferred time sort to the end. Returns a new list; the
        input is left untouched.
        """
        return sorted(
            tasks,
            key=lambda t: (t.preferred_time is None, t.preferred_time or time.min),
        )

    def filter_by_status(self, tasks: list[Task], completed: bool = False) -> list[Task]:
        """Return only the tasks whose completion status matches ``completed``."""
        return [t for t in tasks if t.completed == completed]

    def filter_by_pet(self, owner: Owner, pet_name: str) -> list[Task]:
        """Return the owner's tasks that belong to the pet named ``pet_name``."""
        return owner.tasks_for_pet(pet_name)

    def find_time_conflicts(self, tasks: list[Task]) -> list[str]:
        """Lightweight conflict check: warn when tasks share a preferred time.

        Returns a list of human-readable warning strings (empty if none) instead
        of raising, so callers can surface the warnings without crashing. Only
        exact ``preferred_time`` matches are flagged; tasks with no preferred
        time are ignored.
        """
        by_time: dict[time, list[str]] = {}
        for task in tasks:
            if task.preferred_time is not None:
                by_time.setdefault(task.preferred_time, []).append(task.title)

        warnings: list[str] = []
        for slot, titles in sorted(by_time.items()):
            if len(titles) > 1:
                warnings.append(
                    f"⚠️ Conflict at {slot.strftime('%H:%M')}: " + ", ".join(titles)
                )
        return warnings

    def generate_plan(self, tasks: list[Task], day: date) -> DailyPlan:
        """Build a daily plan for ``day`` that fits within ``available_minutes``.

        Recurring tasks are filtered via ``Task.is_due_on(day)`` before sorting
        and placement; already-completed tasks are excluded.
        """
        due = [t for t in tasks if t.is_due_on(day) and not t.completed]
        ordered = self.sort_tasks(due)

        plan = DailyPlan()
        cursor = self.day_start
        remaining = self.available_minutes
        for task in ordered:
            if task.duration_minutes <= remaining:
                end = _add_minutes(cursor, task.duration_minutes)
                plan.items.append(ScheduledItem(task=task, start=cursor, end=end))
                cursor = end
                remaining -= task.duration_minutes
                plan.total_minutes += task.duration_minutes
            else:
                plan.skipped.append(task)
        return plan

    def plan_for_owner(self, owner: Owner, day: date) -> DailyPlan:
        """Convenience: gather every task across the owner's pets and plan ``day``."""
        return self.generate_plan(owner.all_tasks(), day)

    def detect_conflicts(self, plan: DailyPlan) -> list[ScheduledItem]:
        """Return scheduled items whose time slots overlap another item.

        The greedy ``generate_plan`` never produces overlaps, but this is a
        general check usable on any hand-built or edited plan.
        """
        ordered = sorted(plan.items, key=lambda i: i.start)
        conflicts: list[ScheduledItem] = []
        for prev, curr in zip(ordered, ordered[1:]):
            if curr.start < prev.end:
                if prev not in conflicts:
                    conflicts.append(prev)
                conflicts.append(curr)
        return conflicts

    def explain_plan(self, plan: DailyPlan) -> str:
        """Produce a human-readable explanation of the plan."""
        lines: list[str] = []
        if plan.items:
            lines.append("Daily plan:")
            for item in plan.items:
                lines.append(
                    f"  {item.start.strftime('%H:%M')} — {item.task.title} "
                    f"({item.task.duration_minutes} min) "
                    f"[priority: {item.task.priority.name.lower()}]"
                )
            lines.append(
                f"Total: {plan.total_minutes} min scheduled "
                f"across {len(plan.items)} task(s)."
            )
        else:
            lines.append("Daily plan: nothing scheduled.")

        if plan.skipped:
            lines.append("")
            lines.append("Skipped (not enough time):")
            for task in plan.skipped:
                lines.append(
                    f"  - {task.title} ({task.duration_minutes} min) "
                    f"[priority: {task.priority.name.lower()}]"
                )
        return "\n".join(lines)
