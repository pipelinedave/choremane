"""
Mock authentication module for local development.

This provides a simple local authentication mechanism when the Dex server
is unavailable. Should only be used for development purposes.
"""
import os
import logging
import secrets
import time
from datetime import datetime, timedelta
import jwt
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse

# Create a mock private key for local token signing
MOCK_PRIVATE_KEY = secrets.token_hex(32)

def generate_mock_token(email="developer@example.com", name="Test Developer"):
    """Generate a mock JWT token for development purposes."""
    now = int(time.time())
    expires = now + (60 * 60 * 24)  # 24 hours
    
    payload = {
        "iss": "mock-auth-dev",
        "sub": f"user:{email}",
        "aud": "choremane",
        "exp": expires,
        "iat": now,
        "email": email,
        "email_verified": True,
        "name": name,
        "given_name": name.split()[0] if " " in name else name,
        "family_name": name.split()[-1] if " " in name else "",
        "preferred_username": email
    }
    
    access_token = jwt.encode(payload, MOCK_PRIVATE_KEY, algorithm="HS256")
    refresh_token = secrets.token_urlsafe(32)
    
    return {
        "access_token": access_token,
        "id_token": access_token,  # Use the same token for simplicity
        "refresh_token": refresh_token,
        "expires_in": 86400,  # 24 hours in seconds
        "token_type": "bearer"
    }

async def mock_login(request: Request):
    """Mock login route for development."""
    logging.info("Using mock authentication for local development")
    redirect_uri = str(request.url_for("auth_callback"))
    logging.info(f"Mock login initiated with redirect_uri: {redirect_uri}")
    
    # We'll pass the redirect URI to the login page URL as a query parameter
    # Make absolute URLs to avoid path resolution issues
    base_url = str(request.base_url).rstrip('/')
    mock_login_url = f"{base_url}/auth/mock-login-page?redirect_uri={redirect_uri}"
    logging.info(f"Redirecting to mock login page: {mock_login_url}")
    return RedirectResponse(url=mock_login_url)

async def mock_login_page(request: Request):
    """Simple login form for development."""
    # Get the redirect URI from the query parameters
    redirect_uri = request.query_params.get("redirect_uri", "")
    logging.info(f"Mock login page accessed with redirect_uri: {redirect_uri}")
    
    # Get the base URL for absolute form action
    base_url = str(request.base_url).rstrip('/')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Choremane Development Login</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f5f5f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .login-container {{
                background: white;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 400px;
            }}
            h1 {{
                color: #333;
                text-align: center;
                margin-bottom: 1.5rem;
            }}
            form {{
                display: flex;
                flex-direction: column;
            }}
            label {{
                margin-bottom: 0.5rem;
                color: #555;
            }}
            input {{
                padding: 0.8rem;
                margin-bottom: 1rem;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            button {{
                background-color: #4285F4;
                color: white;
                border: none;
                padding: 0.8rem;
                border-radius: 4px;
                cursor: pointer;
                font-size: 1rem;
            }}
            button:hover {{
                background-color: #3367D6;
            }}
            .info {{
                margin-top: 1rem;
                text-align: center;
                color: #666;
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Development Login</h1>
            <form action="{base_url}/auth/mock-callback" method="post">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" value="developer@example.com" required>
                
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" value="Test Developer" required>
                
                <!-- Include the redirect URI as a hidden input -->
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                
                <button type="submit">Sign In</button>
            </form>
            <div class="info">
                This is a mock login for local development only.
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

async def mock_callback(request: Request):
    """Process the mock login form submission."""
    logging.info(f"Mock callback received at URL: {request.url}")
    
    try:
        form_data = await request.form()
        logging.info(f"Form data received: {form_data}")
        
        email = form_data.get("email", "developer@example.com")
        name = form_data.get("name", "Test Developer")
        redirect_uri = form_data.get("redirect_uri", "")
        
        logging.info(f"Mock callback received with email: {email}, name: {name}, redirect_uri: {redirect_uri}")
        
        # Generate mock tokens
        token_data = generate_mock_token(email, name)
        
        # Use the frontend redirect URL from environment or query parameter
        frontend_redirect_url = os.getenv("FRONTEND_URL", "http://localhost:5000")
        logging.info(f"Using frontend redirect URL: {frontend_redirect_url}")
        
        # Create the redirect URL with the tokens
        redirect_url = (
            f"{frontend_redirect_url}/auth-callback"
            f"?token={token_data['access_token']}"
            f"&id_token={token_data['id_token']}"
            f"&refresh_token={token_data['refresh_token']}"
            f"&expires_in={token_data['expires_in']}"
        )
        
        logging.info(f"Redirecting to: {redirect_url}")
        return RedirectResponse(url=redirect_url, status_code=303)  # Use 303 See Other for POST redirects
    except Exception as e:
        logging.error(f"Error in mock_callback: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )

async def mock_refresh(refresh_token: str):
    """Mock token refresh for development."""
    # Simply generate a new token
    return generate_mock_token()
