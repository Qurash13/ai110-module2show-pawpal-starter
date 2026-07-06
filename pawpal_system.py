"""PawPal+ core logic layer.

Implements the data model (Owner, Pet, Task) and the scheduling engine
(Scheduler) that turns a set of care tasks + constraints into an ordered daily
plan. Designed to be driven from a CLI/demo script or the Streamlit UI in
``app.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    # Only used for WEEKLY tasks: 0 = Monday ... 6 = Sunday. Defaults to Monday.
    day_of_week: Optional[int] = None
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done so it drops out of future plans."""
        self.completed = True

    def is_due_on(self, day: date) -> bool:
        """Return True if this task should appear in the plan for ``day``.

        - DAILY and ONCE tasks are always due (a one-off is scheduled for the
          day the owner is planning).
        - WEEKLY tasks are due only when ``day`` falls on ``day_of_week``
          (Monday if none was set).
        """
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


@dataclass
class Owner:
    """The person planning care for one or more pets."""

    name: str
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner (idempotent)."""
        if pet not in self.pets:
            self.pets.append(pet)

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a care task to one of the owner's pets, registering it if needed."""
        self.add_pet(pet)
        pet.add_task(task)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


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
