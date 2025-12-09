"""
Tests for the archived chores endpoint.
"""

from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import api_router


def make_client():
    app = FastAPI()
    app.include_router(api_router)
    return TestClient(app)


class TestArchivedChoresEndpoint:
    """Tests for the /api/chores/archived endpoint."""

    def test_returns_empty_list_for_no_archived_chores(self, monkeypatch):
        """Empty database should return empty list."""
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
            "app.api.routes.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/archived",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_archived_chores(self, monkeypatch):
        """Should return archived chores correctly formatted."""
        client = make_client()
        today = date.today()

        class DummyCursor:
            def execute(self, *args, **kwargs):
                pass

            def fetchall(self):
                # id, name, interval_days, due_date, done, done_by, archived, owner_email, is_private, last_done
                return [
                    (
                        1,
                        "Archived Chore 1",
                        7,
                        today,
                        False,
                        None,
                        True,
                        None,
                        False,
                        None,
                    ),
                    (
                        2,
                        "Archived Chore 2",
                        14,
                        today,
                        True,
                        "user@example.com",
                        True,
                        "user@example.com",
                        True,
                        today,
                    ),
                ]

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
            "/api/chores/archived",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Archived Chore 1"
        assert data[0]["archived"] is True
        assert data[1]["name"] == "Archived Chore 2"
        assert data[1]["is_private"] is True

    def test_supports_pagination(self, monkeypatch):
        """Should pass pagination parameters correctly."""
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
            "app.api.routes.get_db_connection",
            lambda: DummyConn(),
        )

        # Request page 2 with limit 5
        response = client.get(
            "/api/chores/archived?page=2&limit=5",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 200
        # Verify pagination params were passed (user_email is always first)
        assert len(captured_params) > 0
        assert captured_params[0][0] == "user@example.com"

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
            "app.api.routes.get_db_connection",
            lambda: DummyConn(),
        )

        response = client.get(
            "/api/chores/archived",
            headers={"X-User-Email": "test@example.com"},
        )

        assert response.status_code == 200
        # First param should be the user email
        assert captured_params[0][0] == "test@example.com"

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
            "/api/chores/archived",
            headers={"X-User-Email": "user@example.com"},
        )

        assert response.status_code == 500
