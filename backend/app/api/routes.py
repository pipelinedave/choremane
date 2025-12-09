import json
import logging
from datetime import datetime, timedelta, date

from fastapi import APIRouter, HTTPException, Request

from fastapi.responses import JSONResponse
from typing import List

from app.database import get_db_connection
from app.models import Chore, UndoRequest
from app.utils import log_action
from app.api.household_health_endpoint import router as household_health_router

api_router = APIRouter(prefix="/api")
api_router.include_router(household_health_router)


@api_router.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(content="OK", status_code=200)


def _to_iso_date(value):
    """Convert date/datetime values to ISO string without altering strings/None."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


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
        return {
            "status": "OK",
            "message": "Backend is healthy and database is reachable",
        }
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return {"status": "ERROR", "message": "Backend or database connectivity issue"}


@api_router.get("/logs")
def get_logs(request: Request):
    """
    Return logs visible to the current user. Logs for shared chores are always
    included; logs for private chores are limited to the owner. System-level
    logs without a chore_id are also returned.
    """
    user_email = request.headers.get("X-User-Email")
    logging.info(f"Fetching chore logs for user: {user_email}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT l.id, l.chore_id, l.done_by, l.done_at, l.action_details, l.action_type
            FROM chore_logs l
            LEFT JOIN chores c ON l.chore_id = c.id
            WHERE c.id IS NULL
               OR c.is_private = FALSE
               OR (c.is_private = TRUE AND c.owner_email = %s)
            ORDER BY l.done_at DESC
            """,
            (user_email,),
        )
        logs = cur.fetchall()
        if not logs:
            logging.info("No logs found")
            return []

        def parse_details(raw_details):
            if raw_details is None:
                return {}
            if isinstance(raw_details, str):
                try:
                    return json.loads(raw_details)
                except json.JSONDecodeError:
                    logging.warning(
                        "Unable to decode action_details string; returning raw value"
                    )
                    return raw_details
            return raw_details

        normalized_logs = []
        for row in logs:
            action_type = row[5] if len(row) > 5 else None
            normalized_logs.append(
                {
                    "id": row[0],
                    "chore_id": row[1],
                    "done_by": row[2],
                    "done_at": row[3].isoformat() if row[3] else None,
                    "action_details": parse_details(row[4] if len(row) > 4 else None),
                    "action_type": action_type,
                }
            )
        return normalized_logs
    except Exception as e:
        logging.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch logs")
    finally:
        cur.close()
        conn.close()


