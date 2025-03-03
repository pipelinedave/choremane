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
