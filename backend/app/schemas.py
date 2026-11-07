from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ----------------- Auth & Users -----------------
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None

class UserRegister(UserBase):
    password: str
    role: Optional[str] = "CUSTOMER"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str
    target_role: Optional[str] = "CUSTOMER"  # Requested role: CUSTOMER or TECHNICIAN

class UserOut(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserOut

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str

# ----------------- Customers -----------------
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

# ----------------- Technicians -----------------
class TechnicianOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    phone: str
    email: Optional[str] = None
    specialization: str
    rating: float
    active_tickets_count: int

    class Config:
        from_attributes = True

class TechnicianAssign(BaseModel):
    technician_id: int
    notes: Optional[str] = None

# ----------------- Products -----------------
class ProductBase(BaseModel):
    product_type: str
    brand: Optional[str] = "Apex Appliances"
    model: str
    serial_number: Optional[str] = None

class ProductOut(ProductBase):
    id: int
    customer_id: int

    class Config:
        from_attributes = True

# ----------------- Appointments & Scheduling -----------------
class AppointmentCreate(BaseModel):
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
    scheduled_at: datetime
    status: str
    reschedule_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- OTP Verification -----------------
class ResolutionVerifyRequest(BaseModel):
    code: str

class ResolutionRejectRequest(BaseModel):
    reason: Optional[str] = "Customer reported issue is not resolved."

# ----------------- Notifications -----------------
class NotificationOut(BaseModel):
    id: int
    user_id: int
    ticket_id: Optional[int] = None
    type: str
    title: str
    body: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Estimates & Invoices -----------------
class EstimateCreate(BaseModel):
    parts_cost: float = 0.0
    labor_cost: float = 0.0
    tax: float = 0.0
    items_breakdown: Optional[str] = None
    description: Optional[str] = None

class EstimateReview(BaseModel):
    approved: bool
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

class InvoiceOut(BaseModel):
    id: int
    ticket_id: int
    invoice_number: str
    amount: float
    status: str
    payment_method: str
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class InvoicePay(BaseModel):
    payment_method: Optional[str] = "Card/UPI (Simulated)"

# ----------------- Ticket Timeline & Chat -----------------
class TimelineEventOut(BaseModel):
    id: int
    stage: str
    title: str
    description: Optional[str] = None
    performed_by: str
    created_at: datetime

    class Config:
        from_attributes = True

class TicketEventOut(BaseModel):
    id: int
    from_status: Optional[str] = None
    to_status: str
    actor_name: str
    actor_role: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    ticket_id: Optional[int] = None
    message: str

class ChatMessageOut(BaseModel):
    id: int
    sender: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Tickets -----------------
class TicketCreate(BaseModel):
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    
    product_id: Optional[int] = None
    product_type: str = "Washing Machine"
    model: str = "Model X"
    brand: Optional[str] = "Apex Appliances"
    serial_number: Optional[str] = None
    
    issue_description: str
    issue_category: Optional[str] = None
    priority: Optional[str] = "Medium"
    image_url: Optional[str] = None

class TicketRatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None

class TicketStartWork(BaseModel):
    action: Optional[str] = "Diagnostics started"
    parts_used: Optional[str] = None
    notes: Optional[str] = None

class TicketCancelRequest(BaseModel):
    reason: str

class TicketOut(BaseModel):
    id: int
    ticket_code: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    product_id: int
    product_model: Optional[str] = None
    product_type: Optional[str] = None
    issue_description: str
    issue_category: str
    status: str
    stage: str
    priority: str
    technician_name: Optional[str] = "Unassigned"
    is_repeat: bool = False
    is_reopened: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    latest_action: Optional[str] = None
    latest_outcome: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- Repairs -----------------
class RepairCreate(BaseModel):
    action: str
    outcome: str = "successful"  # successful, temporary, unsuccessful, pending
    technician_notes: Optional[str] = None
    confirmed_by: Optional[str] = None

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

# ----------------- Followups -----------------
class FollowupCreate(BaseModel):
    ticket_id: int
    promised_at: datetime
    owner: str = "Support Team"
    notes: Optional[str] = None

class FollowupUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class FollowupOut(BaseModel):
    id: int
    ticket_id: int
    customer_id: int
    promised_at: datetime
    owner: str
    status: str
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- AI & Dashboard -----------------
class AIAnalysisResponse(BaseModel):
    ticket_id: int
    repeat_issue: bool
    repeat_reason: Optional[str] = None
    previous_repair_summary: Optional[str] = None
    previous_outcome: Optional[str] = None
    suggested_inspection_areas: List[str]
    explanation: str
    supporting_evidence: List[Dict[str, Any]]
    limitations: List[str]
    recalled_memories_count: int = 0
    hindsight_status: str

class MemoryEventOut(BaseModel):
    id: int
    entity_type: str
    entity_id: Optional[int] = None
    operation: str
    query_or_content: str
    provider_ref: Optional[str] = None
    status: str
    error_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardMetrics(BaseModel):
    total_tickets: int
    open_tickets: int
    repeat_cases: int
    overdue_followups: int
    active_patterns: int
    avg_resolution_hours: float
    customer_satisfaction: float
    recent_tickets: List[Dict[str, Any]]
    recent_memory_events: List[Dict[str, Any]]
    needs_attention: List[Dict[str, Any]]
    technician_workload: List[Dict[str, Any]]
    product_distribution: List[Dict[str, Any]]
