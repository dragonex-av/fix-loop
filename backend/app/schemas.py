from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, EmailStr

# ----------------- Auth & User Schemas -----------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: Optional[str] = "customer"  # customer, executive, admin, technician

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    address: Optional[str] = None
    customer_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

# ----------------- Customer Schemas -----------------
class CustomerBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerOut(CustomerBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Technician Schemas -----------------
class TechnicianOut(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    specialization: str
    rating: float
    active_tickets_count: int
    created_at: datetime
    class Config:
        from_attributes = True

class TechnicianAssign(BaseModel):
    technician_id: int
    notes: Optional[str] = None

# ----------------- Product Schemas -----------------
class ProductBase(BaseModel):
    product_type: str
    brand: Optional[str] = "Apex Appliances"
    model: str
    serial_number: Optional[str] = None

class ProductCreate(ProductBase):
    customer_id: int

class ProductOut(ProductBase):
    id: int
    customer_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Appointment Schemas -----------------
class AppointmentCreate(BaseModel):
    ticket_id: int
    technician_id: int
    scheduled_at: datetime
    notes: Optional[str] = None

class AppointmentReschedule(BaseModel):
    scheduled_at: datetime
    reason: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    ticket_id: int
    technician_id: int
    technician_name: Optional[str] = None
    technician_phone: Optional[str] = None
    scheduled_at: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Estimate Schemas -----------------
class EstimateCreate(BaseModel):
    parts_cost: float
    labor_cost: float
    tax: float = 0.0
    items_breakdown: Optional[str] = None
    description: Optional[str] = None

class EstimateReview(BaseModel):
    status: str  # approved, rejected
    rejection_reason: Optional[str] = None

class EstimateOut(BaseModel):
    id: int
    ticket_id: int
    parts_cost: float
    labor_cost: float
    tax: float
    total: float
    items_breakdown: Optional[str] = None
    description: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Invoice Schemas -----------------
class InvoiceOut(BaseModel):
    id: int
    ticket_id: int
    estimate_id: Optional[int] = None
    invoice_number: str
    amount: float
    status: str
    payment_method: str
    paid_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class InvoicePay(BaseModel):
    payment_method: str = "Credit/Debit Card (Simulated)"

# ----------------- Timeline Event Schemas -----------------
class TimelineEventOut(BaseModel):
    id: int
    ticket_id: int
    stage: str
    title: str
    description: Optional[str] = None
    performed_by: str
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Chat Message Schemas -----------------
class ChatMessageCreate(BaseModel):
    ticket_id: Optional[int] = None
    message: str

class ChatMessageOut(BaseModel):
    id: int
    customer_id: int
    ticket_id: Optional[int] = None
    sender: str
    message: str
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Rating & Feedback -----------------
class TicketRatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None

# ----------------- Ticket Schemas -----------------
class TicketCreate(BaseModel):
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    
    product_id: Optional[int] = None
    product_type: Optional[str] = "Washing Machine"
    model: Optional[str] = "Model X"
    brand: Optional[str] = "Apex Appliances"
    serial_number: Optional[str] = None
    
    issue_description: str
    issue_category: Optional[str] = None
    priority: Optional[str] = "Medium"
    image_url: Optional[str] = None

class TicketStageUpdate(BaseModel):
    stage: str
    notes: Optional[str] = None

class TicketOut(BaseModel):
    id: int
    ticket_code: Optional[str] = None
    customer_id: int
    product_id: int
    technician_id: Optional[int] = None
    issue_description: str
    issue_category: str
    status: str
    stage: str
    priority: str
    image_url: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    final_cost: Optional[float] = None
    is_reopened: bool = False
    rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerOut] = None
    product: Optional[ProductOut] = None
    technician: Optional[TechnicianOut] = None
    class Config:
        from_attributes = True

# ----------------- Repair Schemas -----------------
class RepairCreate(BaseModel):
    action: str
    outcome: str = "pending"  # successful, temporary, unsuccessful, pending
    technician_notes: Optional[str] = None
    confirmed_by: Optional[str] = "Staff Lead"

class RepairOut(BaseModel):
    id: int
    ticket_id: int
    action: str
    outcome: str
    technician_notes: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Followup Schemas -----------------
class FollowupCreate(BaseModel):
    ticket_id: int
    promised_at: datetime
    owner: str = "Support Lead"
    notes: Optional[str] = None

class FollowupUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None

class FollowupOut(BaseModel):
    id: int
    customer_id: int
    ticket_id: int
    promised_at: datetime
    owner: str
    status: str
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    customer_name: Optional[str] = None
    ticket_code: Optional[str] = None
    class Config:
        from_attributes = True

# ----------------- AI Analysis / Repair Assistant -----------------
class SupportingEvidenceItem(BaseModel):
    source: str
    reference: str
    detail: Optional[str] = None

class AIAnalysisResponse(BaseModel):
    ticket_id: int
    repeat_issue: bool
    repeat_reason: Optional[str] = None
    previous_repair_summary: Optional[str] = None
    previous_outcome: Optional[str] = None
    suggested_inspection_areas: List[str] = []
    explanation: str
    supporting_evidence: List[SupportingEvidenceItem] = []
    limitations: List[str] = [
        "This is an advisory suggestion based on recorded prior cases, not an automated physical diagnosis."
    ]
    recalled_memories_count: int = 0
    hindsight_status: str = "operational"

# ----------------- Ripple Effect / Pattern Schemas -----------------
class SupportingTicketItem(BaseModel):
    ticket_id: int
    ticket_code: Optional[str] = None
    customer_name: str
    created_at: datetime
    status: str
    stage: Optional[str] = None
    repair_action: Optional[str] = None
    repair_outcome: Optional[str] = None

class PatternAlertOut(BaseModel):
    id: int
    product_model: str
    issue_category: str
    case_count: int
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    status: str
    staff_notes: Optional[str] = None
    created_at: datetime
    supporting_cases: List[SupportingTicketItem] = []
    suggested_investigation: Optional[str] = None
    disclaimer: str = "Potential operational pattern — requires technical inspection; not a confirmed defect."

# ----------------- Memory Explorer Schemas -----------------
class MemoryEventOut(BaseModel):
    id: int
    entity_type: str
    entity_id: Optional[int] = None
    operation: str
    query_or_content: str
    provider_ref: Optional[str] = None
    status: str
    raw_response: Optional[str] = None
    error_summary: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Dashboard Metric Schemas -----------------
class DashboardMetrics(BaseModel):
    total_tickets: int
    open_tickets: int
    repeat_cases: int
    overdue_followups: int
    active_patterns: int
    avg_resolution_hours: float = 24.5
    customer_satisfaction: float = 4.8
    recent_tickets: List[Any] = []
    recent_memory_events: List[Any] = []
    needs_attention: List[Any] = []
    technician_workload: List[Any] = []
    product_distribution: List[Any] = []
