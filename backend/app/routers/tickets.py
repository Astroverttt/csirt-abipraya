"""
Tickets router — CRUD operations for incident tickets.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_current_session
from ..storage import tickets as store
from ..storage import playbooks as pb_store
from ..services import indexer


router = APIRouter(prefix="/api/tickets", tags=["tickets"])
logger = logging.getLogger("patchops.routers.tickets")


@router.get("")
async def list_tickets(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """List all tickets with optional filtering."""
    return store.get_filtered(status, severity, agent_id, search)


@router.get("/stats")
async def ticket_stats(_session: Dict[str, Any] = Depends(get_current_session)):
    """Summary statistics for tickets."""
    return store.get_stats()


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Get a specific ticket by ID."""
    ticket = store.get_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("")
async def create_ticket(
    data: Dict[str, Any],
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Create a new ticket manually or from an alert."""
    ticket = store.create(data)
    if not ticket:
        # Likely a duplicate alertId
        raise HTTPException(status_code=409, detail="Ticket for this alert already exists")
    return ticket


@router.post("/sync")
async def sync_alerts(
    _session: Dict[str, Any] = Depends(get_current_session)
):
    """Fetch all alerts across all agents and create tickets in bulk."""
    username = _session.get("username")
    password = _session.get("password")
    
    hits = await indexer.get_all_alert_history_details(username, password)
    
    ticket_data_list = []
    
    for hit in hits:
        src = hit.get("_source", {})
        
        severity = src.get("data", {}).get("vulnerability", {}).get("severity")
        if not severity:
            lvl = src.get("rule", {}).get("level", 0)
            if lvl >= 15: severity = "Critical"
            elif lvl >= 12: severity = "High"
            else: severity = "Medium"
            
        agent = src.get("agent", {})
        ticket_data = {
            "alertId": hit.get("_id"),
            "alertTimestamp": src.get("timestamp"),
            "agentId": agent.get("id"),
            "agentName": agent.get("name"),
            "agentIp": agent.get("ip"),
            "cveId": src.get("data", {}).get("vulnerability", {}).get("cve"),
            "packageName": src.get("data", {}).get("vulnerability", {}).get("package", {}).get("name"),
            "packageVersion": src.get("data", {}).get("vulnerability", {}).get("package", {}).get("version"),
            "ruleId": src.get("rule", {}).get("id"),
            "ruleDescription": src.get("rule", {}).get("description", "-"),
            "ruleLevel": src.get("rule", {}).get("level"),
            "ruleGroups": src.get("rule", {}).get("groups", []),
            "severity": severity,
            "isAutoCreated": True,
        }
        
        matches = pb_store.match_playbooks(ticket_data.get("ruleGroups", []), severity)
        if matches:
            pb = matches[0]
            stepsProgress = {
                s["id"]: {"checked": False, "checkedAt": None, "checkedBy": None, "note": ""}
                for s in pb.get("steps", [])
            }
            ticket_data["playbook"] = {
                "playbookId": pb["id"],
                "playbookName": pb["name"],
                "attachedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "attachedBy": "auto",
                "steps": stepsProgress,
                "completedSteps": 0,
                "totalSteps": len(pb.get("steps", [])),
                "completedAt": None,
            }
            
        ticket_data_list.append(ticket_data)

    created_tickets = store.create_bulk(ticket_data_list)
    new_count = len(created_tickets)
    skipped = len(hits) - new_count
            
    return {"status": "success", "new_count": new_count, "skipped": skipped}


@router.put("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    updates: Dict[str, Any],
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Update ticket fields or status (Supporting PUT as used by frontend)."""
    ticket = store.update(ticket_id, updates)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: str,
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Delete a ticket."""
    success = store.delete(ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"status": "success"}
