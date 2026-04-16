"""
Vulnerability router — proxies Wazuh vulnerability endpoints.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
import httpx

from ..dependencies import get_current_session
from ..services import wazuh

router = APIRouter(prefix="/api/vulnerability", tags=["vulnerabilities"])


def _extract_creds(session: Dict[str, Any]):
    return session["username"], session["password"]


@router.get("")
async def all_vulnerabilities(
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Dict[str, Any] = Depends(get_current_session),
):
    """List all vulnerabilities across all agents."""
    username, password = _extract_creds(session)
    try:
        data = await wazuh.api_request(
            session_id=id(session),
            username=username,
            password=password,
            method="GET",
            path="/vulnerability",
            params={"limit": limit, "offset": offset},
        )
        return data.get("data", {})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found")
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")


@router.get("/{agent_id}")
async def agent_vulnerabilities(
    agent_id: str,
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Dict[str, Any] = Depends(get_current_session),
):
    """List vulnerabilities for a specific agent."""
    username, password = _extract_creds(session)
    try:
        data = await wazuh.api_request(
            session_id=id(session),
            username=username,
            password=password,
            method="GET",
            path=f"/vulnerability/{agent_id}",
            params={"limit": limit, "offset": offset},
        )
        return data.get("data", {})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found")
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")


@router.get("/{agent_id}/summary/severity")
async def vulnerability_summary(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """Get vulnerability severity summary for an agent."""
    username, password = _extract_creds(session)
    try:
        data = await wazuh.api_request(
            session_id=id(session),
            username=username,
            password=password,
            method="GET",
            path=f"/vulnerability/{agent_id}/summary/severity",
        )
        return data.get("data", {})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found")
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")
