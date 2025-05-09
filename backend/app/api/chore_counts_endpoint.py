import json
import logging
from datetime import datetime, timedelta, date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Dict

from app.database import get_db_connection
from app.models import Chore
from app.api.routes import api_router


@api_router.get("/chores/count")
def get_chore_counts(request: Request) -> Dict[str, int]:
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
