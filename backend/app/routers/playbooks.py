"""
Playbook router — CRUD + matching engine for incident response playbooks.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_session
from ..models.schemas import PlaybookCreate, PlaybookMatchRequest, PlaybookUpdate
from ..storage import playbooks as playbook_store

router = APIRouter(prefix="/api/playbooks", tags=["playbooks"])


@router.get("")
async def list_playbooks(
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """List all playbooks (seeds defaults if empty)."""
    return playbook_store.get_all()


@router.get("/{playbook_id}")
async def get_playbook(
    playbook_id: str,
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Get a single playbook by ID."""
    pb = playbook_store.get_by_id(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook tidak ditemukan")
    return pb


@router.post("", status_code=201)
async def create_playbook(
    body: PlaybookCreate,
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Create a new playbook."""
    return playbook_store.create(body.model_dump())


@router.put("/{playbook_id}")
async def update_playbook(
    playbook_id: str,
    body: PlaybookUpdate,
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Update an existing playbook."""
    updated = playbook_store.update(playbook_id, body.model_dump(exclude_none=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Playbook tidak ditemukan")
    return updated


@router.delete("/{playbook_id}")
async def delete_playbook(
    playbook_id: str,
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Delete a playbook (cannot delete defaults)."""
    try:
        success = playbook_store.delete(playbook_id)
        if not success:
            raise HTTPException(status_code=404, detail="Playbook tidak ditemukan")
        return {"message": "Playbook berhasil dihapus"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/match")
async def match_playbooks(
    body: PlaybookMatchRequest,
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Find playbooks that match a ticket's rule groups and severity."""
    return playbook_store.match_playbooks(body.ruleGroups, body.severity)


@router.post("/seed")
async def seed_playbooks(
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Manually trigger default playbook seeding."""
    playbook_store.seed_defaults()
    return {"message": "Default playbooks seeded"}
