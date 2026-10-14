from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import io
import csv
import json

from app.models.database import get_db, OperatorRecord, BenchmarkRecord, WorkloadPlanRecord, AuditLogRecord
from app.core.security import get_current_user, require_role, UserToken
from app.services.operator_catalog import calculate_backend_coverage
from app.services.benchmark_engine import simulate_workload_execution
from app.services.workload_planner import plan_workload_execution
from app.services.llm_advisory import generate_fallback_analysis_advisory

router = APIRouter()

# Schema definitions
class OperatorResponse(BaseModel):
    id: int
    op_name: str
    category: str
    mps_status: str
    vulkan_status: str
    cpu_status: str
    cuda_status: str
    notes: Optional[str] = None

class CreateOperatorRequest(BaseModel):
    op_name: str
    category: str
    mps_status: str = "missing"
    vulkan_status: str = "missing"
    cpu_status: str = "supported"
    cuda_status: str = "supported"
    notes: Optional[str] = ""

class CoverageResponse(BaseModel):
    backend: str
    total_operators: int
    supported: int
    fallback: int
    missing: int
    coverage_rate: float

class RunBenchmarkRequest(BaseModel):
    workload_name: str = "Transformer-Layer-Norm"
    backend: str = "mps"
    batch_size: int = Field(default=32, ge=1, le=1024)
    num_workers: int = Field(default=0, ge=0, le=64)

class CreatePlanRequest(BaseModel):
    title: str = "Vision-Transformer-Inference"
    target_backend: str = "mps"
    requested_ops: List[str]

class AdvisoryRequest(BaseModel):
    plan_id: int
    custom_prompt: Optional[str] = None

@router.get("/operators", response_model=List[OperatorResponse])
def list_operators(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("viewer"))
):
    query = db.query(OperatorRecord)
    if category:
        query = query.filter(OperatorRecord.category == category)
    if search:
        query = query.filter(OperatorRecord.op_name.contains(search))
    return query.offset(offset).limit(limit).all()

@router.get("/operators/export")
def export_operators(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: UserToken = Depends(get_current_user)
):
    operators = db.query(OperatorRecord).all()
    data = [
        {
            "op_name": o.op_name,
            "category": o.category,
            "mps_status": o.mps_status,
            "vulkan_status": o.vulkan_status,
            "cpu_status": o.cpu_status,
            "cuda_status": o.cuda_status,
            "notes": o.notes,
        }
        for o in operators
    ]
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
        writer.writeheader()
        writer.writerows(data)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=operators.csv"}
        )
    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=operators.json"}
    )

@router.post("/operators", response_model=OperatorResponse, status_code=status.HTTP_201_CREATED)
def add_operator(
    req: CreateOperatorRequest,
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("operator"))
):
    existing = db.query(OperatorRecord).filter(OperatorRecord.op_name == req.op_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Operator with this name already exists")
    
    record = OperatorRecord(
        op_name=req.op_name,
        category=req.category,
        mps_status=req.mps_status,
        vulkan_status=req.vulkan_status,
        cpu_status=req.cpu_status,
        cuda_status=req.cuda_status,
        notes=req.notes
    )
    db.add(record)
    audit = AuditLogRecord(
        action="OPERATOR_REGISTERED",
        actor=user.username,
        details=f"Registered operator {req.op_name} in category {req.category}."
    )
    db.add(audit)
    db.commit()
    db.refresh(record)
    return record

@router.get("/coverage/{backend}", response_model=CoverageResponse)
def get_backend_coverage(
    backend: str,
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("viewer"))
):
    return calculate_backend_coverage(db, backend)

@router.post("/benchmarks/run")
def execute_benchmark(
    req: RunBenchmarkRequest,
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("operator"))
):
    return simulate_workload_execution(
        workload_name=req.workload_name,
        backend=req.backend,
        batch_size=req.batch_size,
        num_workers=req.num_workers,
        db=db,
        actor=user.username
    )

@router.get("/benchmarks/history")
def list_benchmark_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("viewer"))
):
    return db.query(BenchmarkRecord).order_by(BenchmarkRecord.id.desc()).limit(limit).all()

@router.get("/benchmarks/export")
def export_benchmarks(
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("viewer"))
):
    records = db.query(BenchmarkRecord).order_by(BenchmarkRecord.id.desc()).limit(limit).all()
    data = [
        {
            "id": r.id,
            "workload_name": r.workload_name,
            "backend": r.backend,
            "batch_size": r.batch_size,
            "mean_latency_ms": r.mean_latency_ms,
            "p95_latency_ms": r.p95_latency_ms,
            "throughput_samples_per_sec": r.throughput_samples_per_sec,
            "peak_memory_mb": r.peak_memory_mb,
            "replicated_memory_detected": r.replicated_memory_detected,
            "executed_by": r.executed_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
        writer.writeheader()
        writer.writerows(data)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=benchmarks.csv"}
        )
    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=benchmarks.json"}
    )

@router.post("/plans/create")
def create_workload_plan(
    req: CreatePlanRequest,
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("operator"))
):
    return plan_workload_execution(
        title=req.title,
        target_backend=req.target_backend,
        requested_ops=req.requested_ops,
        db=db,
        actor=user.username
    )

@router.get("/plans")
def list_plans(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("viewer"))
):
    return db.query(WorkloadPlanRecord).order_by(WorkloadPlanRecord.id.desc()).limit(limit).all()

@router.get("/plans/export")
def export_plans(
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("viewer"))
):
    records = db.query(WorkloadPlanRecord).order_by(WorkloadPlanRecord.id.desc()).limit(limit).all()
    data = [
        {
            "id": r.id,
            "title": r.title,
            "target_backend": r.target_backend,
            "operators_json": r.operators_json,
            "coverage_score": r.coverage_score,
            "fallback_ops_json": r.fallback_ops_json,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
        writer.writeheader()
        writer.writerows(data)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=workload_plans.csv"}
        )
    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=workload_plans.json"}
    )

@router.post("/advisory/analyze")
def run_advisory(
    req: AdvisoryRequest,
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("viewer"))
):
    plan = db.query(WorkloadPlanRecord).filter(WorkloadPlanRecord.id == req.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Workload plan not found")
    
    import json
    summary = {
        "title": plan.title,
        "target_backend": plan.target_backend,
        "coverage_score": plan.coverage_score,
        "fallbacks": json.loads(plan.fallback_ops_json)
    }
    return generate_fallback_analysis_advisory(summary, req.custom_prompt)

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: UserToken = Depends(require_role("admin"))
):
    return db.query(AuditLogRecord).order_by(AuditLogRecord.id.desc()).limit(limit).all()
