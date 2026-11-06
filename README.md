# FixLoop — The AI That Remembers Every Customer's Problem

> **Hackathon Category:** Operations & Support  
> **Tagline:** Every complaint creates experience. Every confirmed outcome becomes memory. Every new case benefits from what the business has already learned.

---

## 1. Product Overview

**FixLoop** is an AI-powered operations-support and repair intelligence platform for electronics and home-appliance service businesses.

Traditional CRMs store static tickets, but do not connect repair actions with actual outcomes. When an issue returns, new support staff start from zero, repeat unhelpful troubleshooting steps, miss promised callbacks, and fail to detect cross-customer failure trends.

FixLoop solves this with a **three-level collective learning loop**:
1. **Level 1 — Customer Intelligence:** Customer 360 timeline of complaints, repairs, and confirmed outcomes.
2. **Level 2 — Repair Intelligence:** Recalls what was previously attempted; provides evidence-backed, counterfactual guidance on what to inspect next.
3. **Level 3 — Business Intelligence (The Ripple Effect):** Cross-customer pattern detection that identifies emerging product/model-level defects across distinct customers.

---

## 2. Technical Architecture & Tech Stack

```
[React + Vite Frontend (Tailwind CSS, Lucide Icons)]
                     │ HTTP / JSON
                     ▼
             [FastAPI Backend]
           ┌─────────┼─────────┐
           │         │         │
           ▼         ▼         ▼
       [SQLite]   [Groq LLM] [Hindsight Cloud]
  (Structured DB) (Advisory)  (Experience Memory)
```

- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, Axios.
- **Backend API:** Python 3, FastAPI, Pydantic v2, SQLAlchemy.
- **Structured Database:** SQLite (Customers, Products, Tickets, Repairs, Follow-ups, Pattern Alerts).
- **Experience Memory:** Hindsight Cloud (`retain` confirmed outcomes, `recall` semantic case context).
- **LLM Reasoning:** Groq API (fast inference with structured JSON output and evidence citations).

---

## 3. Quickstart & Run Instructions

### Step 1: Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# (Optional) Add your HINDSIGHT_API_KEY and GROQ_API_KEY into backend/.env

# Seed deterministic demo dataset
python3 -m app.seed_data

# Start backend server (runs on port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Frontend Setup
```bash
cd frontend
npm install
npm run dev
# App will open at http://localhost:5173
```

### Step 3: Run Tests
```bash
cd backend
PYTHONPATH=. ./venv/bin/pytest tests/
```

---

## 4. Reproducible 5-Minute Judge Demo Walkthrough

1. **Dashboard Overview (`/`)**:
   - Show the operational overview: Total Tickets (8), Active Repeat Cases, Ripple Effect Model Clusters, and Overdue Customer Rescues.
   - Point out the **"Needs Attention" Queue** highlighting the overdue callback for Rahul and the active Model X drainage pattern alert.
2. **Customer 360 Timeline (`/customer-360`)**:
   - Select **Rahul Sharma**. Show his first complaint (Ticket `TCK-1001` on Model X with error E20).
   - Point out the recorded repair outcome: *Drain pipe cleaning marked as "temporary" after issue returned in 5 days*.
3. **Memory Explorer (`/memory-explorer`)**:
   - Highlight the **Hindsight Memory Explorer**. Show the actual `retain` event logged for Rahul's repair outcome with its provider reference and payload.
   - Explain the architectural difference: SQLite stores structured relational facts; Hindsight retains persistent semantic experience vectors.
4. **Repeat Issue Capture & Real Recall (`/new-complaint`)**:
   - Click **"Insert Rahul Demo Repeat Case"** (or enter: *"Drainage error E20 returned after 5 days. Water is stuck in the drum again."*).
   - Submit the ticket. Notice how FixLoop flags the case as a repeat complaint and triggers an immediate **Hindsight Recall**.
5. **AI Repair Assistant (`/assistant`)**:
   - View the AI Repair Advisory:
     - Notice the **Repeat Issue Alert**: The AI explains that surface pipe cleaning previously failed for Rahul.
     - Notice the **Counterfactual Advice**: Rather than repeating pipe cleaning, it advises inspecting the internal drain pump impeller and pressure switch wiring.
     - Point out the **Supporting Evidence Citations**: Cites both SQLite Ticket #1001 and Hindsight memory ID.
6. **Authorized Staff Outcome Confirmation**:
   - Under *Authorized Staff Repair Confirmation*, record:
     - Action: *"Replaced internal drain pump motor assembly"*
     - Outcome: *"successful"*
   - Click **Confirm & Retain in Memory**. Explain to judges that this confirmed fix is now permanently retained into Hindsight for all future cases.
7. **The Ripple Effect (`/ripple-effect`)**:
   - Open the **Ripple Effect** view. Show the Model X cluster (7 distinct customer cases reporting drainage failure).
   - Expand the supporting customer tickets table (Aman, Priya, Karan, Neha, Riya, Arjun). Explain how operations can alert engineering to investigate component supplier batches before issues escalate.
8. **Proactive Customer Rescue (`/followups`)**:
   - Open the **Follow-Up Center**. Show Rahul's overdue 5-day post-repair check-in.
   - Click **Complete Callback** to resolve the reminder after staff intervention.
