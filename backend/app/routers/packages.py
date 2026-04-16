"""
Packages / Syscollector router — proxies Wazuh syscollector endpoints.
Also includes SCA, OS, Hardware, and Network info.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_current_session
from ..services import wazuh

router = APIRouter(prefix="/api/syscollector", tags=["syscollector"])


def _extract(session: Dict[str, Any]):
    return session["username"], session["password"]


async def _proxy(session, path: str, params: dict = None):
    username, password = _extract(session)
    try:
        data = await wazuh.api_request(
            session_id=id(session),
            username=username,
            password=password,
            method="GET",
            path=path,
            params=params,
        )
        return data.get("data", {})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")


@router.get("/{agent_id}/packages")
async def packages(
    agent_id: str,
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Dict[str, Any] = Depends(get_current_session),
):
    return await _proxy(session, f"/syscollector/{agent_id}/packages", {"limit": limit, "offset": offset})


@router.get("/{agent_id}/hotfixes")
async def hotfixes(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    return await _proxy(session, f"/syscollector/{agent_id}/hotfixes")


@router.get("/{agent_id}/os")
async def os_info(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    return await _proxy(session, f"/syscollector/{agent_id}/os")


@router.get("/{agent_id}/hardware")
async def hardware(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    return await _proxy(session, f"/syscollector/{agent_id}/hardware")


@router.get("/{agent_id}/netaddr")
async def network(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    return await _proxy(session, f"/syscollector/{agent_id}/netaddr")


# ── SCA (mounted under /api/sca for clarity) ─────────────────────────────────

sca_router = APIRouter(prefix="/api/sca", tags=["sca"])


@sca_router.get("/{agent_id}")
async def sca_policy(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    username, password = _extract(session)
    try:
        data = await wazuh.api_request(
            session_id=id(session),
            username=username,
            password=password,
            method="GET",
            path=f"/sca/{agent_id}",
        )
        return data.get("data", {})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh API error: {e}")
