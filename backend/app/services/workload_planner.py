import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import OperatorRecord, WorkloadPlanRecord, AuditLogRecord

def plan_workload_execution(
    title: str,
    target_backend: str,
    requested_ops: List[str],
    db: Session,
    actor: str = "operator"
) -> Dict[str, Any]:
    """
    Evaluates a set of neural network operators against a requested execution backend.
    Identifies unsupported operators, synthesizes CPU fallback nodes, and computes a deployment readiness score.
    """
    all_records = db.query(OperatorRecord).all()
    op_map = {r.op_name: r for r in all_records}

    col_map = {
        "mps": "mps_status",
        "vulkan": "vulkan_status",
        "cpu": "cpu_status",
        "cuda": "cuda_status"
    }
    col_attr = col_map.get(target_backend.lower(), "cpu_status")

    supported_nodes: List[Dict[str, str]] = []
    fallback_nodes: List[Dict[str, str]] = []
    missing_nodes: List[Dict[str, str]] = []

    for op in requested_ops:
        record = op_map.get(op)
        if not record:
            # Op not in catalog; requires CPU fallback or fails
            missing_nodes.append({
                "op": op,
                "reason": "Operator unrecognized in standard catalog; default to CPU graph partition.",
                "resolved_target": "cpu"
            })
            continue

        status_val = getattr(record, col_attr)
        if status_val == "supported":
            supported_nodes.append({"op": op, "target": target_backend})
        elif status_val == "fallback":
            fallback_nodes.append({
                "op": op,
                "target": "cpu",
                "notes": record.notes
            })
        else:
            fallback_nodes.append({
                "op": op,
                "target": "cpu",
                "notes": f"Missing on {target_backend}; routed to host CPU execution kernel."
            })

    total = len(requested_ops)
    if total > 0:
        coverage_score = round((len(supported_nodes) / total) * 100.0, 2)
    else:
        coverage_score = 100.0

    plan_record = WorkloadPlanRecord(
        title=title,
        target_backend=target_backend,
        operators_json=json.dumps(requested_ops),
        coverage_score=coverage_score,
        fallback_ops_json=json.dumps(fallback_nodes + missing_nodes),
        created_by=actor
    )
    db.add(plan_record)
    audit = AuditLogRecord(
        action="PLAN_CREATION",
        actor=actor,
        details=f"Created workload plan '{title}' for target {target_backend} with score {coverage_score}%."
    )
    db.add(audit)
    db.commit()
    db.refresh(plan_record)

    return {
        "id": plan_record.id,
        "title": title,
        "target_backend": target_backend,
        "total_ops": total,
        "supported_ops_count": len(supported_nodes),
        "fallback_ops_count": len(fallback_nodes) + len(missing_nodes),
        "coverage_score": coverage_score,
        "supported_nodes": supported_nodes,
        "fallbacks": fallback_nodes + missing_nodes,
        "is_hardware_accelerated": len(supported_nodes) > 0
    }
