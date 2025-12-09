"""
Tests for the chore counts endpoint.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import api_router


def make_client():
    app = FastAPI()
    app.include_router(api_router)
    return TestClient(app)


class TestChoreCountsEndpoint:
    """Tests for the /api/chores/count endpoint."""

    def test_returns_all_zero_counts_for_empty_db(self, monkeypatch):
        """Empty database should return all zeros."""
        client = make_client()

        class DummyCursor:
            def execute(self, *args, **kwargs):
                pass

            def fetchone(self):
                return (0,)

            def close(self):
                pass

        class DummyConn:
            def cursor(self):
                return DummyCursor()

            def close(self):
                pass

        monkeypatch.setattr(
            "app.api.routes.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/count",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data == {
            "all": 0,
            "overdue": 0,
            "today": 0,
            "tomorrow": 0,
            "thisWeek": 0,
            "upcoming": 0,
        }

    def test_returns_correct_counts(self, monkeypatch):
        """Should return correct counts for each category."""
        client = make_client()

        # Mock different counts for each query
        counts = iter(
            [10, 2, 3, 1, 2, 2]
        )  # all, overdue, today, tomorrow, thisWeek, upcoming

        class DummyCursor:
            def execute(self, *args, **kwargs):
                pass

            def fetchone(self):
                return (next(counts),)

            def close(self):
                pass

        class DummyConn:
            def cursor(self):
                return DummyCursor()

            def close(self):
                pass

        monkeypatch.setattr(
            "app.api.routes.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/count",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["all"] == 10
        assert data["overdue"] == 2
        assert data["today"] == 3
        assert data["tomorrow"] == 1
        assert data["thisWeek"] == 2
        assert data["upcoming"] == 2

    def test_respects_user_email_header(self, monkeypatch):
        """The endpoint should pass the user email to each query."""
        client = make_client()
        captured_params = []

        class DummyCursor:
            def execute(self, query, params=None):
                captured_params.append(params)

            def fetchone(self):
                return (5,)

            def close(self):
                pass

        class DummyConn:
            def cursor(self):
                return DummyCursor()

            def close(self):
                pass

        monkeypatch.setattr(
            "app.api.routes.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/count",
            headers={"X-User-Email": "test@example.com"},
        )

        assert response.status_code == 200
        # All queries should have included the user email
        assert all("test@example.com" in str(p) for p in captured_params)

    def test_handles_database_errors(self, monkeypatch):
        """Database errors should return 500."""
        app = FastAPI()
        app.include_router(api_router)
        client = TestClient(app, raise_server_exceptions=False)

        def raise_error():
            raise Exception("Database connection failed")

        monkeypatch.setattr(
            "app.api.routes.get_db_connection",
            raise_error,
        )

        response = client.get(
            "/api/chores/count",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 500
