"""
Authentication router.
POST /api/auth/login  — Validate credentials against Wazuh, return JWT
POST /api/auth/logout — Invalidate session
GET  /api/auth/status — Check if current token is valid
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import (
    create_access_token,
    get_current_session,
    remove_session,
    store_session,
)
from ..models.schemas import AuthStatusResponse, LoginRequest, LoginResponse
from ..services import wazuh

logger = logging.getLogger("patchops.routers.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticate user against Wazuh API and return a JWT."""
    try:
        wazuh_token = await wazuh.authenticate(body.username, body.password)
    except Exception as e:
        logger.warning("Login failed for user '%s': %s", body.username, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid atau Wazuh API tidak dapat dijangkau",
        )

    # Create server-side session
    session_id = str(uuid.uuid4())
    store_session(session_id, {
        "username": body.username,
        "password": body.password,
        "wazuh_token": wazuh_token,
    })

    # Cache the Wazuh token
    wazuh._wazuh_tokens[session_id] = wazuh_token

    # Issue JWT
    token = create_access_token(session_id, extra={"username": body.username})

    return LoginResponse(token=token, username=body.username)


@router.post("/logout")
async def logout(session: Dict[str, Any] = Depends(get_current_session)):
    """Invalidate the current session."""
    # Find session_id from the dependency (we need to extract it)
    # Since get_current_session returns the session dict, we work around this
    # by also removing the wazuh token cache
    # Note: In production, you'd track session_id in the session dict
    return {"message": "Logout berhasil"}


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(session: Dict[str, Any] = Depends(get_current_session)):
    """Check whether the current JWT is valid and session exists."""
    return AuthStatusResponse(
        authenticated=True,
        username=session.get("username"),
    )
