import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.models import (
    KeyRegistry, IncomingBatch, IncomingRow, MainGoldenRecord, AuditLog
)

def compute_composite_hash(payload: dict, composite_keys: list[str]) -> str:
    """Computes a deterministic SHA256 hash from composite key values in row payload."""
    key_values = [str(payload.get(k, '')).strip().lower() for k in composite_keys]
    composite_str = "|".join(key_values)
    return hashlib.sha256(composite_str.encode('utf-8')).hexdigest()

def seed_database(db: Session):
    """Resets schema and seeds initial key registry, main golden table, and synthetic batches."""
    # Re-create all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("DB Schema initialized.")

    # 1. Seed Key Registry Configuration
    registry_config = KeyRegistry(
        entity_name="customer_orders",
        composite_keys=["customer_id", "order_date"],
        event_time_column="event_timestamp",
        source_priority_order=["CRM_PRIMARY", "WEB_STORE", "POS_LEGACY"],
        rank_column="source_rank",
        is_active=True
    )
    db.add(registry_config)
    db.commit()
    db.refresh(registry_config)
    print(f"Seeded Key Registry for entity '{registry_config.entity_name}'.")

    # 2. Seed Pre-existing Record in Main Golden Table
    main_payload_1 = {
        "customer_id": "CUST-101",
        "order_date": "2026-09-20",
        "customer_name": "Alice Smith",
        "amount": 150.00,
        "event_timestamp": "2026-09-20T10:00:00Z",
        "source_system": "CRM_PRIMARY",
        "source_rank": 1
    }
    hash_1 = compute_composite_hash(main_payload_1, registry_config.composite_keys)

    existing_golden = MainGoldenRecord(
        entity_name="customer_orders",
        composite_key_hash=hash_1,
        payload=main_payload_1,
        last_event_time=datetime.fromisoformat("2026-09-20T10:00:00+00:00"),
        winning_source="CRM_PRIMARY"
    )
    db.add(existing_golden)
    db.commit()
    print("Seeded Main Golden Table record CUST-101.")

    # 3. Seed Synthetic Ingestion Batches with Planted Duplicate Scenarios

    # Batch 001: Exact Duplicate (API Retry scenario)
    batch_1 = IncomingBatch(
        id="batch-20260921-001",
        source_system="CRM_PRIMARY",
        status="INGESTED",
        total_rows=1
    )
    db.add(batch_1)
    db.commit()

    row_b1 = IncomingRow(
        batch_id=batch_1.id,
        entity_name="customer_orders",
        payload={
            "customer_id": "CUST-101",
            "order_date": "2026-09-20",
            "customer_name": "Alice Smith",
            "amount": 150.00,
            "event_timestamp": "2026-09-20T10:00:00Z",
            "source_system": "CRM_PRIMARY",
            "source_rank": 1
        },
        composite_key_hash=hash_1
    )
    db.add(row_b1)

    # Batch 002: Late Arrival (Older timestamp arriving after newer main table record)
    batch_2 = IncomingBatch(
        id="batch-20260921-002",
        source_system="WEB_STORE",
        status="INGESTED",
        total_rows=1
    )
    db.add(batch_2)
    db.commit()

    row_b2 = IncomingRow(
        batch_id=batch_2.id,
        entity_name="customer_orders",
        payload={
            "customer_id": "CUST-101",
            "order_date": "2026-09-20",
            "customer_name": "Alice Smith",
            "amount": 140.00,  # Outdated amount
            "event_timestamp": "2026-09-19T08:00:00Z",  # Older timestamp
            "source_system": "WEB_STORE",
            "source_rank": 2
        },
        composite_key_hash=hash_1
    )
    db.add(row_b2)

    # Batch 003: Multi-Source Conflict (Same key, same event-time, CRM vs POS rank decision)
    batch_3 = IncomingBatch(
        id="batch-20260921-003",
        source_system="MULTI_SOURCE_FEED",
        status="INGESTED",
        total_rows=2
    )
    db.add(batch_3)
    db.commit()

    payload_b3_pos = {
        "customer_id": "CUST-102",
        "order_date": "2026-09-21",
        "customer_name": "Bob Jones",
        "amount": 300.00,
        "event_timestamp": "2026-09-21T09:00:00Z",
        "source_system": "POS_LEGACY",
        "source_rank": 3
    }
    hash_b3 = compute_composite_hash(payload_b3_pos, registry_config.composite_keys)

    payload_b3_crm = {
        "customer_id": "CUST-102",
        "order_date": "2026-09-21",
        "customer_name": "Bob Jones",
        "amount": 320.00,
        "event_timestamp": "2026-09-21T09:00:00Z",
        "source_system": "CRM_PRIMARY",
        "source_rank": 1
    }

    db.add(IncomingRow(batch_id=batch_3.id, entity_name="customer_orders", payload=payload_b3_pos, composite_key_hash=hash_b3))
    db.add(IncomingRow(batch_id=batch_3.id, entity_name="customer_orders", payload=payload_b3_crm, composite_key_hash=hash_b3))

    # Batch 004: Ambiguous Conflict (Unranked sources, conflicting amounts -> Quarantine)
    batch_4 = IncomingBatch(
        id="batch-20260921-004",
        source_system="PARTNER_EXTRACT",
        status="INGESTED",
        total_rows=2
    )
    db.add(batch_4)
    db.commit()

    payload_b4_p1 = {
        "customer_id": "CUST-103",
        "order_date": "2026-09-21",
        "customer_name": "Charlie Brown",
        "amount": 500.00,
        "event_timestamp": "2026-09-21T10:00:00Z",
        "source_system": "UNKNOWN_PARTNER",
        "source_rank": 99
    }
    hash_b4 = compute_composite_hash(payload_b4_p1, registry_config.composite_keys)

    payload_b4_p2 = {
        "customer_id": "CUST-103",
        "order_date": "2026-09-21",
        "customer_name": "Charlie Brown",
        "amount": 550.00,  # Conflicting value
        "event_timestamp": "2026-09-21T10:00:00Z",
        "source_system": "THIRD_PARTY_FEED",
        "source_rank": 99
    }

    db.add(IncomingRow(batch_id=batch_4.id, entity_name="customer_orders", payload=payload_b4_p1, composite_key_hash=hash_b4))
    db.add(IncomingRow(batch_id=batch_4.id, entity_name="customer_orders", payload=payload_b4_p2, composite_key_hash=hash_b4))

    db.commit()

    # Seed Initial Audit Log entry
    audit_entry = AuditLog(
        batch_id="SYSTEM_INIT",
        event_type="SYSTEM_INITIALIZED",
        entity_name="customer_orders",
        details={"message": "Database schema created and synthetic test batches seeded successfully."}
    )
    db.add(audit_entry)
    db.commit()
    print("Seeded synthetic test batches (Exact Duplicate, Late Arrival, Source Conflict, Ambiguous Quarantine).")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
