import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from app.database import get_db_connection

router = APIRouter()

@router.get("/chores/household-health")
def get_household_health(request: Request) -> Dict[str, int]:
    """
    Calculate and return the household health score (0-100).
    Logic mirrors the previous frontend implementation:
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
        
        if not rows:
            return {"score": 100}

        total_score = 0
        active_chore_count = 0
        now = datetime.now()

        for row in rows:
            due_date = row[0]
            interval_days = row[1]
            
            # Ensure due_date is a datetime object for comparison
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date)
            # Check if it is a date object (but not datetime)
            elif hasattr(due_date, 'year') and not isinstance(due_date, datetime):
                 # Convert date to datetime at midnight
                 due_date = datetime.combine(due_date, datetime.min.time())

            interval_ms = interval_days * 24 * 60 * 60 * 1000
            # Python datetime subtraction gives timedelta
            diff = now - due_date
            diff_ms = diff.total_seconds() * 1000
            
            score = 100
            
            if diff_ms > 0:
                # OVERDUE
                overdue_ratio = diff_ms / interval_ms
                # Decay 80 -> 0
                score = max(0, 80 - (overdue_ratio * 80))
            else:
                # NOT OVERDUE (Fresh to Standard)
                # diff_ms is negative
                time_until_due = -diff_ms
                fraction_elapsed = 1 - (time_until_due / interval_ms)
                
                safe_fraction = max(0, min(1, fraction_elapsed))
                
                if safe_fraction <= 0.5:
                    score = 100
                else:
                    # 0.5 -> 1.0  maps to 100 -> 80
                    score = 100 + ((safe_fraction - 0.5) * -40)
            
            total_score += score
            active_chore_count += 1
            
        final_score = 100 if active_chore_count == 0 else round(total_score / active_chore_count)
        
        return {"score": int(final_score)}

    except Exception as e:
        logging.error(f"Error calculating household health: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate household health")
    finally:
        cur.close()
        conn.close()
