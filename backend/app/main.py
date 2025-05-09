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

# Check if we should use mock auth for development
USE_MOCK_AUTH = os.getenv("USE_MOCK_AUTH", "false").lower() == "true"
DEX_ISSUER_URL = os.getenv("DEX_ISSUER_URL", "https://dex.stillon.top")

if not USE_MOCK_AUTH:
    try:
        oauth.register(
            name="dex",
            client_id=os.getenv("OAUTH_CLIENT_ID", "choremane"),
            client_secret=os.getenv("OAUTH_CLIENT_SECRET", "choremane-secret"),
            server_metadata_url=f"{DEX_ISSUER_URL}/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid email profile"
            }
        )
        logging.info(f"OAuth client registered: client_id={os.getenv('OAUTH_CLIENT_ID', 'choremane')}")
        logging.info(f"DEX issuer URL: {DEX_ISSUER_URL}")
    except Exception as e:
        logging.error(f"Error registering OAuth client: {e}")
        logging.warning("Falling back to mock authentication for development")
        USE_MOCK_AUTH = True

logging.info(f"Using mock authentication: {USE_MOCK_AUTH}")
logging.info(f"Frontend URL: {os.getenv('FRONTEND_URL', 'https://chores.stillon.top')}")

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

# Import mock auth
from app.mock_auth import mock_login, mock_login_page, mock_callback, mock_refresh

# Add route for mock login page 
@app.get("/auth/mock-login-page")
async def mock_login_page_route(request: Request):
    return await mock_login_page(request)

# Add route for mock callback
@app.post("/auth/mock-callback")
async def mock_callback_route(request: Request):
    return await mock_callback(request)

# OAuth login route
@app.get("/auth/login")
async def login(request: Request):
    if USE_MOCK_AUTH:
        return await mock_login(request)
    
    redirect_uri = request.url_for("auth_callback")
    logging.info(f"Login redirect URI: {redirect_uri}")
    logging.info(f"DEX_ISSUER_URL: {DEX_ISSUER_URL}")
    logging.info(f"OAUTH_CLIENT_ID: {os.getenv('OAUTH_CLIENT_ID', 'choremane')}")
    return await oauth.dex.authorize_redirect(request, redirect_uri)

# OAuth callback route
@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        if USE_MOCK_AUTH:
            # This shouldn't be called in mock mode, but just in case
            logging.warning("OAuth callback called in mock auth mode")
            return await mock_callback(request)
            
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
            
        redirect_url = f"{frontend_redirect_url}/auth-callback?token={token['access_token']}&id_token={token['id_token']}&expires_in={token['expires_in']}"
        if 'refresh_token' in token:
            redirect_url += f"&refresh_token={token['refresh_token']}"
        
        logging.info(f"Redirecting to: {frontend_redirect_url}/auth-callback")
        
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
