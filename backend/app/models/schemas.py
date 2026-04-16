"""
Pydantic models for request/response schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str
    wazuh_host: Optional[str] = None  # Optional override


class LoginResponse(BaseModel):
    token: str
    username: str
    message: str = "Login berhasil"


class AuthStatusResponse(BaseModel):
    authenticated: bool
    username: Optional[str] = None


# ── Tickets ───────────────────────────────────────────────────────────────────

class HistoryEntry(BaseModel):
    action: str
    timestamp: str
    detail: str


class TicketCreate(BaseModel):
    alertId: Optional[str] = None
    cveId: Optional[str] = None
    severity: Optional[str] = None
    ruleLevel: Optional[int] = None
    ruleDescription: Optional[str] = None
    ruleGroups: Optional[List[str]] = None
    agentId: Optional[str] = None
    agentName: Optional[str] = None
    agentIp: Optional[str] = None
    packageName: Optional[str] = None
    packageVersion: Optional[str] = None
    isAutoCreated: bool = True
    assignee: Optional[str] = ""
    description: Optional[str] = ""
    tags: Optional[List[str]] = []


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    description: Optional[str] = None
    rootCause: Optional[str] = None
    solution: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    relatedTickets: Optional[List[str]] = None
    playbook: Optional[Dict[str, Any]] = None
    evidence: Optional[List[Dict[str, Any]]] = None


class TicketResponse(BaseModel):
    id: str
    createdAt: str
    updatedAt: str
    status: str
    priority: str
    severity: Optional[str] = None
    alertId: Optional[str] = None
    cveId: Optional[str] = None
    ruleLevel: Optional[int] = None
    ruleDescription: Optional[str] = None
    ruleGroups: Optional[List[str]] = None
    agentId: Optional[str] = None
    agentName: Optional[str] = None
    agentIp: Optional[str] = None
    packageName: Optional[str] = None
    packageVersion: Optional[str] = None
    isDuplicate: bool = False
    isAutoCreated: bool = True
    assignee: Optional[str] = ""
    description: Optional[str] = ""
    rootCause: Optional[str] = ""
    solution: Optional[str] = ""
    notes: Optional[str] = ""
    tags: List[str] = []
    relatedTickets: List[str] = []
    history: List[Dict[str, Any]] = []
    playbook: Optional[Dict[str, Any]] = None
    evidence: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"


class TicketStatsResponse(BaseModel):
    total: int = 0
    open: int = 0
    in_progress: int = 0
    solved: int = 0
    closed: int = 0
    false_positive: int = 0
    critical: int = 0
    high: int = 0


# ── Playbooks ─────────────────────────────────────────────────────────────────

class PlaybookStep(BaseModel):
    id: Optional[str] = None
    order: int = 1
    title: str = ""
    description: str = ""
    category: str = "identification"
    requiresEvidence: bool = False
    estimatedMinutes: int = 10


class PlaybookTrigger(BaseModel):
    type: str  # "rule_group" | "severity"
    value: str


class PlaybookCreate(BaseModel):
    name: str = "Untitled Playbook"
    description: str = ""
    icon: str = "generic"
    triggers: List[PlaybookTrigger] = []
    steps: List[PlaybookStep] = []
    createdBy: str = "admin"


class PlaybookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    triggers: Optional[List[PlaybookTrigger]] = None
    steps: Optional[List[PlaybookStep]] = None
    isActive: Optional[bool] = None


class PlaybookMatchRequest(BaseModel):
    ruleGroups: List[str] = []
    severity: str = ""


# ── NVD ───────────────────────────────────────────────────────────────────────

class NVDSearchRequest(BaseModel):
    keywords: List[str]
    days_back: int = 7
