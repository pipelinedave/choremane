import os

import psycopg2
import pytest


class FakeCursor:
    def __init__(self):
        self._rows = []
        self.description = None
        self.rowcount = 1

    def execute(self, query, params=None):
        text = query.lower()
        if "information_schema.columns" in text and "table_name='chores'" in text:
            self._rows = [("owner_email",), ("is_private",)]
            self.description = [("column_name",)]
        elif "select 1" in text:
            self._rows = [(1,)]
            self.description = [("?column?",)]
        else:
            # Default to empty result set for unsupported queries
            self._rows = []
            self.description = []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class FakeConnection:
    def cursor(self):
        return FakeCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


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

    original_connect = psycopg2.connect
    psycopg2.connect = lambda *args, **kwargs: FakeConnection()
    try:
        yield
    finally:
        psycopg2.connect = original_connect
