from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Index,
                        Integer, String)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(Integer, primary_key=True)
    agent_name = Column(String(100), nullable=False)
    tier = Column(String(10), nullable=False)               # L1 / L2 / L3
    primary_category = Column(String(60), nullable=False)
    shift_region = Column(String(40), nullable=False)
    efficiency_multiplier = Column(Float, nullable=False)


class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(Integer, primary_key=True)
    merchant_name = Column(String(150), nullable=False)
    sector = Column(String(60), nullable=False)
    tier = Column(String(20), nullable=False)               # Foundation / Advanced
    region = Column(String(40), nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True)
    merchant_id = Column(Integer, ForeignKey("merchants.merchant_id"), nullable=False)
    category = Column(String(60), nullable=False)
    sub_category = Column(String(60), nullable=False)
    priority = Column(String(2), nullable=False)            # P1 - P4
    created_at = Column(DateTime, nullable=False)
    is_legacy = Column(Boolean)
    assigned_agent_id = Column(Integer, ForeignKey("agents.agent_id"), nullable=True)  # null = unassigned
    category_mismatch = Column(Boolean)
    first_response_at = Column(DateTime)
    closed_at = Column(DateTime)                            # null = still open
    ttfr_hours = Column(Float)
    resolution_hours = Column(Float)
    response_breached = Column(Boolean)
    resolution_breached = Column(Boolean)
    is_reopened = Column(Boolean)
    is_reopen_child = Column(Boolean)
    is_incident_ticket = Column(Boolean)
    csat_score = Column(Float)                              # 0-1, null = no survey response
    status = Column(String(10), nullable=False)             # derived: Open / Resolved
    created_month = Column(String(7), nullable=False)       # derived: YYYY-MM

    __table_args__ = (
        Index("ix_tickets_created_at", "created_at"),
        Index("ix_tickets_category", "category"),
        Index("ix_tickets_priority", "priority"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_agent", "assigned_agent_id"),
        Index("ix_tickets_merchant", "merchant_id"),
    )
