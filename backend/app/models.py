from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="customer")  # admin, executive, technician, customer
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    customer = relationship("Customer", back_populates="user", uselist=False)
    technician_profile = relationship("Technician", back_populates="user", uselist=False)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), unique=True, index=True, nullable=False)
    email = Column(String(120), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="customer")
    products = relationship("Product", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="customer", cascade="all, delete-orphan")
    chat_messages = relationship("CustomerChatMessage", back_populates="customer", cascade="all, delete-orphan")


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(120), nullable=True)
    specialization = Column(String(100), default="General Appliance Repair")
    rating = Column(Float, default=4.8)
    active_tickets_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="technician_profile")
    tickets = relationship("Ticket", back_populates="technician")
    appointments = relationship("Appointment", back_populates="technician")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_type = Column(String(80), nullable=False)  # Washing Machine, Refrigerator, etc.
    brand = Column(String(80), nullable=True, default="Apex Appliances")
    model = Column(String(80), nullable=False, index=True)  # Model X, Model Y, etc.
    serial_number = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    customer = relationship("Customer", back_populates="products")
    tickets = relationship("Ticket", back_populates="product", cascade="all, delete-orphan")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_code = Column(String(50), unique=True, index=True, nullable=True)  # TCK-1001
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    
    issue_description = Column(Text, nullable=False)
    issue_category = Column(String(100), nullable=False, index=True)  # Drainage issue, etc.
    status = Column(String(50), default="New", index=True)  # New, Open, In Progress, Resolved, Reopened, Investigate
    
    # Granular Swiggy/Zomato style order tracking stage:
    # complaint_registered -> support_review -> technician_assigned -> visit_scheduled ->
    # diagnosis_completed -> estimate_approval -> repair_in_progress -> quality_check -> resolved
    stage = Column(String(50), default="complaint_registered", index=True)
    
    priority = Column(String(30), default="Medium")  # Low, Medium, High, Critical
    image_url = Column(Text, nullable=True)
    
    sla_deadline = Column(DateTime, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    final_cost = Column(Float, nullable=True)
    is_reopened = Column(Boolean, default=False)
    
    rating = Column(Integer, nullable=True)  # 1 to 5 stars
    feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    customer = relationship("Customer", back_populates="tickets")
    product = relationship("Product", back_populates="tickets")
    technician = relationship("Technician", back_populates="tickets")
    repairs = relationship("RepairRecord", back_populates="ticket", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="ticket", cascade="all, delete-orphan")
    alert_links = relationship("PatternAlertCase", back_populates="ticket")
    timeline_events = relationship("TicketTimelineEvent", back_populates="ticket", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="ticket", cascade="all, delete-orphan")
    estimates = relationship("Estimate", back_populates="ticket", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="ticket", cascade="all, delete-orphan")
    chat_messages = relationship("CustomerChatMessage", back_populates="ticket", cascade="all, delete-orphan")


class TicketTimelineEvent(Base):
    __tablename__ = "ticket_timeline_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    stage = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    performed_by = Column(String(100), default="System")
    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="timeline_events")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(50), default="scheduled")  # scheduled, rescheduled, completed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="appointments")
    technician = relationship("Technician", back_populates="appointments")


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    parts_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    items_breakdown = Column(Text, nullable=True)  # JSON or comma-separated items
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, approved, rejected
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="estimates")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    estimate_id = Column(Integer, ForeignKey("estimates.id"), nullable=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="unpaid")  # unpaid, paid
    payment_method = Column(String(50), default="Card/UPI (Simulated)")
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="invoices")


class CustomerChatMessage(Base):
    __tablename__ = "customer_chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    sender = Column(String(20), nullable=False)  # customer, ai, support
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    customer = relationship("Customer", back_populates="chat_messages")
    ticket = relationship("Ticket", back_populates="chat_messages")


class RepairRecord(Base):
    __tablename__ = "repair_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    action = Column(String(255), nullable=False)
    outcome = Column(String(50), nullable=False, default="pending")  # successful, temporary, unsuccessful, pending
    technician_notes = Column(Text, nullable=True)
    confirmed_by = Column(String(100), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="repairs")


class Followup(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    promised_at = Column(DateTime, nullable=False, index=True)
    owner = Column(String(100), nullable=False)
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
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    operation = Column(String(50), nullable=False)  # retain, recall
    query_or_content = Column(Text, nullable=False)
    provider_ref = Column(String(255), nullable=True)
    status = Column(String(50), default="success")  # success, empty, failed, unconfigured
    raw_response = Column(Text, nullable=True)
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
