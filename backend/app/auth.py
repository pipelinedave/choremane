"""Authentication module for the Choremane app."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List

import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
import httpx

from app.models import User

# Configure OAuth2 authentication
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://dex.stillon.top/auth",
    tokenUrl="https://dex.stillon.top/token",
    scopes={
        "openid": "OpenID Connect",
        "profile": "Profile information",
        "email": "Email information",
    },
)

# Environment variables for configuration
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "choremane")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "choremane-secret")
DEX_ISSUER_URL = os.getenv("DEX_ISSUER_URL", "https://dex.stillon.top")
ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Cache for JWKs
jwks_cache = {"keys": [], "last_updated": None}


async def get_jwks():
    """Fetch JWKs from DEX_ISSUER_URL."""
    global jwks_cache
    # Return cached JWKs if they exist and are not expired
    if (
        jwks_cache["last_updated"]
        and jwks_cache["keys"]
        and jwks_cache["last_updated"] > datetime.now() - timedelta(hours=24)
    ):
        return jwks_cache["keys"]

    # Fetch JWKs from DEX
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{DEX_ISSUER_URL}/.well-known/openid-configuration"
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not retrieve OpenID configuration from Dex",
            )

        oidc_config = response.json()
        jwks_uri = oidc_config.get("jwks_uri")

        if not jwks_uri:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="JWKS URI not found in OpenID configuration",
            )

        jwks_response = await client.get(jwks_uri)
        if jwks_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not retrieve JWKS from Dex",
            )

        jwks_cache["keys"] = jwks_response.json().get("keys", [])
        jwks_cache["last_updated"] = datetime.now()

        return jwks_cache["keys"]


async def get_rsa_key(token: str, jwks: List[Dict]):
    """Get the RSA key from JWKs matching the token's key ID."""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token header missing key ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    for key in jwks:
        if key.get("kid") == kid:
            if key.get("kty") != "RSA":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Key is not RSA",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return RSAAlgorithm.from_jwk(json.dumps(key))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Key not found",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_token(token: str):
    """Verify the token against Dex JWKs."""
    jwks = await get_jwks()
    rsa_key = await get_rsa_key(token, jwks)

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[ALGORITHM],
            audience=OAUTH_CLIENT_ID,
            issuer=DEX_ISSUER_URL,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTClaimsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect claims, please check the audience and issuer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from the token."""
    payload = await verify_token(token)

    if not payload or "email" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = User(
        email=payload["email"],
        name=payload.get("name", ""),
        given_name=payload.get("given_name", ""),
        family_name=payload.get("family_name", ""),
    )

    return user
