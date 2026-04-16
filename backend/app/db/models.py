from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime
from .database import Base

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, index=True)
    createdAt = Column(String, index=True)
    updatedAt = Column(String)
    status = Column(String, index=True)
    priority = Column(String, index=True)
    isDuplicate = Column(Boolean, default=False)
    isAutoCreated = Column(Boolean, default=True)
    alertId = Column(String, index=True, nullable=True)
    alertTimestamp = Column(String, nullable=True)
    agentId = Column(String, index=True, nullable=True)
    agentName = Column(String, nullable=True)
    agentIp = Column(String, nullable=True)
    cveId = Column(String, index=True, nullable=True)
    packageName = Column(String, nullable=True)
    packageVersion = Column(String, nullable=True)
    ruleId = Column(String, nullable=True)
    ruleDescription = Column(String, nullable=True)
    ruleLevel = Column(Integer, nullable=True)
    ruleGroups = Column(JSON, default=list)
    severity = Column(String, nullable=True)
    assignee = Column(String, nullable=True)
    description = Column(String, nullable=True)
    rootCause = Column(String, nullable=True)
    solution = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    relatedTickets = Column(JSON, default=list)
    history = Column(JSON, default=list)
    playbook = Column(JSON, default=dict)
    evidence = Column(JSON, default=list)

class Playbook(Base):
    __tablename__ = "playbooks"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    icon = Column(String)
    triggers = Column(JSON, default=list)
    steps = Column(JSON, default=list)
    createdAt = Column(String)
    updatedAt = Column(String)
    createdBy = Column(String)
    isDefault = Column(Boolean, default=False)
    isActive = Column(Boolean, default=True)

class Sequence(Base):
    __tablename__ = "sequences"
    name = Column(String, primary_key=True)
    counter = Column(Integer, default=0)
