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
def get_chores(request: Request, page: int = 1, limit: int = 10):
    """
    Fetch chores visible to the current user:
    - All shared chores (is_private = false)
    - Private chores owned by the user (is_private = true and owner_email = user)
    
    Supports pagination with page and limit parameters.
    """
    user_email = request.headers.get("X-User-Email")  # In production, extract from auth/session
    logging.info(f"Fetching chores for user: {user_email}, page: {page}, limit: {limit}")
    
    # Calculate offset based on page and limit
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, interval_days, due_date, done, done_by, archived, owner_email, is_private
            FROM chores
            WHERE archived = FALSE AND (is_private = FALSE OR (is_private = TRUE AND owner_email = %s))
            ORDER BY due_date ASC
            LIMIT %s OFFSET %s
            """,
            (user_email, limit, offset)
        )
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if getattr(cur, "description", None) else []

        chores = []
        for row in rows:
            record = dict(zip(columns, row)) if columns else {}
            chore_owner = record.get("owner_email") if record else (row[7] if len(row) > 7 else None)
            is_private = record.get("is_private", False) if record else (row[8] if len(row) > 8 else False)

            if is_private and chore_owner and chore_owner != user_email:
                continue

            chores.append(
                Chore(
                    id=record.get("id", row[0] if row else None),
                    name=record.get("name", row[1] if len(row) > 1 else None),
                    interval_days=record.get("interval_days", row[2] if len(row) > 2 else None),
                    due_date=str(record.get("due_date", row[3] if len(row) > 3 else "")),
                    done=record.get("done", row[4] if len(row) > 4 else False),
                    done_by=record.get("done_by", row[5] if len(row) > 5 else None),
                    archived=record.get("archived", row[6] if len(row) > 6 else False),
                    owner_email=chore_owner,
                    is_private=is_private,
                )
            )
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
        log_action(chore_id, None, "created", action_details=chore.dict(), conn=conn)
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
        log_chore_id = action_details.get("id") or action_details.get("chore_id") or action_details.get("previous_state", {}).get("id")
        log_action(log_chore_id, None, "undo", action_details={"action_type": action_type, "undone": True}, conn=conn)
        return {"message": f"Action {action_type} undone successfully"}
    except HTTPException:
        conn.rollback()
        raise
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
        log_action(
            chore_id,
            done_by,
            "marked_done",
            action_details={"chore_id": chore_id, "new_due_date": new_due_date, "previous_due_date": due_date_str},
            conn=conn,
        )
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
        log_action(chore_id, None, "archived", conn=conn)
        return {"message": f"Chore {chore_id} archived successfully"}
    except Exception as e:
        conn.rollback()
        logging.error(f"Error archiving chore: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive chore")
    finally:
        cur.close()
        conn.close()

@api_router.put("/chores/{chore_id}/unarchive")
def unarchive_chore(chore_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE chores SET archived = FALSE WHERE id = %s", (chore_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Chore not found")
        conn.commit()
        log_action(chore_id, None, "unarchived", conn=conn)
        return {"message": f"Chore {chore_id} unarchived successfully"}
    except Exception as e:
        conn.rollback()
        logging.error(f"Error unarchiving chore: {e}")
        raise HTTPException(status_code=500, detail="Failed to unarchive chore")
    finally:
        cur.close()
        conn.close()

@api_router.get("/chores/archived", response_model=List[Chore])
def get_archived_chores(request: Request):
    """
    Fetch archived chores visible to the current user:
    - All shared archived chores (is_private = false, archived = true)
    - Private archived chores owned by the user (is_private = true, archived = true, and owner_email = user)
    """
    user_email = request.headers.get("X-User-Email")  # In production, extract from auth/session
    logging.info(f"Fetching archived chores for user: {user_email}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, interval_days, due_date, done, done_by, archived, owner_email, is_private
            FROM chores
            WHERE archived = TRUE AND (is_private = FALSE OR (is_private = TRUE AND owner_email = %s))
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
        logging.error(f"Error fetching archived chores: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch archived chores")
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

@api_router.post("/import")
async def import_data(request: Request):
    """
    Import data from a JSON file.
    Expects a JSON object with:
    - 'chores': array of chore objects  
    """
    try:
        import_data = await request.json()
        user_email = request.headers.get("X-User-Email")
        
        if not import_data.get("chores"):
            raise HTTPException(status_code=400, detail="No chores data found in the import file")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        imported_chores = []
        for chore in import_data["chores"]:
            try:
                # Check if chore with this ID already exists
                if chore.get("id"):
                    cur.execute("SELECT id FROM chores WHERE id = %s", (chore["id"],))
                    if cur.fetchone():
                        # Update existing chore
                        cur.execute(
                            """
                            UPDATE chores 
                            SET name = %s, interval_days = %s, due_date = %s, 
                                is_private = %s, owner_email = %s
                            WHERE id = %s
                            """,
                            (
                                chore["name"], 
                                chore["interval_days"], 
                                chore["due_date"],
                                chore.get("is_private", False),
                                user_email if chore.get("is_private", False) else None,
                                chore["id"]
                            )
                        )
                        imported_chores.append({"id": chore["id"], "status": "updated"})
                        continue
                
                # Insert as new chore
                cur.execute(
                    """
                    INSERT INTO chores (name, interval_days, due_date, archived, owner_email, is_private)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (
                        chore["name"], 
                        chore["interval_days"], 
                        chore["due_date"],
                        chore.get("archived", False),
                        user_email if chore.get("is_private", False) else None,
                        chore.get("is_private", False)
                    )
                )
                new_id = cur.fetchone()[0]
                imported_chores.append({"id": new_id, "status": "created"})
            except Exception as e:
                logging.error(f"Error importing chore {chore.get('name')}: {e}")
                # Continue with next chore
        
        conn.commit()
        log_action(None, user_email, "import", action_details={"imported_chores": imported_chores})
        
        return {
            "message": "Import successful",
            "imported_chores": len(imported_chores),
            "details": imported_chores
        }
    except Exception as e:
        logging.error(f"Error during import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import data: {str(e)}")

