"""
Indexer router — proxies all Elasticsearch/Wazuh Indexer queries.
Credentials stay server-side.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_session
from ..services import indexer

router = APIRouter(prefix="/api/indexer", tags=["indexer"])


def _extract(session: Dict[str, Any]):
    # Note: Service layer will prioritize settings.INDEXER_USERNAME if set in .env
    return session.get("username"), session.get("password")


@router.get("/alerts/summary")
async def alert_summary(
    session: Dict[str, Any] = Depends(get_current_session),
):
    """Aggregated alert summary for all agents."""
    username, password = _extract(session)
    return await indexer.get_alert_history_summary(username, password)


@router.get("/alerts/{agent_id}")
async def alert_details(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """Detailed alert history for a specific agent."""
    username, password = _extract(session)
    try:
        return await indexer.get_alert_history_details(agent_id, username, password)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Indexer error: {e}")


@router.get("/vulnerabilities")
async def all_active_vulnerabilities(
    session: Dict[str, Any] = Depends(get_current_session),
):
    """Active vulnerabilities for ALL agents directly from Wazuh Indexer."""
    username, password = _extract(session)
    return await indexer.get_all_active_vulnerabilities(username, password)


@router.get("/vulnerabilities/{agent_id}")
async def active_vulnerabilities(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """Active vulnerabilities from Wazuh States index."""
    username, password = _extract(session)
    return await indexer.get_active_vulnerabilities(agent_id, username, password)


@router.get("/fim/{agent_id}")
async def fim_history(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """FIM (File Integrity Monitoring) history for an agent."""
    username, password = _extract(session)
    return await indexer.get_fim_history(agent_id, username, password)


@router.get("/sca/{agent_id}")
async def sca_history(
    agent_id: str,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """SCA (Security Configuration Assessment) history for an agent."""
    username, password = _extract(session)
    return await indexer.get_sca_history(agent_id, username, password)
