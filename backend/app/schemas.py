from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

# ----------------- Customer Schemas -----------------
class CustomerBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerOut(CustomerBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Product Schemas -----------------
class ProductBase(BaseModel):
    product_type: str
    brand: Optional[str] = "Apex"
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

# ----------------- Ticket Schemas -----------------
class TicketCreate(BaseModel):
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    
    product_id: Optional[int] = None
    product_type: Optional[str] = "Washing Machine"
    model: Optional[str] = "Model X"
    brand: Optional[str] = "Apex"
    
    issue_description: str
    issue_category: Optional[str] = None
    priority: Optional[str] = "Medium"

class TicketOut(BaseModel):
    id: int
    ticket_code: Optional[str] = None
    customer_id: int
    product_id: int
    issue_description: str
    issue_category: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerOut] = None
    product: Optional[ProductOut] = None
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
    status: Optional[str] = None  # upcoming, due, overdue, completed, cancelled
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
    source: str  # hindsight_memory, sqlite_record, cross_customer_pattern
    reference: str  # id, memory hash, or ticket code
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
    recent_tickets: List[Any] = []
    recent_memory_events: List[Any] = []
    needs_attention: List[Any] = []
