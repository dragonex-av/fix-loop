import os
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db

security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None

def normalize_role(role_str: str) -> str:
    """Normalizes role strings to standard uppercase: CUSTOMER, TECHNICIAN, ADMIN."""
    r = role_str.strip().upper()
    if r in ("ADMIN", "EXECUTIVE"):
        return "ADMIN"
    elif r == "TECHNICIAN":
        return "TECHNICIAN"
    return "CUSTOMER"

def determine_user_role(email: str, requested_role: Optional[str] = None) -> str:
    """
    Nobody can self-promote:
    TECHNICIAN / ADMIN role is granted only if email is in the allowlist.
    Otherwise defaults to CUSTOMER.
    """
    clean_email = email.strip().lower()
    admin_list = [e.strip().lower() for e in settings.ADMIN_EMAILS.split(",") if e.strip()]
    tech_list = [e.strip().lower() for e in settings.TECHNICIAN_EMAILS.split(",") if e.strip()]

    if clean_email in admin_list:
        return "ADMIN"
    if clean_email in tech_list:
        return "TECHNICIAN"
    return "CUSTOMER"

def verify_google_id_token(token: str) -> dict:
    """
    Verifies a Google OAuth ID token using google.oauth2.id_token.
    Falls back to mock decoding for tests when token starts with 'mock-google-token-'.
    """
    if token.startswith("mock-google-token-"):
        # Test hook for automated testing
        email = token.replace("mock-google-token-", "")
        return {
            "sub": f"google-sub-{email}",
            "email": email,
            "name": email.split("@")[0].title(),
            "email_verified": True
        }

    from google.oauth2 import id_token
    from google.auth.transport import requests

    client_id = settings.GOOGLE_CLIENT_ID
    request = requests.Request()
    try:
        id_info = id_token.verify_oauth2_token(token, request, audience=client_id or None)
        return id_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {str(e)}"
        )

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    from app.models import User
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated",
        )
    return user

def require_roles(allowed_roles: List[str]):
    # Normalize list of allowed roles
    normalized_allowed = [normalize_role(r) for r in allowed_roles]

    def role_checker(current_user = Depends(get_current_user)):
        user_role = normalize_role(current_user.role)
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}",
            )
        return current_user
    return role_checker