@api_router.get("/export")
def export_data(request: Request):
    """
    Export all chores and logs for the current user.
    """
    user_email = request.headers.get("X-User-Email")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get chores (visible to this user)
        cur.execute(
            """
            SELECT id, name, interval_days, due_date, done, done_by, archived, owner_email, is_private
            FROM chores
            WHERE is_private = FALSE OR (is_private = TRUE AND owner_email = %s)
            """,
            (user_email,)
        )
        chores = []
        for row in cur.fetchall():
            chore = dict(zip([desc[0] for desc in cur.description], row))
            # Convert date objects to string
            if isinstance(chore["due_date"], (datetime, date)):
                chore["due_date"] = chore["due_date"].isoformat()
            chores.append(chore)
        
        # Get logs
        cur.execute(
            """
            SELECT id, chore_id, done_by, done_at, action_details, action_type
            FROM chore_logs
            ORDER BY done_at DESC
            """
        )
        logs = []
        for row in cur.fetchall():
            log = dict(zip([desc[0] for desc in cur.description], row))
            # Convert date objects to string
            if isinstance(log["done_at"], (datetime, date)):
                log["done_at"] = log["done_at"].isoformat()
            logs.append(log)
            
        log_action(None, user_email, "export", action_details={"chore_count": len(chores), "log_count": len(logs)})
        
        return {
            "chores": chores,
            "logs": logs
        }
    except Exception as e:
        logging.error(f"Error during export: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")
    finally:
        cur.close()
        conn.close()

@api_router.get("/chores/count")
def get_chore_counts(request: Request):
    """
    Get total counts of chores in different categories:
    - all: All non-archived chores
    - overdue: Chores with due date in the past
    - today: Chores due today
    - tomorrow: Chores due tomorrow
    - thisWeek: Chores due in the next week (excluding today and tomorrow)
    - upcoming: Chores due beyond next week
    """
    user_email = request.headers.get("X-User-Email")
    
    # Get today's date for comparisons
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Base query for all non-archived chores visible to the user
        base_query = """
            SELECT COUNT(*) 
            FROM chores 
            WHERE archived = FALSE AND (is_private = FALSE OR (is_private = TRUE AND owner_email = %s))
        """
        
        # Total non-archived chores
        cur.execute(base_query, (user_email,))
        total_count = cur.fetchone()[0]
        
        # Overdue chores
        cur.execute(base_query + " AND due_date < %s", (user_email, today))
        overdue_count = cur.fetchone()[0]
        
        # Due today
        cur.execute(base_query + " AND due_date = %s", (user_email, today))
        today_count = cur.fetchone()[0]
        
        # Due tomorrow
        cur.execute(base_query + " AND due_date = %s", (user_email, tomorrow))
        tomorrow_count = cur.fetchone()[0]
        
        # Due this week (after tomorrow and up to a week from today)
        cur.execute(
            base_query + " AND due_date > %s AND due_date <= %s", 
            (user_email, tomorrow, next_week)
        )
        this_week_count = cur.fetchone()[0]
        
        # Upcoming (beyond next week)
        cur.execute(base_query + " AND due_date > %s", (user_email, next_week))
        upcoming_count = cur.fetchone()[0]
        
        return {
            "all": total_count,
            "overdue": overdue_count,
            "today": today_count,
            "tomorrow": tomorrow_count,
            "thisWeek": this_week_count,
            "upcoming": upcoming_count
        }
    except Exception as e:
        logging.error(f"Error getting chore counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chore counts")
    finally:
        cur.close()
        conn.close()
