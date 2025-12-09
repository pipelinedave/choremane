"""Auth routes for the Choremane API."""

import os
import logging
from fastapi import APIRouter, Request, HTTPException, status
import httpx

auth_router = APIRouter(prefix="/auth")

# Check if we should use mock auth for development
USE_MOCK_AUTH = os.getenv("USE_MOCK_AUTH", "false").lower() == "true"

# Import mock_refresh function - will be imported at runtime
mock_refresh = None
if USE_MOCK_AUTH:
    try:
        from app.mock_auth import mock_refresh

        logging.info("Mock auth refresh function imported")
    except ImportError:
        logging.error("Failed to import mock_refresh function")


@auth_router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh an expired access token using a refresh token."""
    try:
        payload = await request.json()
        refresh_token = payload.get("refresh_token")

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required",
            )

        # Use mock refresh in development mode
        if USE_MOCK_AUTH and mock_refresh:
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
            "client_secret": client_secret,
        }

        # Make the token request to Dex
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.status_code != 200:
                logging.error(f"Failed to refresh token: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh token",
                )

            # Return the new tokens
            return response.json()
    except Exception as e:
        logging.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )
