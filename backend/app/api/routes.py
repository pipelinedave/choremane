import json
import logging
from datetime import datetime, timedelta, date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List

from app.database import get_db_connection
from app.models import Chore, UndoRequest
from app.utils import log_action
from app.api.mcp_routes import router as mcp_router

api_router = APIRouter(prefix="/api")

@api_router.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(content="OK", status_code=200)

@api_router.post("/cors-test")
def cors_test():
    return {"message": "CORS test successful"}

@api_router.get("/status")
def status_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
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
def get_chores(request: Request):
    """
    Fetch chores visible to the current user:
    - All shared chores (is_private = false)
    - Private chores owned by the user (is_private = true and owner_email = user)
    """
    user_email = request.headers.get("X-User-Email")  # In production, extract from auth/session
    logging.info(f"Fetching chores for user: {user_email}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, interval_days, due_date, done, done_by, archived, owner_email, is_private
            FROM chores
            WHERE archived = FALSE AND (is_private = FALSE OR (is_private = TRUE AND owner_email = %s))
            ORDER BY due_date ASC
            """,
            (user_email,)
        )
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
                owner_email=row[7],
                is_private=row[8],
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
def add_chore(chore: Chore, request: Request):
    user_email = request.headers.get("X-User-Email")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO chores (name, interval_days, due_date, archived, owner_email, is_private)
            VALUES (%s, %s, %s, FALSE, %s, %s) RETURNING id
            """,
            (chore.name, chore.interval_days, chore.due_date, user_email if chore.is_private else None, chore.is_private)
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
            original_chore_id = action_details["chore_id"]
            original_due_date = action_details.get("previous_due_date", date.today().isoformat())
            cur.execute(
                "UPDATE chores SET done = FALSE, done_by = %s, due_date = %s WHERE id = %s",
                (None, original_due_date, original_chore_id)
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
        due_date_str = due_date.isoformat() if isinstance(due_date, date) else due_date
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
    import os
    version_tag = os.getenv("VERSION_TAG", "unknown")
    backend_image = os.getenv("BACKEND_IMAGE", "unknown")
    frontend_image = os.getenv("FRONTEND_IMAGE", "unknown")
    return {
        "version_tag": version_tag,
        "backend_image": backend_image,
        "frontend_image": frontend_image
    }
