from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class KeyRegistry(Base):
    """
    Key Registry configuration table.
    Defines composite keys, event-time columns, source priorities, and ranking columns per entity.
    """
    __tablename__ = "key_registry"

    id = Column(Integer, primary_key=True, index=True)
    entity_name = Column(String(100), unique=True, nullable=False, index=True)
    composite_keys = Column(JSON, nullable=False)  # e.g., ["customer_id", "order_date"]
    event_time_column = Column(String(100), nullable=False)  # e.g., "event_timestamp"
    source_priority_order = Column(JSON, nullable=False)  # e.g., ["CRM_PRIMARY", "WEB_STORE", "POS_LEGACY"]
    rank_column = Column(String(100), nullable=True)  # e.g., "source_sequence_rank"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class IncomingBatch(Base):
    """
    Tracks ingested batch metadata.
    """
    __tablename__ = "incoming_batches"

    id = Column(String(100), primary_key=True)  # e.g. "batch-20260921-001"
    source_system = Column(String(100), nullable=False)
    status = Column(String(50), default="INGESTED")  # INGESTED, PROCESSED, COMPLETED, FAILED
    total_rows = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    rows = relationship("IncomingRow", back_populates="batch", cascade="all, delete-orphan")


class IncomingRow(Base):
    """
    Raw rows received in an incoming batch.
    """
    __tablename__ = "incoming_rows"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(100), ForeignKey("incoming_batches.id"), nullable=False, index=True)
    entity_name = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    composite_key_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    batch = relationship("IncomingBatch", back_populates="rows")
    duplicate_flags = relationship("DuplicateFlag", back_populates="incoming_row", cascade="all, delete-orphan")
    repair_decisions = relationship("RepairDecision", back_populates="incoming_row", cascade="all, delete-orphan")


class DuplicateFlag(Base):
    """
    Engine output for detected duplicates and conflicts.
    """
    __tablename__ = "duplicate_flags"

    id = Column(Integer, primary_key=True, index=True)
    incoming_row_id = Column(Integer, ForeignKey("incoming_rows.id"), nullable=False, index=True)
    duplicate_type = Column(String(50), nullable=False)  # EXACT_DUPLICATE, LATE_ARRIVAL, SOURCE_CONFLICT, NEAR_DUPLICATE
    matched_existing_id = Column(String(100), nullable=True)  # Matched row identifier in main table or batch
    confidence_score = Column(Float, default=1.0)
    flagged_at = Column(DateTime(timezone=True), default=utc_now)

    incoming_row = relationship("IncomingRow", back_populates="duplicate_flags")
    lineage = relationship("LineageAttribution", back_populates="duplicate_flag", uselist=False, cascade="all, delete-orphan")
    repair_decision = relationship("RepairDecision", back_populates="duplicate_flag", uselist=False)


class LineageAttribution(Base):
    """
    Lineage details identifying the transformation step or source causing the duplicate.
    """
    __tablename__ = "lineage_attributions"

    id = Column(Integer, primary_key=True, index=True)
    duplicate_flag_id = Column(Integer, ForeignKey("duplicate_flags.id"), nullable=False, unique=True)
    introduced_by_step = Column(String(100), nullable=False)  # e.g., "RETRY_INGESTION", "LATE_STREAM_EVENT", "MULTI_SOURCE_JOIN"
    source_system = Column(String(100), nullable=False)
    attribution_details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    duplicate_flag = relationship("DuplicateFlag", back_populates="lineage")


class RepairDecision(Base):
    """
    Repair Policy Engine output decisions.
    """
    __tablename__ = "repair_decisions"

    id = Column(Integer, primary_key=True, index=True)
    incoming_row_id = Column(Integer, ForeignKey("incoming_rows.id"), nullable=False, index=True)
    duplicate_flag_id = Column(Integer, ForeignKey("duplicate_flags.id"), nullable=True, index=True)
    decision = Column(String(100), nullable=False)  # REPAIRED_RANK_WIN, REPAIRED_EVENT_TIME_WIN, REPAIRED_SOURCE_PRIORITY_WIN, QUARANTINED
    winning_row_payload = Column(JSON, nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="AUTO_RESOLVED")  # AUTO_RESOLVED, PENDING_REVIEW, MANUALLY_APPROVED, MANUALLY_REJECTED
    decided_at = Column(DateTime(timezone=True), default=utc_now)

    incoming_row = relationship("IncomingRow", back_populates="repair_decisions")
    duplicate_flag = relationship("DuplicateFlag", back_populates="repair_decision")


class MainGoldenRecord(Base):
    """
    Main Golden Table storing merged, deduplicated, and resolved rows.
    """
    __tablename__ = "main_golden_records"

    id = Column(Integer, primary_key=True, index=True)
    entity_name = Column(String(100), nullable=False, index=True)
    composite_key_hash = Column(String(64), unique=True, nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    last_event_time = Column(DateTime(timezone=True), nullable=True)
    winning_source = Column(String(100), nullable=False)
    merged_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AuditLog(Base):
    """
    Audit and Lineage log table recording all decisions, actions, and KPI events.
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(100), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # BATCH_INGESTED, DUPLICATE_DETECTED, REPAIR_APPLIED, QUARANTINED, MERGED_TO_MAIN, MANUAL_OVERRIDE
    entity_name = Column(String(100), nullable=True)
    details = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now)
