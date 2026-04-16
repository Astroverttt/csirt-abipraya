"""
Agent router — proxies Wazuh agent endpoints.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_current_session
from ..services import wazuh

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _extract_creds(session: Dict[str, Any]):
    return session["username"], session["password"]


@router.get("")
async def list_agents(
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Dict[str, Any] = Depends(get_current_session),
):
    """List all Wazuh agents."""
    username, password = _extract_creds(session)
    try:
        data = await wazuh.api_request(
            session_id=id(session),
            username=username,
            password=password,
            method="GET",
            path="/agents",
            params={"limit": limit, "offset": offset},
        )
        return data.get("data", {})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")


@router.get("/summary/status")
async def agent_summary(
    session: Dict[str, Any] = Depends(get_current_session),
):
    """Get agent status summary (active, disconnected, etc.)."""
    username, password = _extract_creds(session)
    try:
        data = await wazuh.api_request(
            session_id=id(session),
            username=username,
            password=password,
            method="GET",
            path="/agents/summary/status",
        )
        return data.get("data", {})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")
