from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

from app.database import SessionLocal, engine
from app.models import (
    Base, IncomingBatch, IncomingRow, DuplicateFlag, 
    RepairDecision, AuditLog, MainGoldenRecord, LineageAttribution
)
from app.engine import process_batch, parse_time
from app.seed import seed_database

app = FastAPI(
    title="Duplicate-Safe Incremental Merge Diagnostics & Repair Platform",
    description="Backend API for detecting, attributing, repairing, and auditing data duplicate records.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "online", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# --- API Endpoints ---

@app.post("/api/seed")
def seed_and_process_demo_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Seeds the DB with synthetic data and processes all batches."""
    seed_database(db)
    # Process all un-processed batches
    batches = db.query(IncomingBatch).filter(IncomingBatch.status == "INGESTED").all()
    for b in batches:
        process_batch(b.id, db)
    return {"message": "Database seeded and all batches processed successfully."}

@app.get("/api/batches")
def get_batches(db: Session = Depends(get_db)):
    batches = db.query(IncomingBatch).order_by(IncomingBatch.created_at.desc()).all()
    return [{"id": b.id, "source": b.source_system, "status": b.status, "total_rows": b.total_rows, "created_at": b.created_at} for b in batches]

@app.get("/api/duplicates")
def get_duplicates(db: Session = Depends(get_db)):
    flags = db.query(DuplicateFlag).all()
    result = []
    for f in flags:
        decision = f.repair_decision
        result.append({
            "id": f.id,
            "type": f.duplicate_type,
            "confidence": f.confidence_score,
            "batch_id": f.incoming_row.batch_id,
            "incoming_row_id": f.incoming_row_id,
            "matched_existing_id": f.matched_existing_id,
            "decision": decision.decision if decision else None,
            "decision_status": decision.status if decision else None,
            "decision_id": decision.id if decision else None
        })
    return result

@app.get("/api/duplicates/{flag_id}/root-cause")
def get_root_cause(flag_id: int, db: Session = Depends(get_db)):
    flag = db.query(DuplicateFlag).filter(DuplicateFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Duplicate flag not found")
        
    decision = flag.repair_decision
    lineage = flag.lineage
    incoming_row = flag.incoming_row
    
    # Try fetching the matched main record if it exists
    existing = db.query(MainGoldenRecord).filter(MainGoldenRecord.id == flag.matched_existing_id).first() if flag.matched_existing_id else None

    return {
        "flag_id": flag.id,
        "duplicate_type": flag.duplicate_type,
        "lineage": {
            "step": lineage.introduced_by_step if lineage else "UNKNOWN",
            "source": lineage.source_system if lineage else "UNKNOWN"
        },
        "incoming_payload": incoming_row.payload,
        "existing_payload": existing.payload if existing else None,
        "decision": {
            "action": decision.decision if decision else None,
            "reason": decision.reason if decision else None,
            "status": decision.status if decision else None
        }
    }

class QuarantineResolution(BaseModel):
    action: str  # "APPROVE_INCOMING" or "KEEP_EXISTING"

@app.post("/api/quarantine/{decision_id}/resolve")
def resolve_quarantine(decision_id: int, resolution: QuarantineResolution, db: Session = Depends(get_db)):
    decision = db.query(RepairDecision).filter(RepairDecision.id == decision_id).first()
    if not decision or decision.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail="Invalid decision ID or not in PENDING_REVIEW status")
        
    flag = decision.duplicate_flag
    incoming_row = flag.incoming_row
    existing = db.query(MainGoldenRecord).filter(MainGoldenRecord.id == flag.matched_existing_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Existing golden record not found")

    if resolution.action == "APPROVE_INCOMING":
        # Overwrite golden with incoming
        existing.payload = incoming_row.payload
        event_time_str = incoming_row.payload.get("event_timestamp")
        existing.last_event_time = parse_time(event_time_str)
        existing.winning_source = incoming_row.payload.get("source_system", "MANUAL_OVERRIDE")
        
        decision.status = "MANUALLY_APPROVED"
        decision.decision = "MANUAL_OVERRIDE_INCOMING_WON"
        decision.winning_row_payload = incoming_row.payload
        
        db.add(AuditLog(
            batch_id=incoming_row.batch_id,
            event_type="MANUAL_OVERRIDE",
            entity_name=incoming_row.entity_name,
            details={"row_id": incoming_row.id, "action": "APPROVE_INCOMING"}
        ))
        
    elif resolution.action == "KEEP_EXISTING":
        decision.status = "MANUALLY_REJECTED"
        decision.decision = "MANUAL_OVERRIDE_EXISTING_WON"
        
        db.add(AuditLog(
            batch_id=incoming_row.batch_id,
            event_type="MANUAL_OVERRIDE",
            entity_name=incoming_row.entity_name,
            details={"row_id": incoming_row.id, "action": "KEEP_EXISTING"}
        ))
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    db.commit()
    return {"message": "Quarantine resolved successfully", "status": decision.status}

@app.get("/api/kpis")
def get_kpis(db: Session = Depends(get_db)):
    total_processed = db.query(func.count(IncomingRow.id)).scalar() or 0
    total_duplicates = db.query(func.count(DuplicateFlag.id)).scalar() or 0
    
    auto_repaired = db.query(func.count(RepairDecision.id)).filter(
        RepairDecision.status == "AUTO_RESOLVED", 
        RepairDecision.decision.like("REPAIRED_%")
    ).scalar() or 0
    
    quarantined = db.query(func.count(RepairDecision.id)).filter(
        RepairDecision.status == "PENDING_REVIEW"
    ).scalar() or 0
    
    return {
        "total_rows_processed": total_processed,
        "duplicates_detected": total_duplicates,
        "auto_repaired": auto_repaired,
        "quarantined_pending_review": quarantined,
        "false_block_rate": f"{(auto_repaired / total_duplicates * 100):.1f}%" if total_duplicates > 0 else "0%"
    }

class IncomingBatchPayload(BaseModel):
    batch_id: str
    source_system: str
    entity_name: str
    rows: List[Dict[str, Any]]

@app.post("/api/batches/ingest")
def ingest_batch(payload: IncomingBatchPayload, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if batch exists
    if db.query(IncomingBatch).filter(IncomingBatch.id == payload.batch_id).first():
        raise HTTPException(status_code=400, detail="Batch already exists")
        
    registry = db.query(KeyRegistry).filter(KeyRegistry.entity_name == payload.entity_name).first()
    if not registry:
        raise HTTPException(status_code=400, detail="Entity not registered in KeyRegistry")

    import hashlib
    def compute_hash(p: dict, keys: list[str]) -> str:
        key_vals = [str(p.get(k, '')).strip().lower() for k in keys]
        return hashlib.sha256("|".join(key_vals).encode('utf-8')).hexdigest()

    batch = IncomingBatch(id=payload.batch_id, source_system=payload.source_system, status="INGESTED", total_rows=len(payload.rows))
    db.add(batch)
    
    for row_data in payload.rows:
        h = compute_hash(row_data, registry.composite_keys)
        db.add(IncomingRow(batch_id=batch.id, entity_name=payload.entity_name, payload=row_data, composite_key_hash=h))
        
    db.commit()
    
    # Process immediately
    process_batch(batch.id, db)
    return {"message": "Batch ingested and processed successfully", "batch_id": batch.id}
