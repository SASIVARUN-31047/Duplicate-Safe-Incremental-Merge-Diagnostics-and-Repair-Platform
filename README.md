# Duplicate-Safe Incremental Merge Diagnostics & Repair Platform (DEAI-10)

A capstone data-engineering web platform that ingests data batches, detects duplicates against existing records using configurable composite keys, attributes duplicate root causes to specific upstream pipeline transformations/sources, applies deterministic repair policies, auto-merges resolved records, and quarantines ambiguous records for manual review via an interactive dashboard.

## Tech Stack
- **Frontend**: Next.js (App Router, TypeScript) + Tailwind CSS
- **Backend**: Python + FastAPI + SQLAlchemy
- **Database**: PostgreSQL
- **Deployment Targets**: Render (Backend & DB), Vercel (Frontend)

## Project Structure
```
duplicate-repair-platform/
├── backend/            # FastAPI app, duplicate engine, repair policies, unit tests
└── frontend/           # Next.js dashboard UI, root-cause diagnostic views, KPI cards
```

## Setup & Local Run

### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000` and connects to backend at `http://localhost:8000`.

## Architecture & Core Components
1. **Incoming Data Batch Ingestion**
2. **Key Registry Manager**
3. **Duplicate Detection Engine**
4. **Lineage Attribution Tracker**
5. **Repair Policy Engine**
6. **Quarantine Review Queue**
7. **Main Table Merge Handler**
8. **Audit Log & KPI Metrics**
9. **Interactive Diagnostics Dashboard**
