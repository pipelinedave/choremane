import logging
import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_mcp import FastApiMCP
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
import httpx

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
    conn = None
    cur = None
    try:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
        except Exception as e:
            logging.error(f"Skipping migrations: unable to connect to database ({e})")
            return

        # Create chores table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chores (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                interval_days INT NOT NULL,
                due_date DATE NOT NULL,
                done BOOLEAN DEFAULT FALSE,
                done_by VARCHAR(255),
                owner_email VARCHAR(255),
                is_private BOOLEAN DEFAULT FALSE,
                archived BOOLEAN DEFAULT FALSE
            )
        """)
        conn.commit()
        logging.info("Chores table created or already exists")

        # Create chore_logs table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chore_logs (
                id SERIAL PRIMARY KEY,
                chore_id INT,
                done_by VARCHAR(255),
                done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action_type VARCHAR(50) NOT NULL,
                action_details JSON DEFAULT NULL,
                FOREIGN KEY (chore_id) REFERENCES chores (id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        logging.info("Chore logs table created or already exists")

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
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Run migrations on startup
run_migrations()

app = FastAPI()

# Add session middleware for OAuth with secure cookie settings for production
is_prod_env = os.getenv("ENV", "production").lower() == "production"
session_secret = os.getenv("SESSION_SECRET", "supersecret")

app.add_middleware(
    SessionMiddleware, 
    secret_key=session_secret,
    # Set secure cookies in production to prevent session issues
    https_only=is_prod_env,  
    # Longer max_age in production to prevent premature session expiry
    max_age=3600 if is_prod_env else 1800,  
    # Use SameSite=Lax to ensure cookies work with redirects
    same_site="lax"  
)

logging.info(f"Session middleware configured with https_only={is_prod_env}, expires in {3600 if is_prod_env else 1800}s")

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

# OAuth login route - support both /auth/login and /api/auth/login paths
@app.get("/auth/login")
@app.get("/api/auth/login")
async def login(request: Request):
    if USE_MOCK_AUTH:
        return await mock_login(request)
    
    # Get the environment (staging or production)
    frontend_url = os.getenv("FRONTEND_URL", "")
    is_staging = "staging" in frontend_url
    
    # Determine if request is using HTTP or HTTPS
    is_https = request.url.scheme == "https" or (
        "x-forwarded-proto" in request.headers and 
        request.headers["x-forwarded-proto"] == "https"
    )
    
    # Hard-code the exact redirect URI that is registered in Dex config
    # Use the same scheme (HTTP/HTTPS) that the request came in on
    scheme = "https" if is_https else "http"
    
    if is_staging:
        redirect_uri = f"{scheme}://chores-staging.stillon.top/api/auth/callback"
    else:
        redirect_uri = f"{scheme}://chores.stillon.top/api/auth/callback"
    
    logging.info(f"Request scheme: {request.url.scheme}")
    logging.info(f"X-Forwarded-Proto: {request.headers.get('x-forwarded-proto', 'not set')}")
    logging.info(f"Using scheme: {scheme}")
    logging.info(f"Login redirect URI: {redirect_uri}")
    logging.info(f"DEX_ISSUER_URL: {DEX_ISSUER_URL}")
    logging.info(f"OAUTH_CLIENT_ID: {os.getenv('OAUTH_CLIENT_ID', 'choremane')}")
    
    # Generate and store a custom nonce in the session for verification later
    # This provides a fallback if the Authlib nonce mechanism fails
    import secrets
    custom_nonce = secrets.token_hex(16)
    request.session['custom_dex_nonce'] = custom_nonce
    logging.info(f"Generated and stored custom nonce in session: {custom_nonce[:5]}...")
    
    # Log session details before redirecting
    logging.info(f"Session contents before authorize_redirect: {dict(request.session)}")
    
    return await oauth.dex.authorize_redirect(request, redirect_uri)

# OAuth callback route - support both /auth/callback and /api/auth/callback paths
@app.get("/auth/callback")
@app.get("/api/auth/callback")
async def auth_callback(request: Request):
    token_data = None # Initialize to ensure it's available in except blocks
    original_id_token_string = None # To store id_token before parsing
    try:
        if USE_MOCK_AUTH:
            # This shouldn't be called in mock mode, but just in case
            logging.warning("OAuth callback called in mock auth mode")
            return await mock_callback(request)
            
        token_data = await oauth.dex.authorize_access_token(request)
        logging.info(f"Received token object from Dex (before parse_id_token): {token_data}")

        if 'id_token' not in token_data:
            logging.error(f"CRITICAL: 'id_token' missing from token_data received from Dex: {token_data}")
            raise KeyError("'id_token' not found in initial token response from Dex")
        
        original_id_token_string = token_data['id_token'] # Store it before it's potentially removed/modified

        # logging.info("Attempting to parse id_token...") # OLD LOG AND CALL
        # user_info = await oauth.dex.parse_id_token(request, token_data) # OLD CALL
        # logging.info(f"Successfully parsed id_token. User info claims: {user_info}") # OLD LOG
        # logging.info(f"Token object AFTER parse_id_token (and potential token_data.update()): {token_data}") # OLD LOG

        logging.info("Attempting to decode id_token string directly using oauth.dex.decode_id_token...")
        
        # Debug session contents to see what's available
        logging.info(f"Session contents: {dict(request.session)}")
        
        nonce = request.session.get('__dex_nonce__') # Retrieve nonce from session; 'dex' is the client name.
        logging.info(f"Retrieved nonce from session: {'Present' if nonce else 'MISSING'}")
        
        # Check for our custom nonce as a fallback
        custom_nonce = request.session.get('custom_dex_nonce')
        logging.info(f"Custom nonce found: {'Present' if custom_nonce else 'MISSING'}")
        
        if not nonce:
            logging.error("CRITICAL: Standard nonce not found in session for OIDC callback.")
            # Check if there's any potential nonce with a different key name
            possible_nonce_keys = [k for k in request.session.keys() if 'nonce' in k.lower()]
            if possible_nonce_keys:
                logging.info(f"However, found possible alternative nonce keys: {possible_nonce_keys}")
            
            # If we have our custom nonce, use it as a fallback
            if custom_nonce:
                logging.info("Using custom nonce as fallback for OIDC validation")
                nonce = custom_nonce
            else:
                logging.warn("No nonce available for OIDC validation, will attempt to skip nonce verification")
                # We'll proceed without a nonce and try to validate the token with only signature and standard claims
                # This is not ideal for security but allows debugging in scenarios where session is not maintained
                nonce = None

        try:
            # Log additional metadata about the OAuth client before decoding
            logging.info(f"DEX client metadata: {oauth.dex.server_metadata if hasattr(oauth.dex, 'server_metadata') else 'Not available'}")
            
            # Check for JWKS URI availability which is required for token verification
            jwks_uri = oauth.dex.server_metadata.get('jwks_uri') if hasattr(oauth.dex, 'server_metadata') else None
            logging.info(f"JWKS URI available: {'Yes - ' + jwks_uri if jwks_uri else 'No'}")
            
            # Call decode_id_token with the raw ID token JWT string and the retrieved nonce.
            # This method handles fetching JWKS, verifying signature, expiry, issuer, audience, and nonce.
            logging.info("Calling oauth.dex.decode_id_token...")
            
            # Set up claims options based on whether we have a nonce or not
            if nonce:
                logging.info("Using standard token validation with nonce")
                user_info = await oauth.dex.decode_id_token(
                    token=original_id_token_string,  # The raw ID token JWT string
                    nonce=nonce
                    # claims_options can be added here if specific claim validations are needed.
                    # Authlib uses default claims_params (like issuer, audience) from client's server_metadata.
                )
            else:
                # Attempt to manually decode and validate the token without nonce verification
                # This is a fallback for debugging purposes when session management issues occur
                logging.warn("Attempting ID token validation WITHOUT nonce verification")
                from authlib.jose import jwt
                from authlib.jose.errors import JoseError
                
                try:
                    # Get JWKS (JSON Web Key Set) from Dex
                    jwks_uri = oauth.dex.server_metadata.get('jwks_uri')
                    if not jwks_uri:
                        raise ValueError("JWKS URI not found in server metadata")
                        
                    async with httpx.AsyncClient() as client:
                        jwks_response = await client.get(jwks_uri)
                        jwks = jwks_response.json()
                        
                    # Validate the token with minimal claims validation (no nonce check)
                    claims_options = {
                        "iss": {"essential": True, "value": oauth.dex.server_metadata.get('issuer')},
                        "aud": {"essential": True, "value": os.getenv("OAUTH_CLIENT_ID", "choremane")},
                        "exp": {"essential": True},
                    }
                    
                    user_info = jwt.decode(
                        original_id_token_string,
                        jwks,
                        claims_options=claims_options
                    )
                    
                    logging.warn("Successfully decoded ID token WITHOUT nonce verification")
                except Exception as manual_decode_error:
                    logging.error(f"Manual token validation failed: {manual_decode_error}")
                    # Re-raise to be caught by the outer exception handler
                    raise
        except Exception as e_decode:
            # Catching a broad exception. More specific authlib errors (JoseError, etc.) could be caught.
            logging.error(f"Error during oauth.dex.decode_id_token: {type(e_decode).__name__} - {str(e_decode)}")
            
            # Log more detailed error info if available
            error_attrs = [attr for attr in dir(e_decode) if not attr.startswith('_') and not callable(getattr(e_decode, attr))]
            if error_attrs:
                logging.error(f"Additional error attributes: {', '.join(error_attrs)}")
                for attr in error_attrs:
                    logging.error(f"  {attr}: {getattr(e_decode, attr)}")
                    
            # If it's an authlib JWTError, log additional context
            if hasattr(e_decode, 'error') and hasattr(e_decode, 'description'):
                logging.error(f"JWT Error: {getattr(e_decode, 'error')} - {getattr(e_decode, 'description')}")
            
            # Log a snippet of the token (first 20 chars) for debugging
            if original_id_token_string:
                token_preview = original_id_token_string[:20] + "..." if len(original_id_token_string) > 20 else original_id_token_string
                logging.error(f"Token preview (first 20 chars): {token_preview}")
                
            # Consider adding more detailed error attributes if available from e_decode.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Authentication failed: ID token processing error - {type(e_decode).__name__}: {str(e_decode)}"}
            ) from e_decode

        logging.info(f"Successfully decoded id_token directly. User info claims: {user_info}")
        # Note: token_data dictionary is NOT modified by decode_id_token, as it only operated on original_id_token_string.
        logging.info(f"Token object state (which was not passed to decode_id_token): {token_data}")
        
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
        except Exception as e_db:
            logging.error(f"Error saving user: {e_db}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
        
        # Return tokens to frontend
        frontend_url = os.getenv("FRONTEND_URL", "https://chores.stillon.top")
        
        # Ensure HTTPS in production
        in_production = os.getenv("ENV", "production").lower() != "development"
        if in_production and frontend_url.startswith("http://"):
            frontend_url = "https://" + frontend_url[7:]
            
        logging.info("Attempting to construct redirect_url...")
        
        # Check for essential keys in token_data needed for the redirect URL (access_token, expires_in)
        # We will use original_id_token_string for the id_token part.
        missing_keys_for_redirect = []
        if 'access_token' not in token_data: missing_keys_for_redirect.append('access_token')
        if 'expires_in' not in token_data: missing_keys_for_redirect.append('expires_in')
        if not original_id_token_string: missing_keys_for_redirect.append('original_id_token_string (was None or empty)')


        if missing_keys_for_redirect:
            logging.error(
                f"Keys missing before redirect_url construction: {', '.join(missing_keys_for_redirect)}. "
                f"Current token_data state: {token_data}. Original id_token was: {'present' if original_id_token_string else 'MISSING/EMPTY'}"
            )
            # This will likely lead to a KeyError or other error in the next step, caught by the generic Exception.
            # Or, if original_id_token_string is the issue, it might pass a 'None' string.

        # Use the original_id_token_string that we saved.
        redirect_url = f"{frontend_url}/auth-callback?token={token_data['access_token']}&id_token={original_id_token_string}&expires_in={token_data['expires_in']}"
        
        if 'refresh_token' in token_data: # refresh_token is optional
            redirect_url += f"&refresh_token={token_data['refresh_token']}"
        
        logging.info(f"Redirecting to: {frontend_url}/auth-callback (params will be in browser)")
        
        return RedirectResponse(url=redirect_url)
    except KeyError as ke:
        logging.error(f"Auth callback error: Caught KeyError: {ke}")
        logging.error(f"Details: Key '{ke}' was not found.")
        if token_data is not None:
            logging.error(f"Token_data object state when KeyError occurred: {token_data}")
        if original_id_token_string is not None:
            logging.error(f"Original id_token string state: {'present and not empty' if original_id_token_string else 'empty or None'}")
        else:
            logging.error("Original id_token string was None (meaning it was likely missing from initial Dex response).")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": f"Authentication failed: Key Error - {ke}"}
        )
    except Exception as e:
        logging.error(f"Auth callback error: Caught generic Exception: {type(e).__name__} - {e}")
        if token_data is not None:
             logging.error(f"Token_data object state at time of generic exception: {token_data}")
        else:
             logging.error("Token_data object not available at time of generic exception (was None or not assigned).")
        if original_id_token_string is not None:
            logging.error(f"Original id_token string state: {'present and not empty' if original_id_token_string else 'empty or None'}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication failed due to an unexpected error."}
        )

@app.get("/auth/user", response_model=User)
@app.get("/api/auth/user", response_model=User)
async def get_user(current_user: User = Depends(get_current_user)):
    return current_user

# Add proxy route for the /api/auth/refresh path
@app.post("/api/auth/refresh")
async def api_auth_refresh(request: Request):
    """Proxy for the /auth/refresh endpoint to support /api/auth/refresh path"""
    try:
        payload = await request.json()
        refresh_token = payload.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Use mock refresh in development mode
        if USE_MOCK_AUTH and 'mock_refresh' in globals():
            logging.info("Using mock token refresh")
            return await mock_refresh(refresh_token)
        
        # Get Dex configuration
        client_id = os.getenv("OAUTH_CLIENT_ID", "choremane")
        client_secret = os.getenv("OAUTH_CLIENT_SECRET", "choremane-secret")
        token_url = f"{os.getenv('DEX_ISSUER_URL', 'https://dex.stillon.top')}/token"
        
        # Prepare the token request
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        # Make the token request to Dex
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
            if response.status_code != 200:
                logging.error(f"Failed to refresh token: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh token"
                )
            
            # Return the new tokens
            return response.json()
    except Exception as e:
        logging.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

# Add diagnostic endpoint for session testing
@app.get("/api/auth/session-test")
async def session_test(request: Request):
    """
    Test endpoint to verify session functionality.
    Each call increments a counter stored in the session.
    """
    counter = request.session.get('test_counter', 0)
    counter += 1
    request.session['test_counter'] = counter
    
    return {
        "counter": counter,
        "session_id": str(request.session.get('session_id', 'unknown')),
        "session_contents": dict(request.session),
        "cookies": request.cookies,
        "secure_context": request.url.scheme == "https" or request.headers.get('x-forwarded-proto') == "https"
    }

# Initialize and mount FastAPI-MCP
mcp = FastApiMCP(app)
mcp.mount()
