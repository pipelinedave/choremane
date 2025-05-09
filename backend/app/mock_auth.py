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
from fastapi.responses import RedirectResponse, JSONResponse

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
    
    # Store login state in session
    request.session["mock_auth_redirect"] = redirect_uri
    
    # Redirect to mock login page
    return RedirectResponse(url="/auth/mock-login-page")

async def mock_login_page(request: Request):
    """Simple login form for development."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Choremane Development Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f5f5f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .login-container {
                background: white;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 400px;
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 1.5rem;
            }
            form {
                display: flex;
                flex-direction: column;
            }
            label {
                margin-bottom: 0.5rem;
                color: #555;
            }
            input {
                padding: 0.8rem;
                margin-bottom: 1rem;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            button {
                background-color: #4285F4;
                color: white;
                border: none;
                padding: 0.8rem;
                border-radius: 4px;
                cursor: pointer;
                font-size: 1rem;
            }
            button:hover {
                background-color: #3367D6;
            }
            .info {
                margin-top: 1rem;
                text-align: center;
                color: #666;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Development Login</h1>
            <form action="/auth/mock-callback" method="post">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" value="developer@example.com" required>
                
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" value="Test Developer" required>
                
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
    form_data = await request.form()
    email = form_data.get("email", "developer@example.com")
    name = form_data.get("name", "Test Developer")
    
    # Generate mock tokens
    token_data = generate_mock_token(email, name)
    
    # Get the redirect URL from session
    redirect_uri = request.session.get("mock_auth_redirect")
    if not redirect_uri:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Missing redirect URI"}
        )
    
    # Clear session
    request.session.pop("mock_auth_redirect", None)
    
    # Extract token components for the redirect
    frontend_redirect_url = os.getenv("FRONTEND_URL", "http://localhost:5000")
    
    redirect_url = (
        f"{frontend_redirect_url}/auth-callback"
        f"?token={token_data['access_token']}"
        f"&id_token={token_data['id_token']}"
        f"&refresh_token={token_data['refresh_token']}"
        f"&expires_in={token_data['expires_in']}"
    )
    
    logging.info(f"Redirecting to: {frontend_redirect_url}/auth-callback")
    return RedirectResponse(url=redirect_url)

async def mock_refresh(refresh_token: str):
    """Mock token refresh for development."""
    # Simply generate a new token
    return generate_mock_token()

# Add HTML Response class
from fastapi.responses import HTMLResponse
