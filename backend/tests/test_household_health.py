"""
Tests for the household health endpoint.
"""

from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.household_health_endpoint import router


def make_client():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


class TestHouseholdHealthEndpoint:
    """Tests for the /api/chores/household-health endpoint."""

    def test_returns_100_for_no_chores(self, monkeypatch):
        """Empty chore list should return score 100."""
        client = make_client()

        class DummyCursor:
            def execute(self, *args, **kwargs):
                pass

            def fetchall(self):
                return []

            def close(self):
                pass

        class DummyConn:
            def cursor(self):
                return DummyCursor()

            def close(self):
                pass

        monkeypatch.setattr(
            "app.api.household_health_endpoint.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/household-health",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 200
        assert response.json() == {"score": 100}

    def test_returns_score_for_fresh_chores(self, monkeypatch):
        """Fresh chores should result in a high score."""
        client = make_client()
        # Chore due 10 days from now with 7-day interval = very fresh
        future_date = date.today() + timedelta(days=10)

        class DummyCursor:
            def execute(self, *args, **kwargs):
                pass

            def fetchall(self):
                return [(future_date, 7)]

            def close(self):
                pass

        class DummyConn:
            def cursor(self):
                return DummyCursor()

            def close(self):
                pass

        monkeypatch.setattr(
            "app.api.household_health_endpoint.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/household-health",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 200
        assert response.json()["score"] == 100

    def test_returns_low_score_for_overdue_chores(self, monkeypatch):
        """Overdue chores should result in a lower score."""
        client = make_client()
        # Chore due 5 days ago with 10-day interval = 50% overdue
        past_date = date.today() - timedelta(days=5)

        class DummyCursor:
            def execute(self, *args, **kwargs):
                pass

            def fetchall(self):
                return [(past_date, 10)]

            def close(self):
                pass

        class DummyConn:
            def cursor(self):
                return DummyCursor()

            def close(self):
                pass

        monkeypatch.setattr(
            "app.api.household_health_endpoint.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/household-health",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 200
        # 50% overdue = score around 40
        score = response.json()["score"]
        assert score < 50

    def test_handles_database_errors(self, monkeypatch):
        """Database errors should return 500 or cause an exception."""
        app = FastAPI()
        app.include_router(router, prefix="/api")
        # Use raise_server_exceptions=False to get HTTP response instead of exception
        client = TestClient(app, raise_server_exceptions=False)

        def raise_error():
            raise Exception("Database connection failed")

        monkeypatch.setattr(
            "app.api.household_health_endpoint.get_db_connection",
            raise_error,
        )

        response = client.get(
            "/api/chores/household-health",
            headers={"X-User-Email": "user@example.com"},
        )

        # Server error should return 500
        assert response.status_code == 500

    def test_respects_user_email_header(self, monkeypatch):
        """The endpoint should pass the user email to the query."""
        client = make_client()
        captured_params = []

        class DummyCursor:
            def execute(self, query, params=None):
                captured_params.append(params)

            def fetchall(self):
                return []

            def close(self):
                pass

        class DummyConn:
            def cursor(self):
                return DummyCursor()

            def close(self):
                pass

        monkeypatch.setattr(
            "app.api.household_health_endpoint.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/household-health",
            headers={"X-User-Email": "test@example.com"},
        )

        assert response.status_code == 200
        # The user email should have been passed to the query
        assert captured_params and captured_params[0] == ("test@example.com",)
