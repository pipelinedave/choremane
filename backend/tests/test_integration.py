import os
import pytest
import psycopg2
from fastapi.testclient import TestClient
from app.main import app

def run_migrations():
    # Simulate running migrations (in real projects, use Alembic or similar)
    # Here, create the chores table if needed and check required columns
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        database=os.getenv('POSTGRES_DB', 'choresdb'),
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'password')
    )
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chores (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            interval_days INT NOT NULL,
            due_date DATE NOT NULL,
            done BOOLEAN DEFAULT FALSE,
            done_by VARCHAR(255),
            last_done DATE,
            owner_email VARCHAR(255),
            is_private BOOLEAN DEFAULT FALSE,
            archived BOOLEAN DEFAULT FALSE
        )
        """
    )
    conn.commit()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='chores'")
    columns = [row[0] for row in cur.fetchall()]
    assert 'owner_email' in columns
    assert 'is_private' in columns
    assert 'last_done' in columns
    cur.close()
    conn.close()

def test_migrations():
    run_migrations()

def test_auth_flow(monkeypatch):
    # Simulate a user with a valid token and username
    def fake_get_db_connection():
        class DummyCursor:
            def execute(self, *a, **k): pass
            def fetchall(self):
                return [
                    [1, "Shared Chore", 7, "2025-04-28", False, None, False, None, False, None],
                    [2, "Private Chore", 3, "2025-04-28", False, None, False, "user@example.com", True, None]
                ]
            def close(self): pass
        class DummyConn:
            def cursor(self): return DummyCursor()
            def close(self): pass
        return DummyConn()
    monkeypatch.setattr("app.api.routes.get_db_connection", fake_get_db_connection)
    client = TestClient(app)
    # Simulate auth by passing X-User-Email header
    response = client.get("/api/chores", headers={"X-User-Email": "user@example.com", "Authorization": "Bearer testtoken"})
    assert response.status_code == 200
    data = response.json()
    assert any(c['name'] == "Private Chore" for c in data)
    assert any(c['name'] == "Shared Chore" for c in data)
    # Simulate another user
    response2 = client.get("/api/chores", headers={"X-User-Email": "other@example.com", "Authorization": "Bearer testtoken"})
    data2 = response2.json()
    assert not any(c['name'] == "Private Chore" for c in data2)
    assert any(c['name'] == "Shared Chore" for c in data2)
