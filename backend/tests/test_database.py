from app.database import SessionLocal
from app.models import KeyRegistry, IncomingBatch, IncomingRow, MainGoldenRecord, AuditLog
from app.seed import seed_database

def test_database_seeding():
    db = SessionLocal()
    try:
        # Seed fresh database
        seed_database(db)

        # 1. Verify Key Registry
        registry = db.query(KeyRegistry).filter(KeyRegistry.entity_name == "customer_orders").first()
        assert registry is not None
        assert registry.composite_keys == ["customer_id", "order_date"]
        assert registry.event_time_column == "event_timestamp"

        # 2. Verify Incoming Batches
        batches = db.query(IncomingBatch).all()
        assert len(batches) == 4
        batch_ids = [b.id for b in batches]
        assert "batch-20260921-001" in batch_ids
        assert "batch-20260921-004" in batch_ids

        # 3. Verify Incoming Rows
        rows = db.query(IncomingRow).all()
        assert len(rows) == 6  # 1 from B1, 1 from B2, 2 from B3, 2 from B4

        # 4. Verify Main Golden Record
        golden_records = db.query(MainGoldenRecord).all()
        assert len(golden_records) == 1
        assert golden_records[0].payload["customer_id"] == "CUST-101"

        # 5. Verify Audit Log
        logs = db.query(AuditLog).all()
        assert len(logs) >= 1
        assert logs[0].event_type == "SYSTEM_INITIALIZED"

    finally:
        db.close()
