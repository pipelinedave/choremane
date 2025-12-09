"""
Unit tests for business logic functions.

These tests are isolated and do not require a database connection.
They focus on pure logic like date calculations and scoring algorithms.
"""

from datetime import date, datetime, timedelta

import pytest


# =============================================================================
# Household Health Score Logic Tests (using services module)
# =============================================================================


class TestSingleChoreScoreCalculation:
    """Tests for the calculate_single_chore_score function."""

    def test_fresh_chore_returns_100(self):
        """A chore with less than 50% of interval elapsed should score 100."""
        from app.services import calculate_single_chore_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        due_date = datetime(2025, 1, 15, 12, 0, 0)  # 5 days away
        interval_days = 7  # 7 day interval, 5 days remaining = ~28% elapsed

        score = calculate_single_chore_score(due_date, interval_days, now)

        assert score == 100

    def test_standard_zone_chore_decays_score(self):
        """A chore between 50-100% elapsed should decay from 100 to 80."""
        from app.services import calculate_single_chore_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        due_date = datetime(2025, 1, 11, 12, 0, 0)  # 1 day away
        interval_days = 7  # 7 day interval, 1 day remaining = ~86% elapsed

        score = calculate_single_chore_score(due_date, interval_days, now)

        # At 86% elapsed (0.86), which is in the 0.5-1.0 range
        # score = 100 + ((0.86 - 0.5) * -40) = 100 - 14.4 = 85.6
        assert 80 < score < 90

    def test_due_today_chore_scores_around_80(self):
        """A chore exactly at due date (100% elapsed) should score around 80."""
        from app.services import calculate_single_chore_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        due_date = datetime(2025, 1, 10, 12, 0, 0)  # Due now
        interval_days = 7

        score = calculate_single_chore_score(due_date, interval_days, now)

        # Exactly at due time, diff_ms = 0 goes into overdue branch
        assert 75 <= score <= 85

    def test_overdue_chore_decays_from_80(self):
        """An overdue chore should decay from 80 towards 0."""
        from app.services import calculate_single_chore_score

        now = datetime(2025, 1, 15, 12, 0, 0)
        due_date = datetime(2025, 1, 10, 12, 0, 0)  # 5 days overdue
        interval_days = 10  # 10 day interval, 50% overdue

        score = calculate_single_chore_score(due_date, interval_days, now)

        # overdue_ratio = 0.5, score = 80 - (0.5 * 80) = 40
        assert score == 40

    def test_very_overdue_chore_scores_zero(self):
        """A chore overdue by more than 100% of its interval should score 0."""
        from app.services import calculate_single_chore_score

        now = datetime(2025, 1, 20, 12, 0, 0)
        due_date = datetime(2025, 1, 10, 12, 0, 0)  # 10 days overdue
        interval_days = 7  # 7 day interval, ~143% overdue

        score = calculate_single_chore_score(due_date, interval_days, now)

        # overdue_ratio = 10/7 = 1.43, score = max(0, 80 - (1.43 * 80)) = 0
        assert score == 0

    def test_edge_case_exactly_50_percent_elapsed(self):
        """A chore exactly at 50% elapsed should score 100."""
        from app.services import calculate_single_chore_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        due_date = datetime(2025, 1, 13, 12, 0, 0)  # 3 days away
        interval_days = 6  # 6 day interval, 3 days remaining = 50% elapsed

        score = calculate_single_chore_score(due_date, interval_days, now)

        assert score == 100

    def test_defaults_to_now_when_not_provided(self):
        """Function should work when now is not explicitly provided."""
        from app.services import calculate_single_chore_score

        # Use a due date far in the future to ensure it's fresh
        due_date = datetime.now() + timedelta(days=30)
        interval_days = 7

        score = calculate_single_chore_score(due_date, interval_days)

        assert score == 100


class TestNormalizeDueDate:
    """Tests for the normalize_due_date function."""

    def test_string_iso_format(self):
        """ISO format strings should be parsed correctly."""
        from app.services import normalize_due_date

        result = normalize_due_date("2025-01-15T12:00:00")

        assert result == datetime(2025, 1, 15, 12, 0, 0)

    def test_date_object(self):
        """date objects should be converted to datetime at midnight."""
        from app.services import normalize_due_date

        result = normalize_due_date(date(2025, 1, 15))

        assert result == datetime(2025, 1, 15, 0, 0, 0)

    def test_datetime_passthrough(self):
        """datetime objects should pass through unchanged."""
        from app.services import normalize_due_date

        dt = datetime(2025, 1, 15, 12, 30, 45)
        result = normalize_due_date(dt)

        assert result == dt

    def test_invalid_type_raises_error(self):
        """Invalid types should raise ValueError."""
        from app.services import normalize_due_date

        with pytest.raises(ValueError):
            normalize_due_date(12345)


