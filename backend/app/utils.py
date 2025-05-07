import json
import logging
from datetime import datetime, date
from .database import get_db_connection

# Utility for logging actions
def log_action(chore_id, done_by, action_type, action_details=None):
    if isinstance(action_details, dict):
        action_details = {
            key: (value.isoformat() if isinstance(value, (datetime, date)) else value)
            for key, value in action_details.items()
        }
    action_details_str = json.dumps(action_details) if action_details else "{}"
    logging.info(f"Logging action for chore_id={chore_id}, action_type={action_type}, details={action_details_str}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Special case for system-level actions like import/export that don't relate to a specific chore
        if action_type in ["import", "export"] and chore_id is None:
            # Don't try to log to database for these system operations
            logging.info(f"System operation: {action_type}, details stored in application logs only")
            return
        
        # Normal case - log to database
        cur.execute(
            """
            INSERT INTO chore_logs (chore_id, done_by, action_type, action_details)
            VALUES (%s, %s, %s, %s)
            """,
            (chore_id, done_by, action_type, action_details_str)
        )
        conn.commit()
        logging.info(f"Action logged successfully for action_type={action_type}")
    except Exception as e:
        logging.error(f"Error logging action for chore_id={chore_id}: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
