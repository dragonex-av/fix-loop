from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, Base, engine
from app.models import Customer, Product, Ticket, RepairRecord, Followup, MemoryEvent
from app.services.pattern_service import pattern_service

def seed():
    # Reset all tables cleanly for reproducible demo state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    now = datetime.now(timezone.utc)

    print("Seeding deterministic FixLoop benchmark demo data...")

    # 1. Customers & Products
    demo_customers = [
        {"name": "Rahul Sharma", "phone": "+91-98765-43210", "email": "rahul.s@example.com", "model": "Model X", "type": "Washing Machine"},
        {"name": "Aman Verma", "phone": "+91-98111-22334", "email": "aman.v@example.com", "model": "Model X", "type": "Washing Machine"},
        {"name": "Priya Nair", "phone": "+91-98222-33445", "email": "priya.n@example.com", "model": "Model X", "type": "Washing Machine"},
        {"name": "Karan Patel", "phone": "+91-98333-44556", "email": "karan.p@example.com", "model": "Model X", "type": "Washing Machine"},
        {"name": "Neha Gupta", "phone": "+91-98444-55667", "email": "neha.g@example.com", "model": "Model X", "type": "Washing Machine"},
        {"name": "Riya Sen", "phone": "+91-98555-66778", "email": "riya.s@example.com", "model": "Model X", "type": "Washing Machine"},
        {"name": "Arjun Mehta", "phone": "+91-98666-77889", "email": "arjun.m@example.com", "model": "Model X", "type": "Washing Machine"},
        {"name": "Meera Joshi", "phone": "+91-98777-88990", "email": "meera.j@example.com", "model": "Model Y", "type": "Refrigerator"},
    ]

    cust_objs = {}
    prod_objs = {}

    for c in demo_customers:
        cust = Customer(name=c["name"], phone=c["phone"], email=c["email"], created_at=now - timedelta(days=20))
        db.add(cust)
        db.flush()
        cust_objs[c["name"]] = cust

        prod = Product(
            customer_id=cust.id,
            product_type=c["type"],
            brand="Apex Appliances",
            model=c["model"],
            serial_number=f"APX-{c['model'][:1]}-{cust.id:04d}",
            created_at=now - timedelta(days=20)
        )
        db.add(prod)
        db.flush()
        prod_objs[c["name"]] = prod

    # 2. Tickets & Repairs
    # Case 1: Rahul - first ticket (Drain pipe cleaning -> temporary; issue returned after 5 days)
    t1 = Ticket(
        ticket_code="TCK-1001",
        customer_id=cust_objs["Rahul Sharma"].id,
        product_id=prod_objs["Rahul Sharma"].id,
        issue_description="Washing machine stops halfway with E20 drainage error. Water pooling inside drum.",
        issue_category="Drainage issue",
        status="Resolved",
        priority="High",
        created_at=now - timedelta(days=12)
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

    # Initial Hindsight retain memory log for Rahul
    mem1 = MemoryEvent(
        entity_type="repair",
        entity_id=r1.id,
        operation="retain",
        query_or_content="REPAIR EXPERIENCE for Model X (Drainage issue): Action performed: 'Drain pipe cleaning & debris unclogging'. Confirmed outcome: 'temporary'. Technician notes: 'Unclogged main discharge hose. Advised customer issue may return if internal pump valve sticks'. Original complaint: 'Washing machine stops halfway with E20 drainage error'. Ticket: TCK-1001.",
        provider_ref="hs-mem-exp-1001-rahul",
        status="success",
        raw_response='{"status": "retained", "memory_id": "hs-mem-exp-1001-rahul", "vectors_updated": true, "bank": "fixloop-operations"}',
        created_at=now - timedelta(days=11)
    )
    db.add(mem1)

    # Follow-up for Rahul (Overdue - demonstrating flow D!)
    f1 = Followup(
        customer_id=cust_objs["Rahul Sharma"].id,
        ticket_id=t1.id,
        promised_at=now - timedelta(hours=4),  # 4 hours overdue!
        owner="Sarah Jenkins (Service Lead)",
        status="overdue",
        notes="Post-repair 5-day check-in to confirm if drainage error recurred.",
        created_at=now - timedelta(days=5)
    )
    db.add(f1)

    # Case 2: Aman - Filter inspection -> pending confirmation
    t2 = Ticket(
        ticket_code="TCK-1002",
        customer_id=cust_objs["Aman Verma"].id,
        product_id=prod_objs["Aman Verma"].id,
        issue_description="Drum won't drain water after rinse cycle on Model X.",
        issue_category="Drainage issue",
        status="In Progress",
        priority="Medium",
        created_at=now - timedelta(days=8)
    )
    db.add(t2)
    db.flush()
    r2 = RepairRecord(
        ticket_id=t2.id,
        action="Filter inspection & lint removal",
        outcome="pending",
        technician_notes="Lint filter inspected; awaiting customer cycle test.",
        created_at=now - timedelta(days=7)
    )
    db.add(r2)

    # Case 3: Priya - Drainage check -> unsuccessful
    t3 = Ticket(
        ticket_code="TCK-1003",
        customer_id=cust_objs["Priya Nair"].id,
        product_id=prod_objs["Priya Nair"].id,
        issue_description="Standing water in drum at end of wash cycle; buzzer beeps continuously.",
        issue_category="Drainage issue",
        status="In Progress",
        priority="High",
        created_at=now - timedelta(days=6)
    )
    db.add(t3)
    db.flush()
    r3 = RepairRecord(
        ticket_id=t3.id,
        action="Drainage check & hose reseating",
        outcome="unsuccessful",
        technician_notes="Reseated external drain hose but error code persists on spin cycle.",
        confirmed_by="Rajesh Roy (Lead Tech)",
        confirmed_at=now - timedelta(days=5),
        created_at=now - timedelta(days=5)
    )
    db.add(r3)

    mem3 = MemoryEvent(
        entity_type="repair",
        entity_id=r3.id,
        operation="retain",
        query_or_content="REPAIR EXPERIENCE for Model X (Drainage issue): Action performed: 'Drainage check & hose reseating'. Confirmed outcome: 'unsuccessful'. Ticket: TCK-1003.",
        provider_ref="hs-mem-exp-1003-priya",
        status="success",
        raw_response='{"status": "retained", "memory_id": "hs-mem-exp-1003-priya", "vectors_updated": true}',
        created_at=now - timedelta(days=5)
    )
    db.add(mem3)

    # Case 4: Karan - No repair recorded yet
    t4 = Ticket(
        ticket_code="TCK-1004",
        customer_id=cust_objs["Karan Patel"].id,
        product_id=prod_objs["Karan Patel"].id,
        issue_description="Model X showing drainage timeout error on delicate wash.",
        issue_category="Drainage issue",
        status="Open",
        priority="Medium",
        created_at=now - timedelta(days=4)
    )
    db.add(t4)

    # Case 5: Neha - Pump inspection -> pending
    t5 = Ticket(
        ticket_code="TCK-1005",
        customer_id=cust_objs["Neha Gupta"].id,
        product_id=prod_objs["Neha Gupta"].id,
        issue_description="Water stays in machine after wash. Loud humming noise from bottom right.",
        issue_category="Drainage issue",
        status="In Progress",
        priority="High",
        created_at=now - timedelta(days=3)
    )
    db.add(t5)
    db.flush()
    r5 = RepairRecord(
        ticket_id=t5.id,
        action="Pump inspection & impeller cleaning",
        outcome="pending",
        technician_notes="Assessing motor winding impedance.",
        created_at=now - timedelta(days=2)
    )
    db.add(r5)

    # Case 6 & 7: Riya & Arjun - open complaints
    t6 = Ticket(
        ticket_code="TCK-1006",
        customer_id=cust_objs["Riya Sen"].id,
        product_id=prod_objs["Riya Sen"].id,
        issue_description="Drain cycle fails intermittently; water left behind.",
        issue_category="Drainage issue",
        status="Open",
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
        priority="High",
        created_at=now - timedelta(hours=6)
    )
    db.add(t7)

    # Case 8: Meera (Negative control) - Model Y Cooling issue
    t8 = Ticket(
        ticket_code="TCK-1008",
        customer_id=cust_objs["Meera Joshi"].id,
        product_id=prod_objs["Meera Joshi"].id,
        issue_description="Refrigerator fresh food compartment warm; freezer is working fine.",
        issue_category="Cooling issue",
        status="New",
        priority="Medium",
        created_at=now - timedelta(hours=14)
    )
    db.add(t8)

    # Additional upcoming follow-up
    f2 = Followup(
        customer_id=cust_objs["Neha Gupta"].id,
        ticket_id=t5.id,
        promised_at=now + timedelta(days=1),
        owner="Vikram Singh",
        status="upcoming",
        notes="Call customer to check if pump humming stopped.",
        created_at=now - timedelta(days=1)
    )
    db.add(f2)

    db.commit()

    # Automatically compute and populate Ripple Effect patterns from the seeded cases
    patterns = pattern_service.scan_and_update_patterns(db)
    print(f"Generated {len(patterns)} Ripple Effect pattern alert(s) across {len(demo_customers)} customers.")
    print("Database seeding completed successfully!")
    db.close()

if __name__ == "__main__":
    seed()
