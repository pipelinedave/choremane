from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
import json
import pytest
from app.api.routes import api_router

app = FastAPI()
app.include_router(api_router)
client = TestClient(app)

# Dummy DB connection classes and helper functions
class DummyCursor:
    def __init__(self, rows=None, description=None, rowcount=1):
        self._rows = rows or []
        self.description = description
        self.rowcount = rowcount

    def execute(self, query, params=None):
        self.query = query
        self.params = params

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows

    def close(self):
        pass

class DummyConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

def dummy_get_db_connection_for_status():
    cursor = DummyCursor(rows=[[1]])
    return DummyConnection(cursor)

def dummy_get_db_connection_for_logs():
    # simulate one log entry: id, chore_id, done_by, done_at, action_details
    log_date = datetime.now()
    row = [1, 101, "tester", log_date, json.dumps({"action": "test log"})]
    cursor = DummyCursor(
        rows=[row],
        description=[("id",), ("chore_id",), ("done_by",), ("done_at",), ("action_details",)]
    )
    return DummyConnection(cursor)

def dummy_get_db_connection_for_chores():
    # simulate two chore rows
    rows = [
        [1, "Test Chore", 7, date.today(), False, None, False],
        [2, "Another Chore", 3, date.today() + timedelta(days=3), False, None, False]
    ]
    cursor = DummyCursor(
        rows=rows,
        description=[("id",), ("name",), ("interval_days",), ("due_date",), ("done",), ("done_by",), ("archived",)]
    )
    return DummyConnection(cursor)

def dummy_get_db_connection_for_insert(chore_id=123):
    cursor = DummyCursor(rows=[[chore_id]])
    return DummyConnection(cursor)

def dummy_get_db_connection_for_archive():
    # simulate archive update with rowcount=1
    cursor = DummyCursor(rowcount=1)
    return DummyConnection(cursor)

# Tests
def test_options_handler():
    response = client.options("/api/anything")
    assert response.status_code == 200
    assert response.json() == "OK"

def test_cors_test():
    response = client.post("/api/cors-test")
    assert response.status_code == 200
    assert response.json() == {"message": "CORS test successful"}

def test_status_check(monkeypatch):
    monkeypatch.setattr("app.api.routes.get_db_connection", dummy_get_db_connection_for_status)
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert "database is reachable" in data["message"]

def test_get_logs(monkeypatch):
    monkeypatch.setattr("app.api.routes.get_db_connection", dummy_get_db_connection_for_logs)
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        log = data[0]
        assert log["id"] == 1

def test_get_chores(monkeypatch):
    monkeypatch.setattr("app.api.routes.get_db_connection", dummy_get_db_connection_for_chores)
    response = client.get("/api/chores")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

def test_get_version_info(monkeypatch):
    import os
    monkeypatch.setenv("VERSION_TAG", "v1.2.3")
    monkeypatch.setenv("BACKEND_IMAGE", "backend:latest")
    monkeypatch.setenv("FRONTEND_IMAGE", "frontend:latest")
    response = client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version_tag"] == "v1.2.3"
    assert data["backend_image"] == "backend:latest"
    assert data["frontend_image"] == "frontend:latest"

def test_private_and_shared_chores(monkeypatch):
    # Simulate DB returning both private and shared chores
    def fake_get_db_connection():
        from datetime import date
        rows = [
            [1, "Shared Chore", 7, date.today(), False, None, False, None, False],
            [2, "Private Chore", 3, date.today(), False, None, False, "user@example.com", True]
        ]
        class DummyCursor:
            def execute(self, *a, **k): pass
            def fetchall(self): return rows
            def close(self): pass
        class DummyConn:
            def cursor(self): return DummyCursor()
            def close(self): pass
        return DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", fake_get_db_connection)
    # Simulate user requesting chores
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)
    response = client.get("/api/chores", headers={"X-User-Email": "user@example.com"})
    assert response.status_code == 200
    data = response.json()
    # Should see both shared and their own private chore
    assert any(c['name'] == "Shared Chore" for c in data)
    assert any(c['name'] == "Private Chore" for c in data)
    # Simulate another user (should only see shared chore)
    response2 = client.get("/api/chores", headers={"X-User-Email": "other@example.com"})
    data2 = response2.json()
    assert any(c['name'] == "Shared Chore" for c in data2)
    assert not any(c['name'] == "Private Chore" for c in data2)

