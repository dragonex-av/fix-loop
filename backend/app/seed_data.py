from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, Base, engine
from app.models import (
    User, Customer, Product, Ticket, Technician, Appointment,
    Estimate, Invoice, TicketTimelineEvent, RepairRecord, Followup, MemoryEvent
)
from app.services.auth_service import hash_password
from app.services.pattern_service import pattern_service

def seed():
    print("Initializing schema on NeonDB PostgreSQL...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    now = datetime.now(timezone.utc)

    print("Seeding FixLoop Production Users & Role Hierarchy...")

    pwd_hash = hash_password("password123")

    # 1. Employee Accounts
    admin_user = User(
        email="admin@fixloop.com",
        hashed_password=pwd_hash,
        name="Sarah Jenkins",
        role="admin",
        phone="+91-99000-11223",
        address="FixLoop HQ, Central Operations, Bangalore"
    )
    db.add(admin_user)

    exec_user = User(
        email="support@fixloop.com",
        hashed_password=pwd_hash,
        name="Amit Sharma",
        role="executive",
        phone="+91-99000-44556",
        address="FixLoop Regional Support Center, Bangalore"
    )
    db.add(exec_user)

    tech_user1 = User(
        email="tech.vikram@fixloop.com",
        hashed_password=pwd_hash,
        name="Vikram Singh",
        role="technician",
        phone="+91-98700-11111",
        address="Service Hub North, Bangalore"
    )
    db.add(tech_user1)
    db.flush()

    tech_user2 = User(
        email="tech.rajesh@fixloop.com",
        hashed_password=pwd_hash,
        name="Rajesh Roy",
        role="technician",
        phone="+91-98700-22222",
        address="Service Hub East, Bangalore"
    )
    db.add(tech_user2)
    db.flush()

    # 2. Technician Profiles
    tech1 = Technician(
        user_id=tech_user1.id,
        name="Vikram Singh",
        phone="+91-98700-11111",
        email="tech.vikram@fixloop.com",
        specialization="Washers, Dryers & Hydraulic Pumps",
        rating=4.9,
        active_tickets_count=2
    )
    db.add(tech1)

    tech2 = Technician(
        user_id=tech_user2.id,
        name="Rajesh Roy",
        phone="+91-98700-22222",
        email="tech.rajesh@fixloop.com",
        specialization="Refrigerators, Inverters & Compressors",
        rating=4.8,
        active_tickets_count=1
    )
    db.add(tech2)

    tech3 = Technician(
        name="Deepak Varma",
        phone="+91-98700-33333",
        email="deepak.v@fixloop.com",
        specialization="Smart Home PCBs & Electrical Wiring",
        rating=4.7,
        active_tickets_count=1
    )
    db.add(tech3)
    db.flush()

    # 3. Customer Accounts & Linked Profiles
    demo_customers_data = [
        {
            "name": "Rahul Sharma",
            "email": "rahul@example.com",
            "phone": "+91-98765-43210",
            "address": "Flat 402, Green Glen Layout, Bellandur, Bangalore - 560103",
            "model": "Model X",
            "type": "Washing Machine"
        },
        {
            "name": "Priya Nair",
            "email": "priya@example.com",
            "phone": "+91-98222-33445",
            "address": "Villa 12, Palm Meadows, Whitefield, Bangalore - 560066",
            "model": "Model X",
            "type": "Washing Machine"
        },
        {
            "name": "Aman Verma",
            "email": "aman@example.com",
            "phone": "+91-98111-22334",
            "address": "304, Prestige Lavender, Indiranagar, Bangalore",
            "model": "Model X",
            "type": "Washing Machine"
        },
        {
            "name": "Karan Patel",
            "email": "karan@example.com",
            "phone": "+91-98333-44556",
            "address": "B-101, Salarpuria Green, Koramangala, Bangalore",
            "model": "Model X",
            "type": "Washing Machine"
        },
        {
            "name": "Neha Gupta",
            "email": "neha@example.com",
            "phone": "+91-98444-55667",
            "address": "78, HSR Layout Sector 2, Bangalore",
            "model": "Model X",
            "type": "Washing Machine"
        },
        {
            "name": "Riya Sen",
            "email": "riya@example.com",
            "phone": "+91-98555-66778",
            "address": "12A, Sobha Rose, Whitefield, Bangalore",
            "model": "Model X",
            "type": "Washing Machine"
        },
        {
            "name": "Arjun Mehta",
            "email": "arjun@example.com",
            "phone": "+91-98666-77889",
            "address": "Tower 4, Brigade Gateway, Malleshwaram, Bangalore",
            "model": "Model X",
            "type": "Washing Machine"
        },
        {
            "name": "Meera Joshi",
            "email": "meera@example.com",
            "phone": "+91-98777-88990",
            "address": "Plot 54, Jayanagar 4th Block, Bangalore",
            "model": "Model Y",
            "type": "Refrigerator"
        }
    ]

    cust_objs = {}
    prod_objs = {}

    for c in demo_customers_data:
        cust = Customer(
            name=c["name"],
            phone=c["phone"],
            email=c["email"],
            address=c["address"],
            created_at=now - timedelta(days=30)
        )
        db.add(cust)
        db.flush()
        cust_objs[c["name"]] = cust

        # Create user account for customer
        u = User(
            email=c["email"],
            hashed_password=pwd_hash,
            name=c["name"],
            role="customer",
            phone=c["phone"],
            address=c["address"],
            customer_id=cust.id,
            created_at=now - timedelta(days=30)
        )
        db.add(u)

        prod = Product(
            customer_id=cust.id,
            product_type=c["type"],
            brand="Apex Appliances",
            model=c["model"],
            serial_number=f"APX-{c['model'][:1]}-{cust.id:04d}",
            created_at=now - timedelta(days=30)
        )
        db.add(prod)
        db.flush()
        prod_objs[c["name"]] = prod

    # 4. Tickets with Lifecycle Tracking & Events
    
    # CASE 1: Rahul's Previous Resolved Ticket (Drain Pipe cleaning -> temporary outcome)
    t1 = Ticket(
        ticket_code="TCK-1001",
        customer_id=cust_objs["Rahul Sharma"].id,
        product_id=prod_objs["Rahul Sharma"].id,
        technician_id=tech1.id,
        issue_description="Washing machine stops halfway with E20 drainage error. Water pooling inside drum.",
        issue_category="Drainage issue",
        status="Resolved",
        stage="resolved",
        priority="High",
        estimated_cost=85.00,
        final_cost=85.00,
        rating=4,
        feedback="Technician was polite and cleaned the hose, but problem returned after 5 days.",
        created_at=now - timedelta(days=12),
        updated_at=now - timedelta(days=11)
    )
    db.add(t1)
    db.flush()

    r1 = RepairRecord(
        ticket_id=t1.id,
        action="Drain pipe cleaning & debris unclogging",
        outcome="temporary",
        technician_notes="Unclogged main discharge hose. Advised customer issue may return if internal pump valve sticks.",
        confirmed_by="Vikram Singh (Senior Field Tech)",
        confirmed_at=now - timedelta(days=11),
        created_at=now - timedelta(days=11)
    )
    db.add(r1)

    est1 = Estimate(
        ticket_id=t1.id,
        parts_cost=20.00,
        labor_cost=60.00,
        tax=5.00,
        total=85.00,
        items_breakdown="Discharge hose flush & sanitize kit ($20), Standard Service Labor ($60), GST ($5)",
        description="Drain line unclogging and system flush",
        status="approved",
        created_at=now - timedelta(days=12)
    )
    db.add(est1)
    db.flush()

    inv1 = Invoice(
        ticket_id=t1.id,
        estimate_id=est1.id,
        invoice_number="INV-1001-8841",
        amount=85.00,
        status="paid",
        paid_at=now - timedelta(days=11),
        created_at=now - timedelta(days=11)
    )
    db.add(inv1)

    # Follow-up for Rahul (Overdue)
    f1 = Followup(
        customer_id=cust_objs["Rahul Sharma"].id,
        ticket_id=t1.id,
        promised_at=now - timedelta(hours=4),
        owner="Sarah Jenkins (Service Lead)",
        status="overdue",
        notes="Post-repair 5-day check-in to confirm if drainage error recurred.",
        created_at=now - timedelta(days=5)
    )
    db.add(f1)

    # Timeline events for TCK-1001
    events_t1 = [
        ("complaint_registered", "Complaint Registered", "Customer reported error E20 and standing water in drum.", "Rahul Sharma", -12),
        ("support_review", "Support Review Completed", "Verified warranty status and assigned senior technician.", "Sarah Jenkins", -12),
        ("technician_assigned", "Technician Assigned: Vikram Singh", "Vikram assigned for washing machine diagnostics.", "Operations", -12),
        ("visit_scheduled", "Service Visit Scheduled", "Appointment set for 10:30 AM next day.", "System", -12),
        ("diagnosis_completed", "Diagnosis Completed", "Debris detected in discharge hose.", "Vikram Singh", -11),
        ("estimate_approval", "Estimate Approved", "Customer approved $85.00 repair quote.", "Rahul Sharma", -11),
        ("repair_in_progress", "Repair Completed", "Hose cleaned and sanitized.", "Vikram Singh", -11),
        ("quality_check", "Quality Inspection Passed", "Cycle tested without error.", "Vikram Singh", -11),
        ("resolved", "Service Ticket Resolved", "Invoice paid and ticket closed.", "System", -11)
    ]
    for st, title, desc, perf, days_ago in events_t1:
        db.add(TicketTimelineEvent(
            ticket_id=t1.id,
            stage=st,
            title=title,
            description=desc,
            performed_by=perf,
            created_at=now + timedelta(days=days_ago)
        ))

    # Initial Hindsight retain memory log for Rahul
    mem1 = MemoryEvent(
        entity_type="repair",
        entity_id=r1.id,
        operation="retain",
        query_or_content="REPAIR EXPERIENCE for Model X (Drainage issue): Action performed: 'Drain pipe cleaning & debris unclogging'. Confirmed outcome: 'temporary'. Technician notes: 'Unclogged main discharge hose. Advised customer issue may return if internal pump valve sticks'. Original complaint: 'Washing machine stops halfway with E20 drainage error'. Ticket: TCK-1001.",
        provider_ref="hs-mem-exp-1001-rahul",
        status="success",
        raw_response='{"status": "retained", "memory_id": "hs-mem-exp-1001-rahul", "bank": "fixloop-operations"}',
        created_at=now - timedelta(days=11)
    )
    db.add(mem1)

    # CASE 2: Priya - Estimate Approval Pending (Customer Portal Showpiece!)
    t3 = Ticket(
        ticket_code="TCK-1003",
        customer_id=cust_objs["Priya Nair"].id,
        product_id=prod_objs["Priya Nair"].id,
        technician_id=tech1.id,
        issue_description="Standing water in drum at end of wash cycle; buzzer beeps continuously with E20 code.",
        issue_category="Drainage issue",
        status="In Progress",
        stage="estimate_approval",
        priority="High",
        estimated_cost=125.00,
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(hours=3)
    )
    db.add(t3)
    db.flush()

    est3 = Estimate(
        ticket_id=t3.id,
        parts_cost=65.00,
        labor_cost=50.00,
        tax=10.00,
        total=125.00,
        items_breakdown="Secondary Drain Pump Impeller Assembly ($65), Labor ($50), Tax ($10)",
        description="Drain pump impeller replacement & seal test. Avoids repeat hose cleaning based on prior Model X failure patterns.",
        status="pending",
        created_at=now - timedelta(hours=4)
    )
    db.add(est3)

    app3 = Appointment(
        ticket_id=t3.id,
        technician_id=tech1.id,
        scheduled_at=now + timedelta(hours=18),
        status="scheduled",
        notes="Customer requested morning arrival before 11 AM."
    )
    db.add(app3)

    events_t3 = [
        ("complaint_registered", "Complaint Registered", "Water standing in drum at end of cycle.", "Priya Nair", -2),
        ("support_review", "Support Review Completed", "AI recalled recurring Model X drainage patterns.", "Amit Sharma", -2),
        ("technician_assigned", "Technician Assigned: Vikram Singh", "Dispatched for drain assembly inspection.", "Operations", -1),
        ("visit_scheduled", "Visit Scheduled", "Scheduled for technician physical inspection.", "System", -1),
        ("diagnosis_completed", "Diagnosis Completed", "Pump impeller shaft loose; requires replacement.", "Vikram Singh", 0),
        ("estimate_approval", "Estimate Generated", "Estimate of $125.00 sent to Priya for approval.", "Vikram Singh", 0)
    ]
    for st, title, desc, perf, days_ago in events_t3:
        db.add(TicketTimelineEvent(
            ticket_id=t3.id,
            stage=st,
            title=title,
            description=desc,
            performed_by=perf,
            created_at=now + timedelta(days=days_ago)
        ))

    # CASE 3: Aman - Visit Scheduled
    t2 = Ticket(
        ticket_code="TCK-1002",
        customer_id=cust_objs["Aman Verma"].id,
        product_id=prod_objs["Aman Verma"].id,
        technician_id=tech1.id,
        issue_description="Drum won't drain water after rinse cycle on Model X.",
        issue_category="Drainage issue",
        status="In Progress",
        stage="visit_scheduled",
        priority="Medium",
        created_at=now - timedelta(days=3)
    )
    db.add(t2)
    db.flush()

    app2 = Appointment(
        ticket_id=t2.id,
        technician_id=tech1.id,
        scheduled_at=now + timedelta(days=1, hours=2),
        status="scheduled",
        notes="Gate security code: 4920"
    )
    db.add(app2)

    # Cases 4 - 8: Karan, Neha, Riya, Arjun, Meera
    t4 = Ticket(
        ticket_code="TCK-1004",
        customer_id=cust_objs["Karan Patel"].id,
        product_id=prod_objs["Karan Patel"].id,
        issue_description="Model X showing drainage timeout error on delicate wash.",
        issue_category="Drainage issue",
        status="Open",
        stage="support_review",
        priority="Medium",
        created_at=now - timedelta(days=4)
    )
    db.add(t4)

    t5 = Ticket(
        ticket_code="TCK-1005",
        customer_id=cust_objs["Neha Gupta"].id,
        product_id=prod_objs["Neha Gupta"].id,
        technician_id=tech3.id,
        issue_description="Water stays in machine after wash. Loud humming noise from bottom right pump area.",
        issue_category="Drainage issue",
        status="In Progress",
        stage="repair_in_progress",
        priority="High",
        created_at=now - timedelta(days=3)
    )
    db.add(t5)

    t6 = Ticket(
        ticket_code="TCK-1006",
        customer_id=cust_objs["Riya Sen"].id,
        product_id=prod_objs["Riya Sen"].id,
        issue_description="Drain cycle fails intermittently; water left behind in tub.",
        issue_category="Drainage issue",
        status="Open",
        stage="complaint_registered",
        priority="Medium",
        created_at=now - timedelta(days=2)
    )
    db.add(t6)

    t7 = Ticket(
        ticket_code="TCK-1007",
        customer_id=cust_objs["Arjun Mehta"].id,
        product_id=prod_objs["Arjun Mehta"].id,
        issue_description="Model X washer drum full of soapy water, won't pump out.",
        issue_category="Drainage issue",
        status="New",
        stage="complaint_registered",
        priority="High",
        created_at=now - timedelta(hours=6)
    )
    db.add(t7)

    t8 = Ticket(
        ticket_code="TCK-1008",
        customer_id=cust_objs["Meera Joshi"].id,
        product_id=prod_objs["Meera Joshi"].id,
        technician_id=tech2.id,
        issue_description="Refrigerator fresh food compartment warm; freezer is working fine.",
        issue_category="Cooling issue",
        status="In Progress",
        stage="diagnosis_completed",
        priority="Medium",
        created_at=now - timedelta(hours=14)
    )
    db.add(t8)

    db.commit()

    # Recalculate Ripple Effect
    patterns = pattern_service.scan_and_update_patterns(db)
    print(f"Generated {len(patterns)} Ripple Effect pattern alert(s) across {len(demo_customers_data)} customers.")
    print("Database seeding completed successfully on NeonDB!")
    db.close()

if __name__ == "__main__":
    seed()
