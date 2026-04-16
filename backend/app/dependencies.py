"""
JWT authentication utilities and FastAPI dependencies.

Session store keeps Wazuh credentials in server memory (never sent to client).
Client only receives an opaque JWT token.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

logger = logging.getLogger("patchops.auth")

# ── In-memory session store: session_id → {wazuh_username, wazuh_password, ...} ─
_sessions: Dict[str, Dict[str, Any]] = {}

security_scheme = HTTPBearer(auto_error=False)


# ── Token helpers ─────────────────────────────────────────────────────────────

def create_access_token(session_id: str, extra: Optional[dict] = None) -> str:
    """Create a JWT that carries only the session_id (no secrets)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": session_id,
        "exp": expire,
        **(extra or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT, returning its payload."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token tidak valid: {e}",
        )


# ── Session management ────────────────────────────────────────────────────────

def store_session(session_id: str, data: Dict[str, Any]) -> None:
    _sessions[session_id] = {**data, "created_at": datetime.now(timezone.utc).isoformat()}


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return _sessions.get(session_id)


def remove_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_current_session(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Extracts & validates the JWT from the Authorization header,
    then returns the associated server-side session dict.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi diperlukan",
        )

    payload = decode_token(credentials.credentials)
    session_id = payload.get("sub")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak memiliki session ID",
        )

    session = get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi telah kedaluwarsa, silakan login ulang",
        )

    return session