def test_add_chore_with_privacy(monkeypatch):
    # Simulate DB insert and return id
    def fake_get_db_connection():
        class DummyCursor:
            def execute(self, *a, **k): pass
            def fetchone(self): return [123]
            def close(self): pass
        class DummyConn:
            def cursor(self): return DummyCursor()
            def commit(self): pass
            def rollback(self): pass
            def close(self): pass
        return DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", fake_get_db_connection)
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)
    chore = {
        "name": "Private Chore",
        "interval_days": 5,
        "due_date": "2025-04-28",
        "done": False,
        "done_by": None,
        "archived": False,
        "owner_email": "user@example.com",
        "is_private": True
    }
    response = client.post("/api/chores", json=chore)
    assert response.status_code == 200
    assert response.json()["id"] == 123

def test_undo_created_action(monkeypatch):
    # Simulate DB for undoing a 'created' action
    class DummyCursor:
        def __init__(self):
            self.closed = False
            self.deleted = False
            self.log_id = None
        def execute(self, query, params=None):
            if "SELECT action_type" in query:
                self.log_id = params[0]
                self._row = ("created", json.dumps({"id": 42}))
            elif "DELETE FROM chores" in query:
                self.deleted = True
        def fetchone(self):
            return getattr(self, '_row', None)
        def close(self):
            self.closed = True
    class DummyConn:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: DummyConn())
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)
    response = client.post("/api/undo", json={"log_id": 1})
    assert response.status_code == 200
    assert "undone successfully" in response.json()["message"]

def test_undo_invalid_log(monkeypatch):
    # Simulate DB for missing log entry
    class DummyCursor:
        def execute(self, query, params=None):
            self._row = None
        def fetchone(self):
            return None
        def close(self): pass
    class DummyConn:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: DummyConn())
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)
    response = client.post("/api/undo", json={"log_id": 999})
    assert response.status_code == 404
    assert "Log entry not found" in response.json()["detail"]

def test_undo_updated_action(monkeypatch):
    # Simulate DB for undoing an 'updated' action
    class DummyCursor:
        def __init__(self):
            self.closed = False
            self.updated = False
            self.log_id = None
        def execute(self, query, params=None):
            if "SELECT action_type" in query:
                self.log_id = params[0]
                self._row = ("updated", json.dumps({"previous_state": {"name": "Old Name", "interval_days": 2, "due_date": "2025-04-28", "id": 42}}))
            elif "UPDATE chores SET name" in query:
                self.updated = True
        def fetchone(self):
            return getattr(self, '_row', None)
        def close(self):
            self.closed = True
    class DummyConn:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: DummyConn())
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)
    response = client.post("/api/undo", json={"log_id": 2})
    assert response.status_code == 200
    assert "undone successfully" in response.json()["message"]

def test_undo_archived_action(monkeypatch):
    # Simulate DB for undoing an 'archived' action
    class DummyCursor:
        def __init__(self):
            self.closed = False
            self.unarchived = False
            self.log_id = None
        def execute(self, query, params=None):
            if "SELECT action_type" in query:
                self.log_id = params[0]
                self._row = ("archived", json.dumps({"id": 42}))
            elif "UPDATE chores SET archived = FALSE" in query:
                self.unarchived = True
        def fetchone(self):
            return getattr(self, '_row', None)
        def close(self):
            self.closed = True
    class DummyConn:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: DummyConn())
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)
    response = client.post("/api/undo", json={"log_id": 3})
    assert response.status_code == 200
    assert "undone successfully" in response.json()["message"]

def test_undo_marked_done_action(monkeypatch):
    # Simulate DB for undoing a 'marked_done' action
    class DummyCursor:
        def __init__(self):
            self.closed = False
            self.undone = False
            self.log_id = None
        def execute(self, query, params=None):
            if "SELECT action_type" in query:
                self.log_id = params[0]
                self._row = ("marked_done", json.dumps({"chore_id": 42, "previous_due_date": "2025-04-27"}))
            elif "UPDATE chores SET done = FALSE" in query:
                self.undone = True
        def fetchone(self):
            return getattr(self, '_row', None)
        def close(self):
            self.closed = True
    class DummyConn:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: DummyConn())
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)
    response = client.post("/api/undo", json={"log_id": 4})
    assert response.status_code == 200
    assert "undone successfully" in response.json()["message"]

def test_undo_unsupported_action(monkeypatch):
    # Simulate DB for unsupported undo action
    class DummyCursor:
        def __init__(self):
            self.closed = False
            self.log_id = None
        def execute(self, query, params=None):
            if "SELECT action_type" in query:
                self.log_id = params[0]
                self._row = ("something_else", json.dumps({"id": 42}))
        def fetchone(self):
            return getattr(self, '_row', None)
        def close(self):
            self.closed = True
    class DummyConn:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
    monkeypatch.setattr("app.api.routes.get_db_connection", lambda: DummyConn())
    from app.main import app as fastapi_app
    client = TestClient(fastapi_app)
    response = client.post("/api/undo", json={"log_id": 5})
    assert response.status_code == 400
    assert "Undo not supported" in response.json()["detail"]
