"""Authentication middleware for FastAPI."""
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import verify_token
from app.models import User

security = HTTPBearer()

async def get_user_from_header(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Extract user from Authorization header."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = await verify_token(token)
    
    if not payload or "email" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or missing email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For backward compatibility, also set the X-User-Email header
    request.headers.__dict__["_list"].append(
        (b"x-user-email", payload["email"].encode())
    )
    
    return User(
        email=payload["email"],
        name=payload.get("name", ""),
        given_name=payload.get("given_name", ""),
        family_name=payload.get("family_name", ""),
    )
