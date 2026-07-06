"""PawPal+ core logic layer.

Phase 1 skeleton: class definitions, attributes, and empty method stubs derived
from ``diagrams/uml.mmd``. No scheduling logic is implemented yet — method bodies
raise ``NotImplementedError`` so that unfinished behavior fails loudly instead of
silently returning ``None``. Logic is filled in during later phases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
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


@dataclass
class Task:
    """A single unit of pet care (a walk, a feeding, a medication, etc.)."""

    title: str
    category: str = "general"
    duration_minutes: int = 15
    priority: Priority = Priority.MEDIUM
    recurrence: Recurrence = Recurrence.DAILY
    preferred_time: Optional[time] = None

    def is_due_on(self, day: date) -> bool:
        """Return True if this task should appear in the plan for ``day``."""
        raise NotImplementedError


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
        raise NotImplementedError


@dataclass
class Owner:
    """The person planning care for one or more pets."""

    name: str
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        raise NotImplementedError

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a care task to one of the owner's pets."""
        raise NotImplementedError

    def all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        raise NotImplementedError


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
    """Turns a set of tasks + constraints into an ordered daily plan."""

    available_minutes: int = 240
    day_start: time = time(8, 0)

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks (e.g., by priority, then duration/preferred time)."""
        raise NotImplementedError

    def detect_conflicts(self, plan: DailyPlan) -> list[ScheduledItem]:
        """Return scheduled items whose time slots overlap."""
        raise NotImplementedError

    def generate_plan(self, tasks: list[Task], day: date) -> DailyPlan:
        """Build a daily plan for ``day`` that fits within ``available_minutes``.

        ``day`` is needed so recurring tasks can be filtered via
        ``Task.is_due_on(day)`` before sorting and placement.
        """
        raise NotImplementedError

    def explain_plan(self, plan: DailyPlan) -> str:
        """Produce a human-readable explanation of why the plan looks as it does."""
        raise NotImplementedError
