import math
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.database import BenchmarkRecord, AuditLogRecord

def simulate_workload_execution(
    workload_name: str,
    backend: str,
    batch_size: int,
    num_workers: int = 0,
    db: Session = None,
    actor: str = "operator"
) -> Dict[str, Any]:
    """
    Simulates latency, throughput, and memory scaling characteristics
    for dynamic neural networks across hardware targets.
    Includes explicit modeling of the DataLoader worker memory replication issue (#13246).
    """
    base_latencies = {
        "cuda": 4.2,
        "mps": 8.5,
        "vulkan": 11.2,
        "cpu": 28.0
    }
    base_lat = base_latencies.get(backend.lower(), 25.0)

    # Scaling with batch size: sublinear compute due to vectorization, but quadratic memory in attention
    complexity_multiplier = 1.0 + (math.log2(max(1, batch_size)) * 0.35)
    mean_latency = round(base_lat * complexity_multiplier, 3)
    p95_latency = round(mean_latency * 1.22, 3)
    
    # Throughput calculation in samples/sec
    throughput = round((batch_size / (mean_latency / 1000.0)), 2)

    # Base process memory in MB
    base_mem = 450.0 + (batch_size * 18.5)
    
    # DataLoader num_workers replication defect simulation (#13246)
    # When num_workers > 0 and using list-based datasets, memory replicates across child processes
    replicated = False
    if num_workers > 0:
        replicated = True
        total_memory = round(base_mem + (num_workers * base_mem * 0.85), 2)
    else:
        total_memory = round(base_mem, 2)

    result = {
        "workload_name": workload_name,
        "backend": backend,
        "batch_size": batch_size,
        "num_workers": num_workers,
        "mean_latency_ms": mean_latency,
        "p95_latency_ms": p95_latency,
        "throughput_samples_per_sec": throughput,
        "peak_memory_mb": total_memory,
        "replicated_memory_detected": replicated,
        "hardware_acceleration_efficiency": round(100.0 * (base_latencies["cpu"] / max(0.1, mean_latency)), 2)
    }

    if db:
        record = BenchmarkRecord(
            workload_name=workload_name,
            backend=backend,
            batch_size=batch_size,
            mean_latency_ms=mean_latency,
            p95_latency_ms=p95_latency,
            throughput_samples_per_sec=throughput,
            peak_memory_mb=total_memory,
            replicated_memory_detected=replicated,
            executed_by=actor
        )
        db.add(record)
        audit = AuditLogRecord(
            action="BENCHMARK_EXECUTION",
            actor=actor,
            details=f"Ran workload '{workload_name}' on {backend} with batch_size={batch_size}, num_workers={num_workers}."
        )
        db.add(audit)
        db.commit()
        db.refresh(record)
        result["id"] = record.id

    return result
