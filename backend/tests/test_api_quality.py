import json
from datetime import date, datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import routes as routes_module
from app.api.routes import api_router
from app.api.mcp_routes import router as mcp_router


def make_client():
    app = FastAPI()
    app.include_router(api_router)
    app.include_router(mcp_router)
    return TestClient(app)


def test_to_iso_date_converts_datetime_and_passes_through():
    now = datetime(2024, 1, 2, 3, 4, 5)
    assert routes_module._to_iso_date(now) == now.isoformat()
    assert routes_module._to_iso_date("2024-01-02") == "2024-01-02"
    assert routes_module._to_iso_date(None) is None


def test_mark_chore_done_updates_due_date_and_logs(monkeypatch):
    client = make_client()
    today = date.today()

    class DummyCursor:
        def __init__(self):
            self.calls = []
            self.description = None
            self.rowcount = 1

        def execute(self, query, params=None):
            self.calls.append((query, params))

        def fetchone(self):
            # interval_days, due_date, last_done
            return (2, today, None)

        def close(self):
            pass

    class DummyConn:
        def __init__(self):
            self.cursor_obj = DummyCursor()
            self.committed = False
            self.rolled_back = False
            self.closed = False

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

        def close(self):
            self.closed = True

    dummy_conn = DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: dummy_conn)
    log_calls = []
    monkeypatch.setattr("app.api.routes.log_action", lambda *a, **k: log_calls.append((a, k)))

    response = client.put("/api/chores/7/done", json={"done_by": "tester"})

    assert response.status_code == 200
    body = response.json()
    assert body["done_by"] == "tester"
    assert body["new_due_date"] == (today + timedelta(days=2)).isoformat()
    assert dummy_conn.committed is True
    assert dummy_conn.rolled_back is False
    assert any("UPDATE chores" in call[0] for call in dummy_conn.cursor_obj.calls)
    assert log_calls and log_calls[0][0][0] == 7


def test_mark_chore_done_requires_actor():
    client = make_client()
    response = client.put("/api/chores/1/done", json={})
    assert response.status_code == 422


def test_update_chore_uses_previous_state(monkeypatch):
    client = make_client()

    class DummyCursor:
        def __init__(self):
            self.description = [("id",), ("name",), ("interval_days",), ("due_date",)]
            self.calls = []
            self._fetched = False

        def execute(self, query, params=None):
            self.calls.append((query, params))

        def fetchone(self):
            if not self._fetched:
                self._fetched = True
                return (5, "Old name", 3, date(2025, 1, 1))
            return None

        def close(self):
            pass

    class DummyConn:
        def __init__(self):
            self.cursor_obj = DummyCursor()
            self.committed = False
            self.rolled_back = False

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

        def close(self):
            pass

    dummy_conn = DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: dummy_conn)
    log_calls = []
    monkeypatch.setattr("app.api.routes.log_action", lambda *a, **k: log_calls.append((a, k)))

    payload = {
        "name": "Updated",
        "interval_days": 5,
        "due_date": "2025-02-02",
        "done": False,
        "archived": False,
        "is_private": False,
    }
    response = client.put("/api/chores/5", json=payload)

    assert response.status_code == 200
    assert dummy_conn.committed is True
    assert dummy_conn.rolled_back is False
    assert log_calls
    previous_state = log_calls[0][1]["action_details"]["previous_state"]
    assert previous_state["name"] == "Old name"
    assert previous_state["due_date"] == date(2025, 1, 1).isoformat()


def test_update_chore_not_found(monkeypatch):
    client = make_client()

    class DummyCursor:
        def __init__(self):
            self.description = []

        def execute(self, *args, **kwargs):
            pass

        def fetchone(self):
            return None

        def close(self):
            pass

    class DummyConn:
        def __init__(self):
            self.committed = False
            self.rolled_back = False
            self.cursor_obj = DummyCursor()

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

        def close(self):
            pass

    dummy_conn = DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: dummy_conn)

    response = client.put(
        "/api/chores/99",
        json={"name": "Missing", "interval_days": 1, "due_date": "2025-01-01", "done": False, "archived": False, "is_private": False},
    )

    assert response.status_code == 404
    assert dummy_conn.rolled_back is True
    assert dummy_conn.committed is False


def test_archive_chore_returns_404_when_missing(monkeypatch):
    client = make_client()

    class DummyCursor:
        def __init__(self):
            self.rowcount = 0

        def execute(self, *args, **kwargs):
            pass

        def close(self):
            pass

    class DummyConn:
        def __init__(self):
            self.cursor_obj = DummyCursor()
            self.rolled_back = False

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            pass

        def rollback(self):
            self.rolled_back = True

        def close(self):
            pass

    dummy_conn = DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: dummy_conn)

    response = client.put("/api/chores/321/archive")

    assert response.status_code == 404
    assert dummy_conn.rolled_back is True


