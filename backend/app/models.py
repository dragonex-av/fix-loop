from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), unique=True, index=True, nullable=False)
    email = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    products = relationship("Product", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="customer", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_type = Column(String(80), nullable=False)  # e.g. Washing Machine, Refrigerator
    brand = Column(String(80), nullable=True, default="Apex")
    model = Column(String(80), nullable=False, index=True)  # e.g. Model X, Model Y
    serial_number = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    customer = relationship("Customer", back_populates="products")
    tickets = relationship("Ticket", back_populates="product", cascade="all, delete-orphan")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_code = Column(String(50), unique=True, index=True, nullable=True)  # e.g. TCK-1001
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    issue_description = Column(Text, nullable=False)
    issue_category = Column(String(100), nullable=False, index=True)  # e.g. Drainage issue
    status = Column(String(50), default="New", index=True)  # New, Open, In Progress, Resolved, Reopened, Investigate
    priority = Column(String(30), default="Medium")  # Low, Medium, High, Critical
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    customer = relationship("Customer", back_populates="tickets")
    product = relationship("Product", back_populates="tickets")
    repairs = relationship("RepairRecord", back_populates="ticket", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="ticket", cascade="all, delete-orphan")
    alert_links = relationship("PatternAlertCase", back_populates="ticket")


class RepairRecord(Base):
    __tablename__ = "repair_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    action = Column(String(255), nullable=False)  # e.g. Drain pipe cleaning, Filter inspection
    outcome = Column(String(50), nullable=False, default="pending")  # successful, temporary, unsuccessful, pending
    technician_notes = Column(Text, nullable=True)
    confirmed_by = Column(String(100), nullable=True)  # staff name / technician ID
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="repairs")


class Followup(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    promised_at = Column(DateTime, nullable=False, index=True)
    owner = Column(String(100), nullable=False)  # e.g. Sarah Jenkins (Senior Lead)
    status = Column(String(50), default="upcoming", index=True)  # upcoming, due, overdue, completed, cancelled
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    customer = relationship("Customer", back_populates="followups")
    ticket = relationship("Ticket", back_populates="followups")


class PatternAlert(Base):
    __tablename__ = "pattern_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_model = Column(String(80), nullable=False, index=True)
    issue_category = Column(String(100), nullable=False, index=True)
    case_count = Column(Integer, default=0)
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)
    status = Column(String(50), default="active")  # active, investigating, dismissed
    staff_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    cases = relationship("PatternAlertCase", back_populates="alert", cascade="all, delete-orphan")


class PatternAlertCase(Base):
    __tablename__ = "pattern_alert_cases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("pattern_alerts.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)

    alert = relationship("PatternAlert", back_populates="cases")
    ticket = relationship("Ticket", back_populates="alert_links")


class MemoryEvent(Base):
    __tablename__ = "memory_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # ticket, repair, complaint
    entity_id = Column(Integer, nullable=True)
    operation = Column(String(50), nullable=False)  # retain, recall
    query_or_content = Column(Text, nullable=False)
    provider_ref = Column(String(255), nullable=True)
    status = Column(String(50), default="success")  # success, empty, failed
    raw_response = Column(Text, nullable=True)
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
