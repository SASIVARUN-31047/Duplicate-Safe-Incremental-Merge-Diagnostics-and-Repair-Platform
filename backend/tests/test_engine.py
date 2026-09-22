import pytest
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.seed import seed_database
from app.engine import process_batch
from app.models import (
    IncomingBatch, DuplicateFlag, RepairDecision, MainGoldenRecord, AuditLog
)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    seed_database(db)
    yield db
    db.close()

def test_batch_001_exact_duplicate(db_session: Session):
    process_batch("batch-20260921-001", db_session)
    batch = db_session.query(IncomingBatch).filter_by(id="batch-20260921-001").first()
    assert batch.status == "PROCESSED"
    
    # Should flag EXACT_DUPLICATE
    flags = db_session.query(DuplicateFlag).join(DuplicateFlag.incoming_row).filter(
        DuplicateFlag.incoming_row.has(batch_id="batch-20260921-001")
    ).all()
    assert len(flags) == 1
    assert flags[0].duplicate_type == "EXACT_DUPLICATE"
    
    decisions = db_session.query(RepairDecision).join(RepairDecision.incoming_row).filter(
        RepairDecision.incoming_row.has(batch_id="batch-20260921-001")
    ).all()
    assert len(decisions) == 1
    assert decisions[0].decision == "REPAIRED_EXACT_MATCH"

def test_batch_002_late_arrival(db_session: Session):
    process_batch("batch-20260921-002", db_session)
    
    flags = db_session.query(DuplicateFlag).join(DuplicateFlag.incoming_row).filter(
        DuplicateFlag.incoming_row.has(batch_id="batch-20260921-002")
    ).all()
    assert len(flags) == 1
    assert flags[0].duplicate_type == "LATE_ARRIVAL"
    
    decisions = db_session.query(RepairDecision).join(RepairDecision.incoming_row).filter(
        RepairDecision.incoming_row.has(batch_id="batch-20260921-002")
    ).all()
    assert len(decisions) == 1
    # Existing time is newer, so existing wins by event time
    assert decisions[0].decision == "REPAIRED_RANK_WIN"


def test_batch_003_multi_source_conflict(db_session: Session):
    process_batch("batch-20260921-003", db_session)
    
    # Batch 3 has 2 rows. One goes to insert_new_golden, the second hits handle_duplicate.
    flags = db_session.query(DuplicateFlag).join(DuplicateFlag.incoming_row).filter(
        DuplicateFlag.incoming_row.has(batch_id="batch-20260921-003")
    ).all()
    assert len(flags) == 1
    assert flags[0].duplicate_type == "SOURCE_CONFLICT"
    
    decisions = db_session.query(RepairDecision).join(RepairDecision.incoming_row).filter(
        RepairDecision.incoming_row.has(batch_id="batch-20260921-003")
    ).all()
    assert len(decisions) == 1
    assert decisions[0].decision == "REPAIRED_RANK_WIN"

def test_batch_004_ambiguous_quarantine(db_session: Session):
    process_batch("batch-20260921-004", db_session)
    
    decisions = db_session.query(RepairDecision).join(RepairDecision.incoming_row).filter(
        RepairDecision.incoming_row.has(batch_id="batch-20260921-004")
    ).all()
    assert len(decisions) == 1
    assert decisions[0].decision == "QUARANTINED"
    assert decisions[0].status == "PENDING_REVIEW"