def test_export_data_formats_dates(monkeypatch):
    client = make_client()
    due_date = date(2025, 1, 1)
    last_done = datetime(2024, 12, 31, 12, 0, 0)
    done_at = datetime(2025, 1, 2, 8, 30, 0)

    class DummyCursor:
        def __init__(self):
            self.last_query = None
            self.description = []

        def execute(self, query, params=None):
            if "FROM chores" in query:
                self.last_query = "chores"
                self.description = [
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
            else:
                self.last_query = "logs"
                self.description = [
                    ("id",),
                    ("chore_id",),
                    ("done_by",),
                    ("done_at",),
                    ("action_details",),
                    ("action_type",),
                ]

        def fetchall(self):
            if self.last_query == "chores":
                return [(1, "Test", 3, due_date, False, None, False, None, False, last_done)]
            if self.last_query == "logs":
                return [(10, 1, "tester", done_at, {"detail": "x"}, "done")]
            return []

        def close(self):
            pass

    class DummyConn:
        def __init__(self):
            self.cursor_obj = DummyCursor()

        def cursor(self):
            return self.cursor_obj

        def close(self):
            pass

    dummy_conn = DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: dummy_conn)
    log_calls = []
    monkeypatch.setattr("app.api.routes.log_action", lambda *a, **k: log_calls.append((a, k)))

    response = client.get("/api/export", headers={"X-User-Email": "user@example.com"})

    assert response.status_code == 200
    data = response.json()
    assert data["chores"][0]["due_date"] == due_date.isoformat()
    assert data["chores"][0]["last_done"] == last_done.isoformat()
    assert data["logs"][0]["done_at"] == done_at.isoformat()
    assert log_calls and log_calls[0][0][2] == "export"


def test_import_data_validates_payload():
    client = make_client()
    response = client.post("/api/import", json={})
    assert response.status_code == 400


def test_import_data_creates_and_updates(monkeypatch):
    client = make_client()

    class DummyCursor:
        def __init__(self):
            self.pending_fetch = None
            self.created = []
            self.updated = []
            self.inserted_logs = 0
            self.next_id = 500

        def execute(self, query, params=None):
            if "SELECT id FROM chores" in query:
                # Only id=101 exists already
                self.pending_fetch = (101,) if params and params[0] == 101 else None
            elif query.strip().startswith("UPDATE chores"):
                # params: name, interval_days, due_date, is_private, owner_email, last_done, id
                self.updated.append(params[6])
                self.pending_fetch = None
            elif query.strip().startswith("INSERT INTO chores"):
                self.created.append(params[0])
                self.pending_fetch = (self.next_id,)
                self.next_id += 1
            elif "INSERT INTO chore_logs" in query:
                self.inserted_logs += 1
                self.pending_fetch = None

        def fetchone(self):
            value = self.pending_fetch
            self.pending_fetch = None
            return value

        def close(self):
            pass

    class DummyConn:
        def __init__(self):
            self.cursor_obj = DummyCursor()
            self.committed = False

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.committed = True

        def close(self):
            pass

    dummy_conn = DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: dummy_conn)
    log_calls = []
    monkeypatch.setattr("app.api.routes.log_action", lambda *a, **k: log_calls.append((a, k)))

    payload = {
        "chores": [
            {"id": 101, "name": "Existing", "interval_days": 3, "due_date": "2025-05-01", "is_private": True},
            {"name": "New chore", "interval_days": 1, "due_date": "2025-05-02", "archived": False, "last_done": "2025-04-01"},
        ],
        "logs": [
            {"chore_id": 101, "done_by": "tester", "done_at": "2025-04-01T00:00:00", "action_type": "marked_done", "action_details": {"x": 1}}
        ],
    }

    response = client.post("/api/import", json=payload, headers={"X-User-Email": "user@example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["imported_chores"] == 2
    assert dummy_conn.committed is True
    assert dummy_conn.cursor_obj.updated == [101]
    assert dummy_conn.cursor_obj.created  # new chore created
    assert dummy_conn.cursor_obj.inserted_logs == 1
    assert log_calls and log_calls[0][0][2] == "import"


def test_get_chore_counts_returns_breakdown(monkeypatch):
    client = make_client()

    class DummyCursor:
        def __init__(self):
            self.values = [12, 2, 3, 1, 4, 2]

        def execute(self, *args, **kwargs):
            pass

        def fetchone(self):
            return (self.values.pop(0),)

        def close(self):
            pass

    class DummyConn:
        def __init__(self):
            self.cursor_obj = DummyCursor()

        def cursor(self):
            return self.cursor_obj

        def close(self):
            pass

    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: DummyConn())

    response = client.get("/api/chores/count", headers={"X-User-Email": "user@example.com"})

    assert response.status_code == 200
    counts = response.json()
    assert counts == {
        "all": 12,
        "overdue": 2,
        "today": 3,
        "tomorrow": 1,
        "thisWeek": 4,
        "upcoming": 2,
    }


def test_get_logs_parses_action_details(monkeypatch):
    client = make_client()
    log_time = datetime(2025, 1, 1, 10, 0, 0)

    class DummyCursor:
        def __init__(self):
            self.description = None

        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return [
                (1, None, "tester", log_time, json.dumps({"action": "json"}), "created"),
                (2, None, "tester", log_time, "not-json", "created"),
            ]

        def close(self):
            pass

    class DummyConn:
        def __init__(self):
            self.cursor_obj = DummyCursor()

        def cursor(self):
            return self.cursor_obj

        def close(self):
            pass

    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: DummyConn())

    response = client.get("/api/logs", headers={"X-User-Email": "user@example.com"})

    assert response.status_code == 200
    data = response.json()
    assert data[0]["action_details"] == {"action": "json"}
    assert data[1]["action_details"] == "not-json"
    assert data[0]["done_at"] == log_time.isoformat()


def test_mcp_generate_requires_user_message(monkeypatch):
    client = make_client()
    response = client.post("/mcp/generate", json={"messages": [{"role": "system", "content": "hello"}]})
    assert response.status_code == 400
