"""
Ticket storage — PostgreSQL SQLAlchemy backed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import or_, desc, asc, func

from ..db.database import SessionLocal
from ..db.models import Ticket, Sequence

logger = logging.getLogger("patchops.storage.tickets")

def dict_from_model(obj: Any) -> Dict[str, Any]:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

def _next_id(db) -> str:
    seq = db.query(Sequence).filter(Sequence.name == "ticket_counter").first()
    if not seq:
        seq = Sequence(name="ticket_counter", counter=0)
        db.add(seq)
        db.commit()
        db.refresh(seq)
    
    seq.counter += 1
    db.commit()
    year = datetime.now(timezone.utc).year
    return f"TKT-{year}-{str(seq.counter).zfill(4)}"

def _derive_priority(severity: Optional[str]) -> str:
    s = (severity or "").lower()
    if s == "critical": return "critical"
    if s == "high": return "high"
    if s == "medium": return "medium"
    return "low"


# ── Public API ───────────────────────────────────────────────────────────────

def get_all() -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        tickets = db.query(Ticket).order_by(desc(Ticket.createdAt)).all()
        return [dict_from_model(t) for t in tickets]

def get_by_id(ticket_id: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        return dict_from_model(ticket) if ticket else None

def create(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with SessionLocal() as db:
        alert_id = data.get("alertId")
        if alert_id:
            existing = db.query(Ticket).filter(Ticket.alertId == alert_id).first()
            if existing:
                return None

        now = datetime.now(timezone.utc).isoformat()
        new_id = _next_id(db)
        
        history_entry = {
            "action": "created",
            "timestamp": now,
            "detail": "Auto-created from alert sync" if data.get("isAutoCreated", True) else "Manually created",
        }
        
        ticket_data = {
            "id": new_id,
            "createdAt": now,
            "updatedAt": now,
            "status": "open",
            "priority": _derive_priority(data.get("severity")),
            "isDuplicate": False,
            "isAutoCreated": data.get("isAutoCreated", True),
            "assignee": "",
            "description": "",
            "rootCause": "",
            "solution": "",
            "notes": "",
            "tags": [],
            "relatedTickets": [],
            "history": [history_entry],
            "playbook": None,
            "evidence": [],
            **data,
        }
        # Unconditionally replace ID and createdAt
        ticket_data["id"] = new_id
        ticket_data["createdAt"] = now
        ticket_data["updatedAt"] = now

        db_ticket = Ticket(**ticket_data)
        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)
        
        return dict_from_model(db_ticket)

def create_bulk(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not data_list:
        return []
        
    with SessionLocal() as db:
        alert_ids = [d.get("alertId") for d in data_list if d.get("alertId")]
        
        existing_ids = set()
        if alert_ids:
            existing = db.query(Ticket.alertId).filter(Ticket.alertId.in_(alert_ids)).all()
            existing_ids = {e[0] for e in existing}

        created_tickets = []
        for data in data_list:
            alert_id = data.get("alertId")
            if alert_id and alert_id in existing_ids:
                continue
                
            now = datetime.now(timezone.utc).isoformat()
            new_id = _next_id(db)
            
            history_entry = {
                "action": "created",
                "timestamp": now,
                "detail": "Auto-created from alert sync" if data.get("isAutoCreated", True) else "Manually created",
            }
            
            ticket_data = {
                "id": new_id,
                "createdAt": now,
                "updatedAt": now,
                "status": "open",
                "priority": _derive_priority(data.get("severity")),
                "isDuplicate": False,
                "isAutoCreated": data.get("isAutoCreated", True),
                "assignee": "",
                "description": "",
                "rootCause": "",
                "solution": "",
                "notes": "",
                "tags": [],
                "relatedTickets": [],
                "history": [history_entry],
                "playbook": data.get("playbook"),
                "evidence": [],
                **{k: v for k, v in data.items() if k != "playbook"}
            }
            ticket_data["id"] = new_id
            ticket_data["createdAt"] = now
            ticket_data["updatedAt"] = now

            db_ticket = Ticket(**ticket_data)
            db.add(db_ticket)
            created_tickets.append(db_ticket)
            
        if created_tickets:
            db.commit()
            for t in created_tickets:
                db.refresh(t)
                
        return [dict_from_model(t) for t in created_tickets]

def update(ticket_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return None

        now = datetime.now(timezone.utc).isoformat()
        history_entries = []

        if "status" in updates and updates["status"] != ticket.status:
            history_entries.append({
                "action": "status_change",
                "timestamp": now,
                "detail": f'Status changed from "{ticket.status}" to "{updates["status"]}"',
            })

        if "assignee" in updates and updates["assignee"] != ticket.assignee:
            detail = f'Assigned to "{updates["assignee"]}"' if updates["assignee"] else "Unassigned"
            history_entries.append({
                "action": "assigned",
                "timestamp": now,
                "detail": detail,
            })

        for k, v in updates.items():
            if hasattr(ticket, k) and k != "id":
                setattr(ticket, k, v)
        
        ticket.updatedAt = now
        if history_entries:
            ticket.history = list(ticket.history) + history_entries

        db.commit()
        db.refresh(ticket)
        return dict_from_model(ticket)

def delete(ticket_id: str) -> bool:
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return False
        db.delete(ticket)
        db.commit()
        return True

def get_filtered(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    agent_id: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        query = db.query(Ticket)

        if status:
            query = query.filter(Ticket.status == status)
        if severity:
            # simple matching by lowercasing
            query = query.filter(func.lower(Ticket.severity) == severity.lower())
        if agent_id:
            query = query.filter(Ticket.agentId == agent_id)
        if search:
            q = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Ticket.id).like(q),
                    func.lower(Ticket.cveId).like(q),
                    func.lower(Ticket.agentName).like(q),
                    func.lower(Ticket.ruleDescription).like(q),
                    func.lower(Ticket.packageName).like(q),
                    func.lower(Ticket.assignee).like(q),
                )
            )

        tickets = query.order_by(desc(Ticket.createdAt)).all()
        return [dict_from_model(t) for t in tickets]

def get_stats() -> Dict[str, int]:
    with SessionLocal() as db:
        tickets = db.query(Ticket).all()
        return {
            "total": len(tickets),
            "open": sum(1 for t in tickets if (t.status or '').lower() == "open"),
            "in_progress": sum(1 for t in tickets if (t.status or '').lower() == "in_progress"),
            "solved": sum(1 for t in tickets if (t.status or '').lower() == "solved"),
            "closed": sum(1 for t in tickets if (t.status or '').lower() == "closed"),
            "false_positive": sum(1 for t in tickets if (t.status or '').lower() == "false_positive"),
            "critical": sum(1 for t in tickets if (t.priority or '').lower() == "critical"),
            "high": sum(1 for t in tickets if (t.priority or '').lower() == "high"),
        }

def import_tickets(tickets_data: List[Dict[str, Any]]) -> int:
    with SessionLocal() as db:
        count = 0
        for data in tickets_data:
            existing = db.query(Ticket).filter(Ticket.id == data.get("id")).first()
            if not existing:
                db.add(Ticket(**data))
                count += 1
        db.commit()
        return count
