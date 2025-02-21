import logging
from datetime import datetime, timedelta, date
import os
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import psycopg2
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment-based configuration
DB_HOST = os.getenv("POSTGRES_HOST", "postgres-service")
DB_NAME = os.getenv("POSTGRES_DB", "choresdb")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
ALLOW_ORIGINS = os.getenv(
    "ALLOW_ORIGINS",
    "https://chores.stillon.top,https://chores-staging.stillon.top,http://localhost:5000,http://127.0.0.1:5000"
).split(",")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create an API router with the /api prefix
api_router = APIRouter(prefix="/api")

@api_router.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(content="OK", status_code=200)

@api_router.post("/cors-test")
def cors_test():
    return {"message": "CORS test successful"}

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Models
class Chore(BaseModel):
    id: Optional[int] = None
    name: str
    interval_days: int
    due_date: str
    done: bool = Field(default=False)
    done_by: Optional[str] = Field(default=None)
    archived: bool = Field(default=False)

class UndoRequest(BaseModel):
    log_id: int

# Utility for logging actions
def log_action(chore_id, done_by, action_type, action_details=None):
    if isinstance(action_details, dict):
        # Ensure dates in action_details are serializable
        action_details = {
            key: (value.isoformat() if isinstance(value, (datetime, date)) else value)
            for key, value in action_details.items()
        }

    # Serialize action_details to JSON string
    action_details_str = json.dumps(action_details) if action_details else "{}"
    logging.info(f"Logging action for chore_id={chore_id}, action_type={action_type}, details={action_details_str}")

    # Insert into database
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO chore_logs (chore_id, done_by, action_type, action_details)
            VALUES (%s, %s, %s, %s)
            """,
            (chore_id, done_by, action_type, action_details_str)
        )
        conn.commit()
        logging.info(f"Action logged successfully for chore_id={chore_id}")
    except Exception as e:
        logging.error(f"Error logging action for chore_id={chore_id}: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# Endpoints
@api_router.get("/status")
def status_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Ensure database connectivity
        cur.execute("SELECT 1")
        cur.close()
        conn.close()

        return {"status": "OK", "message": "Backend is healthy and database is reachable"}

    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return {"status": "ERROR", "message": "Backend or database connectivity issue"}

@api_router.get("/logs")
def get_logs():
    logging.info("Fetching chore logs")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, chore_id, done_by, done_at, action_details
        FROM chore_logs
        ORDER BY done_at DESC
    """)
    logs = cur.fetchall()
    if not logs:
        logging.info("No logs found")
        return []

    cur.close()
    conn.close()

    # Deserialize action_details and ensure proper formatting
    return [
        {
            "id": row[0],
            "chore_id": row[1],
            "done_by": row[2],
            "done_at": row[3].isoformat() if row[3] else None,
            "details": json.loads(row[4]) if row[4] and isinstance(row[4], str) else "No details available"
        }
        for row in logs
    ]

@api_router.get("/chores", response_model=List[Chore])
def get_chores():
    logging.info("Fetching all chores...")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name, interval_days, due_date, done, done_by, archived FROM chores WHERE archived = FALSE ORDER BY due_date ASC")
        rows = cur.fetchall()
        chores = [
            Chore(
                id=row[0],
                name=row[1],
                interval_days=row[2],
                due_date=str(row[3]),
                done=row[4],
                done_by=row[5],
                archived=row[6],
            ) for row in rows
        ]
        return chores
    except Exception as e:
        logging.error(f"Error fetching chores: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chores")
    finally:
        cur.close()
        conn.close()

@api_router.post("/chores")
def add_chore(chore: Chore):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO chores (name, interval_days, due_date, archived) VALUES (%s, %s, %s, FALSE) RETURNING id",
            (chore.name, chore.interval_days, chore.due_date)
        )
        chore_id = cur.fetchone()[0]
        conn.commit()
        log_action(chore_id, None, "created", action_details=chore.dict())
        return {"message": "Chore added successfully", "id": chore_id}
    except Exception as e:
        logging.error(f"Error adding chore: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to add chore")
    finally:
        cur.close()
        conn.close()