@api_router.get("/chores", response_model=List[Chore])
def get_chores(request: Request, page: int = 1, limit: int = 10):
    """
    Fetch chores visible to the current user:
    - All shared chores (is_private = false)
    - Private chores owned by the user (is_private = true and owner_email = user)

    Supports pagination with page and limit parameters.
    """
    user_email = request.headers.get(
        "X-User-Email"
    )  # In production, extract from auth/session
    logging.info(
        f"Fetching chores for user: {user_email}, page: {page}, limit: {limit}"
    )

    # Calculate offset based on page and limit
    offset = (page - 1) * limit

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, interval_days, due_date, done, done_by, archived, owner_email, is_private, last_done
            FROM chores
            WHERE archived = FALSE AND (is_private = FALSE OR (is_private = TRUE AND owner_email = %s))
            ORDER BY due_date ASC
            LIMIT %s OFFSET %s
            """,
            (user_email, limit, offset),
        )
        rows = cur.fetchall()
        columns = (
            [desc[0] for desc in cur.description]
            if getattr(cur, "description", None)
            else []
        )

        chores = []
        for row in rows:
            record = dict(zip(columns, row)) if columns else {}
            chore_owner = (
                record.get("owner_email")
                if record
                else (row[7] if len(row) > 7 else None)
            )
            is_private = (
                record.get("is_private", False)
                if record
                else (row[8] if len(row) > 8 else False)
            )

            if is_private and chore_owner and chore_owner != user_email:
                continue

            chores.append(
                Chore(
                    id=record.get("id", row[0] if row else None),
                    name=record.get("name", row[1] if len(row) > 1 else None),
                    interval_days=record.get(
                        "interval_days", row[2] if len(row) > 2 else None
                    ),
                    due_date=str(
                        _to_iso_date(
                            record.get("due_date", row[3] if len(row) > 3 else "")
                        )
                    ),
                    done=record.get("done", row[4] if len(row) > 4 else False),
                    done_by=record.get("done_by", row[5] if len(row) > 5 else None),
                    archived=record.get("archived", row[6] if len(row) > 6 else False),
                    last_done=_to_iso_date(
                        record.get("last_done", row[9] if len(row) > 9 else None)
                    ),
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
            (
                chore.name,
                chore.interval_days,
                chore.due_date,
                user_email if chore.is_private else None,
                chore.is_private,
            ),
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
        cur.execute(
            "SELECT action_type, action_details FROM chore_logs WHERE id = %s",
            (undo_request.log_id,),
        )
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
                ),
            )
        elif action_type == "archived":
            cur.execute(
                "UPDATE chores SET archived = FALSE WHERE id = %s",
                (action_details["id"],),
            )
        elif action_type == "marked_done":
            original_chore_id = action_details["chore_id"]
            original_due_date = action_details.get(
                "previous_due_date", date.today().isoformat()
            )
            previous_last_done = action_details.get("previous_last_done")
            cur.execute(
                "UPDATE chores SET done = FALSE, done_by = %s, due_date = %s, last_done = %s WHERE id = %s",
                (None, original_due_date, previous_last_done, original_chore_id),
            )
        else:
            raise HTTPException(
                status_code=400, detail="Undo not supported for this action type"
            )
        conn.commit()
        log_chore_id = (
            action_details.get("id")
            or action_details.get("chore_id")
            or action_details.get("previous_state", {}).get("id")
        )
        log_action(
            log_chore_id,
            None,
            "undo",
            action_details={"action_type": action_type, "undone": True},
            conn=conn,
        )
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
            (
                updated_chore.name,
                updated_chore.interval_days,
                updated_chore.due_date,
                chore_id,
            ),
        )
        conn.commit()
        log_action(
            chore_id,
            None,
            "updated",
            action_details={"previous_state": previous_state_dict},
        )
        return {"message": f"Chore {chore_id} updated successfully"}
    except HTTPException:
        conn.rollback()
        raise
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
        cur.execute(
            "SELECT interval_days, due_date, last_done FROM chores WHERE id = %s",
            (chore_id,),
        )
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Chore not found or incomplete")
        interval_days, due_date, last_done = result

        today_date = date.today()
        last_done_date = None
        if last_done:
            if isinstance(last_done, datetime):
                last_done_date = last_done.date()
            elif isinstance(last_done, date):
                last_done_date = last_done
            elif isinstance(last_done, str):
                last_done_date = datetime.fromisoformat(last_done).date()
        if last_done_date == today_date:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Chore already completed today",
                    "last_done": today_date.isoformat(),
                },
            )

        due_date_str = due_date.isoformat() if isinstance(due_date, date) else due_date
        new_due_date = (today_date + timedelta(days=interval_days)).isoformat()
        cur.execute(
            """
            UPDATE chores 
            SET done = TRUE, done_by = %s, due_date = %s, last_done = %s 
            WHERE id = %s
            """,
            (done_by, new_due_date, today_date, chore_id),
        )
        conn.commit()
        log_action(
            chore_id,
            done_by,
            "marked_done",
            action_details={
                "chore_id": chore_id,
                "new_due_date": new_due_date,
                "previous_due_date": due_date_str,
                "previous_last_done": _to_iso_date(last_done),
            },
            conn=conn,
        )
        return {
            "message": f"Chore {chore_id} marked as done",
            "new_due_date": new_due_date,
            "last_done": today_date.isoformat(),
            "done_by": done_by,
        }
    except HTTPException:
        conn.rollback()
        raise
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
    except HTTPException:
        conn.rollback()
        raise
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
    except HTTPException:
        conn.rollback()
        raise
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
    user_email = request.headers.get(
        "X-User-Email"
    )  # In production, extract from auth/session
    logging.info(f"Fetching archived chores for user: {user_email}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, interval_days, due_date, done, done_by, archived, owner_email, is_private, last_done
            FROM chores
            WHERE archived = TRUE AND (is_private = FALSE OR (is_private = TRUE AND owner_email = %s))
            ORDER BY due_date ASC
            """,
            (user_email,),
        )
        rows = cur.fetchall()
        chores = [
            Chore(
                id=row[0],
                name=row[1],
                interval_days=row[2],
                due_date=str(_to_iso_date(row[3])),
                done=row[4],
                done_by=row[5],
                archived=row[6],
                owner_email=row[7] if len(row) > 7 else None,
                is_private=row[8] if len(row) > 8 else False,
                last_done=_to_iso_date(row[9] if len(row) > 9 else None),
            )
            for row in rows
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
        "frontend_image": frontend_image,
    }


