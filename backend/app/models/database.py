from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OperatorRecord(Base):
    __tablename__ = "operator_records"

    id = Column(Integer, primary_key=True, index=True)
    op_name = Column(String(128), unique=True, index=True, nullable=False)
    category = Column(String(64), index=True, nullable=False)
    mps_status = Column(String(32), default="missing") # supported, missing, fallback
    vulkan_status = Column(String(32), default="missing")
    cpu_status = Column(String(32), default="supported")
    cuda_status = Column(String(32), default="supported")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class BenchmarkRecord(Base):
    __tablename__ = "benchmark_records"

    id = Column(Integer, primary_key=True, index=True)
    workload_name = Column(String(128), index=True, nullable=False)
    backend = Column(String(32), index=True, nullable=False)
    batch_size = Column(Integer, nullable=False)
    mean_latency_ms = Column(Float, nullable=False)
    p95_latency_ms = Column(Float, nullable=False)
    throughput_samples_per_sec = Column(Float, nullable=False)
    peak_memory_mb = Column(Float, nullable=False)
    replicated_memory_detected = Column(Boolean, default=False)
    executed_by = Column(String(128), default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class WorkloadPlanRecord(Base):
    __tablename__ = "workload_plan_records"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    target_backend = Column(String(32), nullable=False)
    operators_json = Column(Text, nullable=False)
    coverage_score = Column(Float, nullable=False)
    fallback_ops_json = Column(Text, nullable=False)
    created_by = Column(String(128), default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLogRecord(Base):
    __tablename__ = "audit_log_records"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(64), nullable=False)
    actor = Column(String(128), nullable=False)
    details = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