@api_router.post("/undo")
def undo_action(undo_request: UndoRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT action_type, action_details FROM chore_logs WHERE id = %s", (undo_request.log_id,))
        log_entry = cur.fetchone()
        if not log_entry:
            raise HTTPException(status_code=404, detail="Log entry not found")

        action_type, action_details = log_entry
        if isinstance(action_details, str):
            action_details = json.loads(action_details)

        logging.info(f"Undoing action: {action_type} with details: {action_details}")

        if action_type == "created":
            cur.execute("DELETE FROM chores WHERE id = %s", (action_details["id"],))
        elif action_type == "updated":
            cur.execute(
                """
                UPDATE chores SET name = %s, interval_days = %s, due_date = %s WHERE id = %s
                """,
                (
                    action_details["previous_state"]["name"],
                    action_details["previous_state"]["interval_days"],
                    action_details["previous_state"]["due_date"],
                    action_details["previous_state"]["id"],
                )
            )
        elif action_type == "archived":
            cur.execute("UPDATE chores SET archived = FALSE WHERE id = %s", (action_details["id"],))
        elif action_type == "marked_done":
            # The previous code references variables done_by/new_due_date/chore_id not defined here,
            # this is a bug in the original code. Assuming we had them, we’d revert done state.
            # For now, we’ll assume we have to restore from action_details:
            original_chore_id = action_details["chore_id"]
            original_due_date = action_details["previous_due_date"] if "previous_due_date" in action_details else None
            original_done_by = None
            if original_due_date is None:
                original_due_date = date.today().isoformat()
            cur.execute(
                "UPDATE chores SET done = FALSE, done_by = %s, due_date = %s WHERE id = %s",
                (original_done_by, original_due_date, original_chore_id)
            )
        else:
            raise HTTPException(status_code=400, detail="Undo not supported for this action type")

        conn.commit()
        log_action(action_details["id"], None, "undo", action_details={"action_type": action_type, "undone": True})
        return {"message": f"Action {action_type} undone successfully"}
    except Exception as e:
        conn.rollback()
        logging.error(f"Error undoing action: {e}")
        raise HTTPException(status_code=500, detail="Failed to undo action")
    finally:
        cur.close()
        conn.close()

@api_router.put("/chores/{chore_id}")
def update_chore(chore_id: int, updated_chore: Chore):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM chores WHERE id = %s", (chore_id,))
        previous_state = cur.fetchone()
        if not previous_state:
            raise HTTPException(status_code=404, detail="Chore not found")

        previous_state_dict = (
            dict(zip([desc[0] for desc in cur.description], previous_state))
            if cur.description and previous_state
            else {}
        )

        for key, value in previous_state_dict.items():
            if isinstance(value, (datetime, date)):
                previous_state_dict[key] = value.isoformat()

        cur.execute(
            """
            UPDATE chores SET name = %s, interval_days = %s, due_date = %s
            WHERE id = %s
            """,
            (updated_chore.name, updated_chore.interval_days, updated_chore.due_date, chore_id)
        )
        conn.commit()

        log_action(chore_id, None, "updated", action_details={"previous_state": previous_state_dict})
        return {"message": f"Chore {chore_id} updated successfully"}
    except Exception as e:
        conn.rollback()
        logging.error(f"Error updating chore: {e}")
        raise HTTPException(status_code=500, detail="Failed to update chore")
    finally:
        cur.close()
        conn.close()

@api_router.put("/chores/{chore_id}/done")
def mark_chore_done(chore_id: int, payload: dict):
    done_by = payload.get("done_by")
    if not done_by:
        raise HTTPException(status_code=422, detail="done_by is required")

    logging.info(f"Marking chore {chore_id} as done by {done_by}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT interval_days, due_date FROM chores WHERE id = %s", (chore_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Chore not found or incomplete")

        interval_days, due_date = result

        if isinstance(due_date, date):
            due_date_str = due_date.isoformat()
        else:
            due_date_str = due_date

        new_due_date = (date.today() + timedelta(days=interval_days)).isoformat()

        cur.execute(
            "UPDATE chores SET done = TRUE, done_by = %s, due_date = %s WHERE id = %s",
            (done_by, new_due_date, chore_id)
        )
        conn.commit()

        log_action(chore_id, done_by, "marked_done", action_details={"chore_id": chore_id, "new_due_date": new_due_date, "previous_due_date": due_date_str})
        return {"message": f"Chore {chore_id} marked as done", "new_due_date": new_due_date}

    except Exception as e:
        conn.rollback()
        logging.error(f"Error marking chore as done: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark chore as done")
    finally:
        cur.close()
        conn.close()

@api_router.put("/chores/{chore_id}/archive")
def archive_chore(chore_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE chores SET archived = TRUE WHERE id = %s", (chore_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Chore not found")
        conn.commit()
        log_action(chore_id, None, "archived")
        return {"message": f"Chore {chore_id} archived successfully"}
    except Exception as e:
        conn.rollback()
        logging.error(f"Error archiving chore: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive chore")
    finally:
        cur.close()
        conn.close()

@api_router.get("/version")
def get_version_info():
    version_tag = os.getenv("VERSION_TAG", "unknown")
    backend_image = os.getenv("BACKEND_IMAGE", "unknown")
    frontend_image = os.getenv("FRONTEND_IMAGE", "unknown")

    return {
        "version_tag": version_tag,
        "backend_image": backend_image,
        "frontend_image": frontend_image
    }

# Include the API router in the FastAPI application
app.include_router(api_router)