class TestHouseholdHealthScore:
    """Tests for the calculate_household_health_score function."""

    def test_empty_chores_returns_100(self):
        """Empty chore list should return 100."""
        from app.services import calculate_household_health_score

        score = calculate_household_health_score([])

        assert score == 100

    def test_single_fresh_chore_returns_100(self):
        """A single fresh chore should result in score 100."""
        from app.services import calculate_household_health_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        chores = [(datetime(2025, 1, 20, 12, 0, 0), 7)]  # Fresh chore

        score = calculate_household_health_score(chores, now)

        assert score == 100

    def test_mixed_chores_returns_average(self):
        """Multiple chores with different scores should return their average."""
        from app.services import calculate_household_health_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        chores = [
            (datetime(2025, 1, 20, 12, 0, 0), 7),  # Fresh = 100
            (datetime(2025, 1, 5, 12, 0, 0), 10),  # 50% overdue = 40
        ]

        score = calculate_household_health_score(chores, now)

        # Average of 100 and 40 = 70
        assert score == 70

    def test_skips_invalid_interval_days(self):
        """Chores with interval_days <= 0 should be skipped."""
        from app.services import calculate_household_health_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        chores = [
            (datetime(2025, 1, 20, 12, 0, 0), 7),  # Valid
            (datetime(2025, 1, 5, 12, 0, 0), 0),  # Invalid - should be skipped
            (datetime(2025, 1, 5, 12, 0, 0), -1),  # Invalid - should be skipped
        ]

        score = calculate_household_health_score(chores, now)

        # Only the fresh chore should count
        assert score == 100

    def test_handles_date_objects(self):
        """Should handle date objects in addition to datetime."""
        from app.services import calculate_household_health_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        chores = [(date(2025, 1, 20), 7)]  # date object

        score = calculate_household_health_score(chores, now)

        assert score == 100

    def test_handles_string_dates(self):
        """Should handle ISO string dates."""
        from app.services import calculate_household_health_score

        now = datetime(2025, 1, 10, 12, 0, 0)
        chores = [("2025-01-20T12:00:00", 7)]  # ISO string

        score = calculate_household_health_score(chores, now)

        assert score == 100


# =============================================================================
# Date Utility Tests
# =============================================================================


class TestDateConversion:
    """Tests for the _to_iso_date utility function."""

    def test_datetime_converts_to_iso(self):
        """datetime objects should convert to ISO format strings."""
        from app.api.routes import _to_iso_date

        dt = datetime(2024, 1, 2, 3, 4, 5)
        result = _to_iso_date(dt)

        assert result == "2024-01-02T03:04:05"

    def test_date_converts_to_iso(self):
        """date objects should convert to ISO format strings."""
        from app.api.routes import _to_iso_date

        d = date(2024, 1, 2)
        result = _to_iso_date(d)

        assert result == "2024-01-02"

    def test_string_passes_through(self):
        """String values should pass through unchanged."""
        from app.api.routes import _to_iso_date

        result = _to_iso_date("2024-01-02")

        assert result == "2024-01-02"

    def test_none_returns_none(self):
        """None should return None."""
        from app.api.routes import _to_iso_date

        result = _to_iso_date(None)

        assert result is None


# =============================================================================
# Log Action Utility Tests
# =============================================================================


class TestLogAction:
    """Tests for the log_action utility function."""

    def test_log_action_commits_to_database(self, mock_db_connection, monkeypatch):
        """log_action should insert a log entry and commit."""
        conn = mock_db_connection()
        monkeypatch.setattr("app.utils.get_db_connection", lambda: conn)
        from app.utils import log_action

        log_action(
            chore_id=1,
            done_by="tester",
            action_type="marked_done",
            action_details={"previous_due_date": "2025-01-01"},
        )

        assert conn.committed is True
        assert len(conn.cursor().queries) > 0

    def test_log_action_skips_import_export_without_chore_id(
        self, mock_db_connection, monkeypatch
    ):
        """System-level actions like import/export should skip database logging."""
        conn = mock_db_connection()
        monkeypatch.setattr("app.utils.get_db_connection", lambda: conn)
        from app.utils import log_action

        log_action(
            chore_id=None,
            done_by="system",
            action_type="export",
            action_details={"count": 10},
        )

        # Should not have committed anything since it's a system action
        assert conn.committed is False

    def test_log_action_converts_dates_to_iso(self, mock_db_connection, monkeypatch):
        """Date/datetime values in action_details should be converted to ISO strings."""
        conn = mock_db_connection()
        monkeypatch.setattr("app.utils.get_db_connection", lambda: conn)
        from app.utils import log_action

        log_action(
            chore_id=1,
            done_by="tester",
            action_type="updated",
            action_details={"due_date": date(2025, 1, 15)},
        )

        # The query should have been executed with ISO date string
        assert conn.committed is True
