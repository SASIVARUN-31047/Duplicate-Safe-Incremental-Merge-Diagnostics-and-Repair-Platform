from sqlalchemy.orm import Session
from datetime import datetime, timezone
from dateutil.parser import parse
from app.models import (
    KeyRegistry, IncomingBatch, IncomingRow, MainGoldenRecord,
    DuplicateFlag, LineageAttribution, RepairDecision, AuditLog
)

def parse_time(dt_str):
    if not dt_str:
        return None
    if isinstance(dt_str, datetime):
        dt = dt_str
    else:
        try:
            dt = parse(dt_str)
        except:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def process_batch(batch_id: str, db: Session):
    batch = db.query(IncomingBatch).filter(IncomingBatch.id == batch_id).first()
    if not batch:
        raise ValueError(f"Batch {batch_id} not found")
        
    rows = db.query(IncomingRow).filter(IncomingRow.batch_id == batch_id).order_by(IncomingRow.id).all()
    
    for row in rows:
        registry = db.query(KeyRegistry).filter(KeyRegistry.entity_name == row.entity_name).first()
        if not registry:
            continue
            
        hash_val = row.composite_key_hash
        
        # Check against existing main record
        existing_golden = db.query(MainGoldenRecord).filter(
            MainGoldenRecord.composite_key_hash == hash_val
        ).first()
        
        if existing_golden:
            handle_duplicate(row, existing_golden, registry, db)
        else:
            insert_new_golden(row, registry, db)

    batch.status = "PROCESSED"
    db.commit()


def insert_new_golden(row: IncomingRow, registry: KeyRegistry, db: Session):
    payload = row.payload
    event_time_str = payload.get(registry.event_time_column)
    event_time = parse_time(event_time_str)
    source = payload.get("source_system", row.batch.source_system)
    
    golden = MainGoldenRecord(
        entity_name=row.entity_name,
        composite_key_hash=row.composite_key_hash,
        payload=payload,
        last_event_time=event_time,
        winning_source=source
    )
    db.add(golden)
    
    db.add(AuditLog(
        batch_id=row.batch_id,
        event_type="NEW_RECORD_INSERTED",
        entity_name=row.entity_name,
        details={"row_id": row.id, "hash": row.composite_key_hash}
    ))
    db.flush()

def handle_duplicate(row: IncomingRow, existing: MainGoldenRecord, registry: KeyRegistry, db: Session):
    payload = row.payload
    ext_payload = existing.payload
    
    new_time = parse_time(payload.get(registry.event_time_column))
    old_time = parse_time(existing.last_event_time)
    
    new_rank = payload.get(registry.rank_column)
    old_rank = ext_payload.get(registry.rank_column)
    
    new_source = payload.get("source_system", "")
    old_source = existing.winning_source

    # Determine type of duplicate
    dup_type = "SOURCE_CONFLICT"
    lineage_step = "MULTI_SOURCE_JOIN"
    
    if payload == ext_payload:
        dup_type = "EXACT_DUPLICATE"
        lineage_step = "API_RETRY"
    elif new_time and old_time and new_time < old_time:
        dup_type = "LATE_ARRIVAL"
        lineage_step = "LATE_STREAM_EVENT"
    
    flag = DuplicateFlag(
        incoming_row_id=row.id,
        duplicate_type=dup_type,
        matched_existing_id=str(existing.id)
    )
    db.add(flag)
    db.flush()
    
    lineage = LineageAttribution(
        duplicate_flag_id=flag.id,
        introduced_by_step=lineage_step,
        source_system=new_source,
        attribution_details={"incoming_hash": row.composite_key_hash}
    )
    db.add(lineage)
    
    # Repair Policy Engine
    decision_str = ""
    reason_str = ""
    winning_payload = None
    update_golden = False
    
    if dup_type == "EXACT_DUPLICATE":
        decision_str = "REPAIRED_EXACT_MATCH"
        reason_str = "Payloads are identical. Ignoring duplicate."
        winning_payload = ext_payload
    else:
        # Rule 1: Rank (lower is better, assuming 1 is top rank)
        if new_rank is not None and old_rank is not None and new_rank != old_rank:
            if new_rank < old_rank:
                decision_str = "REPAIRED_RANK_WIN"
                reason_str = f"Incoming rank {new_rank} is better than existing {old_rank}."
                winning_payload = payload
                update_golden = True
            else:
                decision_str = "REPAIRED_RANK_WIN"
                reason_str = f"Existing rank {old_rank} is better than incoming {new_rank}."
                winning_payload = ext_payload
        # Rule 2: Event Time (newer is better)
        elif new_time and old_time and new_time != old_time:
            if new_time > old_time:
                decision_str = "REPAIRED_EVENT_TIME_WIN"
                reason_str = f"Incoming event time {new_time.isoformat()} is newer than existing {old_time.isoformat()}."
                winning_payload = payload
                update_golden = True
            else:
                decision_str = "REPAIRED_EVENT_TIME_WIN"
                reason_str = f"Existing event time {old_time.isoformat()} is newer than incoming {new_time.isoformat()}."
                winning_payload = ext_payload
        # Rule 3: Source Priority Order
        elif registry.source_priority_order and new_source in registry.source_priority_order and old_source in registry.source_priority_order:
            new_idx = registry.source_priority_order.index(new_source)
            old_idx = registry.source_priority_order.index(old_source)
            if new_idx < old_idx:
                decision_str = "REPAIRED_SOURCE_PRIORITY_WIN"
                reason_str = f"Incoming source '{new_source}' has higher priority."
                winning_payload = payload
                update_golden = True
            elif old_idx < new_idx:
                decision_str = "REPAIRED_SOURCE_PRIORITY_WIN"
                reason_str = f"Existing source '{old_source}' has higher priority."
                winning_payload = ext_payload
            else:
                decision_str = "QUARANTINED"
                reason_str = "Source priorities are equal but payloads differ."
        else:
            decision_str = "QUARANTINED"
            reason_str = "No rules resolved the conflict."
            
    decision = RepairDecision(
        incoming_row_id=row.id,
        duplicate_flag_id=flag.id,
        decision=decision_str,
        winning_row_payload=winning_payload,
        reason=reason_str,
        status="PENDING_REVIEW" if decision_str == "QUARANTINED" else "AUTO_RESOLVED"
    )
    db.add(decision)
    
    if update_golden and decision_str != "QUARANTINED":
        existing.payload = winning_payload
        existing.last_event_time = parse_time(winning_payload.get(registry.event_time_column))
        existing.winning_source = winning_payload.get("source_system", existing.winning_source)
        db.add(AuditLog(
            batch_id=row.batch_id,
            event_type="REPAIR_APPLIED",
            entity_name=row.entity_name,
            details={"row_id": row.id, "decision": decision_str, "reason": reason_str}
        ))
    elif decision_str == "QUARANTINED":
        db.add(AuditLog(
            batch_id=row.batch_id,
            event_type="QUARANTINED",
            entity_name=row.entity_name,
            details={"row_id": row.id, "reason": reason_str}
        ))
    else:
        db.add(AuditLog(
            batch_id=row.batch_id,
            event_type="DUPLICATE_IGNORED",
            entity_name=row.entity_name,
            details={"row_id": row.id, "decision": decision_str, "reason": reason_str}
        ))
        
    db.flush()
