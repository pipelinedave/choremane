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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
