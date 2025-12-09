import logging
from typing import Dict

from fastapi import APIRouter, HTTPException, Request

from app.database import get_db_connection
from app.services import calculate_household_health_score

router = APIRouter()


@router.get("/chores/household-health")
def get_household_health(request: Request) -> Dict[str, int]:
    """
    Calculate and return the household health score (0-100).
    Logic:
    - Fresh (0-50% elapsed): 100
    - Standard (50-100% elapsed): Decays 100 -> 80
    - Overdue (>100% elapsed): Decays 80 -> 0 based on overdue amount
    """
    user_email = request.headers.get("X-User-Email")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch all active chores relevant to the score
        query = """
            SELECT due_date, interval_days 
            FROM chores 
            WHERE archived = FALSE 
            AND interval_days IS NOT NULL 
            AND interval_days > 0
            AND (is_private = FALSE OR (is_private = TRUE AND owner_email = %s))
        """
        cur.execute(query, (user_email,))
        rows = cur.fetchall()

        score = calculate_household_health_score(rows)
        return {"score": score}

    except Exception as e:
        logging.error(f"Error calculating household health: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate household health"
        )
    finally:
        cur.close()
        conn.close()
