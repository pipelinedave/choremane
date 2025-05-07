import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from app.api.routes import api_router
from app.api.mcp_routes import router as mcp_router
from app.database import get_db_connection

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def run_migrations():
    """Run database migrations on startup"""
    logging.info("Running database migrations...")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if chore_logs.chore_id allows NULL values
        cur.execute("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'chore_logs' AND column_name = 'chore_id'
        """)
        result = cur.fetchone()
        if result and result[0] == 'NO':  # If NOT NULL constraint exists
            logging.info("Applying migration: Allow NULL for chore_id in chore_logs")
            cur.execute("ALTER TABLE chore_logs ALTER COLUMN chore_id DROP NOT NULL")
            conn.commit()
            logging.info("Migration completed successfully")
        else:
            logging.info("Migration already applied or not needed")
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# Run migrations on startup
run_migrations()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(mcp_router)

# Initialize and mount FastAPI-MCP
mcp = FastApiMCP(app)
mcp.mount()
