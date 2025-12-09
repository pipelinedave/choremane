"""
Business logic services for the Choremane backend.

This module contains pure functions for business logic that can be easily unit tested.
"""

from datetime import datetime
from typing import List, Tuple, Optional


def calculate_single_chore_score(
    due_date: datetime,
    interval_days: int,
    now: Optional[datetime] = None,
) -> float:
    """
    Calculate the health score for a single chore.

    Args:
        due_date: The due date of the chore (as datetime).
        interval_days: The interval in days for the chore.
        now: The current datetime. Defaults to datetime.now().

    Returns:
        A score from 0-100:
        - Fresh (0-50% elapsed): 100
        - Standard (50-100% elapsed): Decays 100 -> 80
        - Overdue (>100% elapsed): Decays 80 -> 0 based on overdue amount
    """
    if now is None:
        now = datetime.now()

    interval_ms = interval_days * 24 * 60 * 60 * 1000
    diff = now - due_date
    diff_ms = diff.total_seconds() * 1000

    score = 100.0

    if diff_ms > 0:
        # OVERDUE
        overdue_ratio = diff_ms / interval_ms
        # Decay 80 -> 0
        score = max(0, 80 - (overdue_ratio * 80))
    else:
        # NOT OVERDUE (Fresh to Standard)
        # diff_ms is negative
        time_until_due = -diff_ms
        fraction_elapsed = 1 - (time_until_due / interval_ms)

        safe_fraction = max(0, min(1, fraction_elapsed))

        if safe_fraction <= 0.5:
            score = 100
        else:
            # 0.5 -> 1.0 maps to 100 -> 80
            score = 100 + ((safe_fraction - 0.5) * -40)

    return score


def normalize_due_date(due_date) -> datetime:
    """
    Normalize a due_date to a datetime object.

    Args:
        due_date: Can be a string (ISO format), date, or datetime.

    Returns:
        A datetime object.
    """
    if isinstance(due_date, str):
        return datetime.fromisoformat(due_date)
    elif isinstance(due_date, datetime):
        return due_date
    elif hasattr(due_date, "year") and not isinstance(due_date, datetime):
        # It's a date object
        return datetime.combine(due_date, datetime.min.time())
    else:
        raise ValueError(f"Cannot normalize due_date of type {type(due_date)}")


def calculate_household_health_score(
    chore_rows: List[Tuple],
    now: Optional[datetime] = None,
) -> int:
    """
    Calculate the overall household health score from a list of chores.

    Args:
        chore_rows: List of tuples (due_date, interval_days).
        now: The current datetime. Defaults to datetime.now().

    Returns:
        An integer score from 0-100 (averaged across all chores).
        Returns 100 if no chores are provided.
    """
    if not chore_rows:
        return 100

    if now is None:
        now = datetime.now()

    total_score = 0.0
    active_chore_count = 0

    for row in chore_rows:
        due_date = row[0]
        interval_days = row[1]

        # Skip invalid chores
        if interval_days is None or interval_days <= 0:
            continue

        try:
            normalized_due_date = normalize_due_date(due_date)
            score = calculate_single_chore_score(
                normalized_due_date, interval_days, now
            )
            total_score += score
            active_chore_count += 1
        except (ValueError, TypeError):
            # Skip chores with invalid dates
            continue

    if active_chore_count == 0:
        return 100

    return int(round(total_score / active_chore_count))
