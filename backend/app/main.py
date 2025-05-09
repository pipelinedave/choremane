import logging
import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_mcp import FastApiMCP
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth

from app.api.routes import api_router
from app.api.mcp_routes import router as mcp_router
from app.api.auth_routes import auth_router
from app.database import get_db_connection
from app.auth import get_current_user
from app.models import User, Token

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
            
        # Check if users table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            logging.info("Creating users table")
            cur.execute("""
                CREATE TABLE users (
                    email VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255),
                    given_name VARCHAR(255),
                    family_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logging.info("Users table created successfully")
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# Run migrations on startup
run_migrations()

app = FastAPI()

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "supersecret"))

# Configure OAuth client
oauth = OAuth()
oauth.register(
    name="dex",
    client_id=os.getenv("OAUTH_CLIENT_ID", "choremane"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET", "choremane-secret"),
    server_metadata_url=f"{os.getenv('DEX_ISSUER_URL', 'https://dex.stillon.top')}/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)
app.include_router(mcp_router)
app.include_router(auth_router)

# OAuth login route
@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.dex.authorize_redirect(request, redirect_uri)

# OAuth callback route
@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.dex.authorize_access_token(request)
        user_info = await oauth.dex.parse_id_token(request, token)
        
        # Save user info to database
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO users (email, name, given_name, family_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    given_name = EXCLUDED.given_name, 
                    family_name = EXCLUDED.family_name,
                    last_login = CURRENT_TIMESTAMP
                """,
                (
                    user_info["email"],
                    user_info.get("name", ""),
                    user_info.get("given_name", ""),
                    user_info.get("family_name", "")
                )
            )
            conn.commit()
        except Exception as e:
            logging.error(f"Error saving user: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
        
        # Return tokens to frontend
        frontend_redirect_url = os.getenv("FRONTEND_URL", "https://chores.stillon.top")
        if "localhost" in str(request.base_url):
            frontend_redirect_url = "http://localhost:8080"
            
        redirect_url = f"{frontend_redirect_url}/auth-callback?token={token['access_token']}&id_token={token['id_token']}&expires_in={token['expires_in']}"
        if 'refresh_token' in token:
            redirect_url += f"&refresh_token={token['refresh_token']}"
        
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        logging.error(f"Auth callback error: {e}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication failed"}
        )

@app.get("/auth/user", response_model=User)
async def get_user(current_user: User = Depends(get_current_user)):
    return current_user

# Initialize and mount FastAPI-MCP
mcp = FastApiMCP(app)
mcp.mount()