@api_router.post("/import")
async def import_data(request: Request):
    """
    Import data from a JSON file.
    Expects a JSON object with:
    - 'chores': array of chore objects
    - 'logs' (optional): array of chore log objects
    """
    try:
        import_data = await request.json()
        user_email = request.headers.get("X-User-Email")

        if not import_data.get("chores"):
            raise HTTPException(
                status_code=400, detail="No chores data found in the import file"
            )

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
                                is_private = %s, owner_email = %s, last_done = %s
                            WHERE id = %s
                            """,
                            (
                                chore["name"],
                                chore["interval_days"],
                                chore["due_date"],
                                chore.get("is_private", False),
                                user_email if chore.get("is_private", False) else None,
                                chore.get("last_done"),
                                chore["id"],
                            ),
                        )
                        imported_chores.append({"id": chore["id"], "status": "updated"})
                        continue

                # Insert as new chore
                cur.execute(
                    """
                    INSERT INTO chores (name, interval_days, due_date, archived, owner_email, is_private, last_done)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (
                        chore["name"],
                        chore["interval_days"],
                        chore["due_date"],
                        chore.get("archived", False),
                        user_email if chore.get("is_private", False) else None,
                        chore.get("is_private", False),
                        chore.get("last_done"),
                    ),
                )
                new_id = cur.fetchone()[0]
                imported_chores.append({"id": new_id, "status": "created"})
            except Exception as e:
                logging.error(f"Error importing chore {chore.get('name')}: {e}")
                # Continue with next chore

        imported_logs = []
        logs_payload = import_data.get("logs", [])
        for log in logs_payload:
            try:
                action_details = log.get("action_details") or log.get("details") or {}
                if isinstance(action_details, str):
                    try:
                        action_details = json.loads(action_details)
                    except json.JSONDecodeError:
                        logging.warning(
                            "Received unparseable action_details string during import; storing raw value"
                        )
                done_at = log.get("done_at")
                if done_at:
                    try:
                        done_at = datetime.fromisoformat(done_at)
                    except Exception:
                        logging.warning(
                            f"Invalid done_at format in imported log {log.get('id')}, using current time"
                        )
                        done_at = datetime.utcnow()
                cur.execute(
                    """
                    INSERT INTO chore_logs (chore_id, done_by, done_at, action_type, action_details)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        log.get("chore_id"),
                        log.get("done_by") or user_email,
                        done_at or datetime.utcnow(),
                        log.get("action_type") or "imported",
                        json.dumps(action_details),
                    ),
                )
                imported_logs.append(
                    {"chore_id": log.get("chore_id"), "status": "created"}
                )
            except Exception as e:
                logging.error(f"Error importing log entry {log.get('id')}: {e}")
                # Continue with next log

        conn.commit()
        log_action(
            None,
            user_email,
            "import",
            action_details={
                "imported_chores": imported_chores,
                "imported_logs": len(imported_logs),
            },
        )

        return {
            "message": "Import successful",
            "imported_chores": len(imported_chores),
            "imported_logs": len(imported_logs),
            "details": imported_chores,
        }
    except HTTPException:
        if "conn" in locals():
            conn.rollback()
        raise
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
            SELECT id, name, interval_days, due_date, done, done_by, archived, owner_email, is_private, last_done
            FROM chores
            WHERE is_private = FALSE OR (is_private = TRUE AND owner_email = %s)
            """,
            (user_email,),
        )
        chores = []
        for row in cur.fetchall():
            chore = dict(zip([desc[0] for desc in cur.description], row))
            # Convert date objects to string
            if isinstance(chore["due_date"], (datetime, date)):
                chore["due_date"] = chore["due_date"].isoformat()
            if isinstance(chore.get("last_done"), (datetime, date)):
                chore["last_done"] = chore["last_done"].isoformat()
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

        log_action(
            None,
            user_email,
            "export",
            action_details={"chore_count": len(chores), "log_count": len(logs)},
        )

        return {"chores": chores, "logs": logs}
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
            (user_email, tomorrow, next_week),
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
            "upcoming": upcoming_count,
        }
    except Exception as e:
        logging.error(f"Error getting chore counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chore counts")
    finally:
        cur.close()
        conn.close()
