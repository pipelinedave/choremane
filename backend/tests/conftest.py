"""
Shared pytest fixtures and reusable mocks for backend tests.
"""

import json
import os
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import psycopg2
import pytest


# =============================================================================
# Reusable Mock Classes
# =============================================================================


class MockCursor:
    """A configurable mock database cursor for unit tests."""

    def __init__(
        self,
        rows: Optional[List[Any]] = None,
        description: Optional[List[Tuple[str]]] = None,
        rowcount: int = 1,
        fetchone_handler: Optional[Callable[..., Any]] = None,
        fetchall_handler: Optional[Callable[..., List[Any]]] = None,
    ):
        self._rows = rows or []
        self.description = description
        self.rowcount = rowcount
        self.queries: List[Tuple[str, Any]] = []
        self._fetchone_handler = fetchone_handler
        self._fetchall_handler = fetchall_handler

    def execute(self, query: str, params: Any = None) -> None:
        self.queries.append((query, params))

    def fetchone(self) -> Optional[Any]:
        if self._fetchone_handler:
            return self._fetchone_handler(self.queries)
        return self._rows[0] if self._rows else None

    def fetchall(self) -> List[Any]:
        if self._fetchall_handler:
            return self._fetchall_handler(self.queries)
        return self._rows

    def close(self) -> None:
        pass


class MockConnection:
    """A configurable mock database connection for unit tests."""

    def __init__(self, cursor: MockCursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self) -> MockCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


# =============================================================================
# Mock Factories
# =============================================================================


def create_mock_connection(
    rows: Optional[List[Any]] = None,
    description: Optional[List[Tuple[str]]] = None,
    rowcount: int = 1,
    fetchone_handler: Optional[Callable] = None,
    fetchall_handler: Optional[Callable] = None,
) -> MockConnection:
    """Factory function to create a MockConnection with a configured MockCursor."""
    cursor = MockCursor(
        rows=rows,
        description=description,
        rowcount=rowcount,
        fetchone_handler=fetchone_handler,
        fetchall_handler=fetchall_handler,
    )
    return MockConnection(cursor)


# =============================================================================
# Common Test Data Builders
# =============================================================================


def build_chore_row(
    id: int = 1,
    name: str = "Test Chore",
    interval_days: int = 7,
    due_date: Optional[date] = None,
    done: bool = False,
    done_by: Optional[str] = None,
    archived: bool = False,
    owner_email: Optional[str] = None,
    is_private: bool = False,
    last_done: Optional[date] = None,
) -> List[Any]:
    """Build a chore row tuple as returned from the database."""
    return [
        id,
        name,
        interval_days,
        due_date or date.today(),
        done,
        done_by,
        archived,
        owner_email,
        is_private,
        last_done,
    ]


def build_log_row(
    id: int = 1,
    chore_id: Optional[int] = None,
    done_by: str = "tester",
    done_at: Optional[datetime] = None,
    action_details: Optional[Dict] = None,
    action_type: str = "marked_done",
) -> List[Any]:
    """Build a log row tuple as returned from the database."""
    return [
        id,
        chore_id,
        done_by,
        done_at or datetime.now(),
        json.dumps(action_details or {}),
        action_type,
    ]


CHORE_DESCRIPTION = [
    ("id",),
    ("name",),
    ("interval_days",),
    ("due_date",),
    ("done",),
    ("done_by",),
    ("archived",),
    ("owner_email",),
    ("is_private",),
    ("last_done",),
]

LOG_DESCRIPTION = [
    ("id",),
    ("chore_id",),
    ("done_by",),
    ("done_at",),
    ("action_details",),
    ("action_type",),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db_connection():
    """
    Provides a factory fixture to create mock database connections.

    Usage in tests:
        def test_something(mock_db_connection, monkeypatch):
            conn = mock_db_connection(rows=[[1, "Test", ...]])
            monkeypatch.setattr("app.api.routes.get_db_connection", lambda: conn)
    """
    return create_mock_connection


@pytest.fixture(scope="session", autouse=True)
def fallback_fake_db():
    """Provide a lightweight fake database when PostgreSQL isn't available."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            database=os.getenv("POSTGRES_DB", "choresdb"),
            user=os.getenv("POSTGRES_USER", "admin"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            connect_timeout=1,
        )
        conn.close()
        yield
        return
    except Exception:
        pass

    # If no real DB, patch psycopg2.connect for the entire session
    original_connect = psycopg2.connect

    def fake_connect(*args, **kwargs):
        cursor = MockCursor(
            rows=[(1,)],
            description=[("?column?",)],
        )
        return MockConnection(cursor)

    psycopg2.connect = fake_connect
    try:
        yield
    finally:
        psycopg2.connect = original_connect


@pytest.fixture
def real_db_connection():
    """
    Fixture providing a real PostgreSQL connection for integration tests.
    Skips if DB is unavailable.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            database=os.getenv("POSTGRES_DB", "choresdb"),
            user=os.getenv("POSTGRES_USER", "admin"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            connect_timeout=2,
        )
        yield conn
        conn.rollback()
        conn.close()
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")
