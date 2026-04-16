"""
Playbook storage — PostgreSQL SQLAlchemy backed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.sql import text

from ..config import settings
from ..db.database import SessionLocal
from ..db.models import Playbook, Sequence

logger = logging.getLogger("patchops.storage.playbooks")

def dict_from_model(obj: Any) -> Dict[str, Any]:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

def _next_id(db) -> str:
    seq = db.query(Sequence).filter(Sequence.name == "playbook_counter").first()
    if not seq:
        seq = Sequence(name="playbook_counter", counter=6)
        db.add(seq)
        db.commit()
        db.refresh(seq)
    
    seq.counter += 1
    db.commit()
    return f"PB-{str(seq.counter).zfill(4)}"

# ── Public API ───────────────────────────────────────────────────────────────

def get_all() -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        pbs = db.query(Playbook).all()
        if not pbs:
            seed_defaults()
            pbs = db.query(Playbook).all()
        return [dict_from_model(p) for p in pbs]

def get_by_id(playbook_id: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as db:
        pb = db.query(Playbook).filter(Playbook.id == playbook_id).first()
        return dict_from_model(pb) if pb else None

def create(data: Dict[str, Any]) -> Dict[str, Any]:
    with SessionLocal() as db:
        now = datetime.now(timezone.utc).isoformat()
        
        steps = []
        for i, s in enumerate(data.get("steps", [])):
            steps.append({
                "id": s.get("id") or f"s{int(datetime.now(timezone.utc).timestamp())}-{i}",
                "order": s.get("order", i + 1),
                "title": s.get("title", ""),
                "description": s.get("description", ""),
                "category": s.get("category", "identification"),
                "requiresEvidence": s.get("requiresEvidence", False),
                "estimatedMinutes": s.get("estimatedMinutes", 10),
            })
        
        playbook_data = {
            "id": _next_id(db),
            "name": data.get("name", "Untitled Playbook"),
            "description": data.get("description", ""),
            "icon": data.get("icon", "generic"),
            "triggers": data.get("triggers", []),
            "steps": steps,
            "createdAt": now,
            "updatedAt": now,
            "createdBy": data.get("createdBy", "admin"),
            "isDefault": False,
            "isActive": True,
        }
        
        db_pb = Playbook(**playbook_data)
        db.add(db_pb)
        db.commit()
        db.refresh(db_pb)
        return dict_from_model(db_pb)

def update(playbook_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with SessionLocal() as db:
        pb = db.query(Playbook).filter(Playbook.id == playbook_id).first()
        if not pb:
            return None
        
        for k, v in updates.items():
            if hasattr(pb, k) and k != "id":
                setattr(pb, k, v)
                
        pb.updatedAt = datetime.now(timezone.utc).isoformat()
        db.commit()
        db.refresh(pb)
        return dict_from_model(pb)

def delete(playbook_id: str) -> bool:
    with SessionLocal() as db:
        pb = db.query(Playbook).filter(Playbook.id == playbook_id).first()
        if not pb:
            return False
        if pb.isDefault:
            raise ValueError("Cannot delete default playbook")
            
        db.delete(pb)
        db.commit()
        return True

def match_playbooks(rule_groups: List[str], severity: str) -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        pbs = db.query(Playbook).filter(Playbook.isActive == True).all()
        ticket_groups = [g.lower() for g in rule_groups]
        ticket_sev = severity.lower()

        results = []
        for pb in pbs:
            matches = any(
                (trigger.get("type") == "rule_group" and trigger.get("value", "").lower() in ticket_groups)
                or (trigger.get("type") == "severity" and ticket_sev == trigger.get("value", "").lower())
                for trigger in (pb.triggers or [])
            )
            if matches:
                results.append(dict_from_model(pb))
        return results

def seed_defaults() -> None:
    with SessionLocal() as db:
        if db.query(Playbook).count() > 0:
            return
            
        defaults = _get_default_playbooks()
        for pdata in defaults:
            db.add(Playbook(**pdata))
            
        seq = db.query(Sequence).filter(Sequence.name == "playbook_counter").first()
        if not seq:
            db.add(Sequence(name="playbook_counter", counter=len(defaults)))
        else:
            seq.counter = len(defaults)
            
        db.commit()
        logger.info("Seeded %d default playbooks", len(defaults))

def _get_default_playbooks() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
       {
           "id": "PB-0001", "name": "Malware Incident Response", "description": "Standard operating procedure for handling malware detection alerts from Wazuh.",
           "icon": "malware", "triggers": [{"type": "rule_group", "value": "rootcheck"}, {"type": "rule_group", "value": "virustotal"}],
           "steps": [
               {"id": "s1", "order": 1, "title": "Isolate affected endpoint", "description": "Disconnect the host from the network to prevent lateral movement.", "category": "containment", "requiresEvidence": True, "estimatedMinutes": 5},
               {"id": "s2", "order": 2, "title": "Collect forensic artifacts", "description": "Capture memory dump, running processes, and network connections.", "category": "identification", "requiresEvidence": True, "estimatedMinutes": 30},
               {"id": "s3", "order": 3, "title": "Analyze malware sample", "description": "Submit sample to sandbox and check IOCs against threat intelligence.", "category": "identification", "requiresEvidence": True, "estimatedMinutes": 60},
               {"id": "s4", "order": 4, "title": "Remove malware and restore", "description": "Clean the infection and restore from known good backup if needed.", "category": "eradication", "requiresEvidence": True, "estimatedMinutes": 45},
               {"id": "s5", "order": 5, "title": "Post-incident review", "description": "Document findings, update detection rules, and brief stakeholders.", "category": "post_incident", "requiresEvidence": False, "estimatedMinutes": 30},
           ],
           "createdAt": now, "updatedAt": now, "createdBy": "system", "isDefault": True, "isActive": True,
       },
       {
           "id": "PB-0002", "name": "Authentication Anomaly", "description": "Respond to brute-force, credential stuffing, or unauthorized access attempts.",
           "icon": "auth", "triggers": [{"type": "rule_group", "value": "authentication_failed"}, {"type": "rule_group", "value": "authentication_failures"}],
           "steps": [
               {"id": "s1", "order": 1, "title": "Verify alert legitimacy", "description": "Check if the login attempts are from a known user or automated attack.", "category": "identification", "requiresEvidence": False, "estimatedMinutes": 10},
               {"id": "s2", "order": 2, "title": "Block source IP", "description": "Add source IP to firewall blocklist if confirmed malicious.", "category": "containment", "requiresEvidence": True, "estimatedMinutes": 5},
               {"id": "s3", "order": 3, "title": "Reset compromised credentials", "description": "Force password reset for any accounts that may have been compromised.", "category": "eradication", "requiresEvidence": True, "estimatedMinutes": 15},
               {"id": "s4", "order": 4, "title": "Review access logs", "description": "Check if any successful login occurred from the malicious source.", "category": "identification", "requiresEvidence": True, "estimatedMinutes": 20},
               {"id": "s5", "order": 5, "title": "Update detection rules", "description": "Tune authentication monitoring rules to reduce false positives.", "category": "post_incident", "requiresEvidence": False, "estimatedMinutes": 15},
           ],
           "createdAt": now, "updatedAt": now, "createdBy": "system", "isDefault": True, "isActive": True,
       },
       {
           "id": "PB-0003", "name": "Critical Vulnerability Response", "description": "Triage and remediate critical/high severity vulnerabilities detected by Wazuh.",
           "icon": "vuln", "triggers": [{"type": "severity", "value": "critical"}, {"type": "rule_group", "value": "vulnerability-detector"}],
           "steps": [
               {"id": "s1", "order": 1, "title": "Assess exposure", "description": "Determine if the vulnerable service is internet-facing or internally exposed.", "category": "identification", "requiresEvidence": False, "estimatedMinutes": 15},
               {"id": "s2", "order": 2, "title": "Check for active exploits", "description": "Search for public exploits or active exploitation in the wild.", "category": "identification", "requiresEvidence": True, "estimatedMinutes": 20},
               {"id": "s3", "order": 3, "title": "Apply temporary mitigation", "description": "Implement WAF rules, network ACLs, or disable vulnerable features.", "category": "containment", "requiresEvidence": True, "estimatedMinutes": 30},
               {"id": "s4", "order": 4, "title": "Schedule and apply patch", "description": "Plan maintenance window and apply the security update.", "category": "eradication", "requiresEvidence": True, "estimatedMinutes": 60},
               {"id": "s5", "order": 5, "title": "Verify remediation", "description": "Re-scan the host to confirm the vulnerability is resolved.", "category": "post_incident", "requiresEvidence": True, "estimatedMinutes": 15},
           ],
           "createdAt": now, "updatedAt": now, "createdBy": "system", "isDefault": True, "isActive": True,
       },
       {
           "id": "PB-0004", "name": "File Integrity Change", "description": "Investigate unauthorized file changes detected by Wazuh FIM (syscheck).",
           "icon": "fim", "triggers": [{"type": "rule_group", "value": "syscheck"}],
           "steps": [
               {"id": "s1", "order": 1, "title": "Identify the changed file", "description": "Review FIM alert details: file path, modification type, and timestamp.", "category": "identification", "requiresEvidence": False, "estimatedMinutes": 5},
               {"id": "s2", "order": 2, "title": "Determine change source", "description": "Correlate with user sessions, cron jobs, or deployments to find who made the change.", "category": "identification", "requiresEvidence": True, "estimatedMinutes": 20},
               {"id": "s3", "order": 3, "title": "Assess impact", "description": "Determine if the change affects security, configuration, or application behavior.", "category": "identification", "requiresEvidence": False, "estimatedMinutes": 15},
               {"id": "s4", "order": 4, "title": "Restore or approve", "description": "Restore the original file if unauthorized, or document if approved change.", "category": "eradication", "requiresEvidence": True, "estimatedMinutes": 15},
           ],
           "createdAt": now, "updatedAt": now, "createdBy": "system", "isDefault": True, "isActive": True,
       },
       {
           "id": "PB-0005", "name": "Rootkit Detection", "description": "Respond to potential rootkit alerts from Wazuh rootcheck module.",
           "icon": "rootkit", "triggers": [{"type": "rule_group", "value": "rootcheck"}],
           "steps": [
               {"id": "s1", "order": 1, "title": "Isolate the host", "description": "Immediately quarantine the affected system from the network.", "category": "containment", "requiresEvidence": True, "estimatedMinutes": 5},
               {"id": "s2", "order": 2, "title": "Run offline rootkit scan", "description": "Boot from clean media and run rootkit scanning tools (rkhunter, chkrootkit).", "category": "identification", "requiresEvidence": True, "estimatedMinutes": 45},
               {"id": "s3", "order": 3, "title": "Full system rebuild", "description": "If confirmed, rebuild the system from scratch using known good images.", "category": "eradication", "requiresEvidence": True, "estimatedMinutes": 120},
               {"id": "s4", "order": 4, "title": "Investigate entry point", "description": "Determine how the rootkit was installed to prevent recurrence.", "category": "post_incident", "requiresEvidence": True, "estimatedMinutes": 60},
           ],
           "createdAt": now, "updatedAt": now, "createdBy": "system", "isDefault": True, "isActive": True,
       },
       {
           "id": "PB-0006", "name": "Network Anomaly Investigation", "description": "Investigate suspicious network activity such as unusual connections or data exfiltration.",
           "icon": "network", "triggers": [{"type": "rule_group", "value": "suricata"}, {"type": "rule_group", "value": "firewall"}],
           "steps": [
               {"id": "s1", "order": 1, "title": "Review network alert details", "description": "Analyze source/destination IPs, ports, protocols, and alert signatures.", "category": "identification", "requiresEvidence": False, "estimatedMinutes": 10},
               {"id": "s2", "order": 2, "title": "Check threat intelligence", "description": "Look up IPs/domains against threat intelligence feeds and reputation databases.", "category": "identification", "requiresEvidence": True, "estimatedMinutes": 15},
               {"id": "s3", "order": 3, "title": "Block malicious traffic", "description": "Update firewall rules to block the identified malicious connections.", "category": "containment", "requiresEvidence": True, "estimatedMinutes": 10},
               {"id": "s4", "order": 4, "title": "Capture and analyze traffic", "description": "Run packet capture to understand the full scope of the communication.", "category": "identification", "requiresEvidence": True, "estimatedMinutes": 30},
               {"id": "s5", "order": 5, "title": "Document and report", "description": "Write up findings and update network monitoring signatures.", "category": "post_incident", "requiresEvidence": False, "estimatedMinutes": 20},
           ],
           "createdAt": now, "updatedAt": now, "createdBy": "system", "isDefault": True, "isActive": True,
       },
    ]
