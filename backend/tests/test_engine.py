import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base, OperatorRecord
from app.services.operator_catalog import seed_operator_catalog, calculate_backend_coverage
from app.services.benchmark_engine import simulate_workload_execution
from app.services.workload_planner import plan_workload_execution
from app.services.llm_advisory import generate_fallback_analysis_advisory

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    try:
        seed_operator_catalog(db)
        yield db
    finally:
        db.close()

def test_operator_catalog_seeding(test_db):
    ops = test_db.query(OperatorRecord).all()
    assert len(ops) >= 15
    op_names = [o.op_name for o in ops]
    assert "aten::max_pool3d_with_indices" in op_names
    assert "aten::_linalg_solve_ex.result" in op_names

def test_mps_backend_coverage(test_db):
    cov = calculate_backend_coverage(test_db, "mps")
    assert cov["backend"] == "mps"
    assert cov["total_operators"] >= 15
    assert cov["supported"] > 0
    assert cov["coverage_rate"] > 50.0

def test_vulkan_backend_coverage(test_db):
    cov = calculate_backend_coverage(test_db, "vulkan")
    assert cov["backend"] == "vulkan"
    assert cov["total_operators"] >= 15
    assert cov["supported"] >= 2
    assert cov["coverage_rate"] < 50.0

def test_benchmark_simulation_scaling(test_db):
    res_b16 = simulate_workload_execution("Transformer-Block", "mps", batch_size=16, num_workers=0, db=test_db)
    res_b64 = simulate_workload_execution("Transformer-Block", "mps", batch_size=64, num_workers=0, db=test_db)
    
    assert res_b64["throughput_samples_per_sec"] > res_b16["throughput_samples_per_sec"]
    assert res_b64["peak_memory_mb"] > res_b16["peak_memory_mb"]
    assert not res_b16["replicated_memory_detected"]

def test_dataloader_worker_memory_replication(test_db):
    # Tests simulation of DataLoader num_workers issue #13246
    res_w0 = simulate_workload_execution("CV-Dataset", "cpu", batch_size=32, num_workers=0, db=test_db)
    res_w8 = simulate_workload_execution("CV-Dataset", "cpu", batch_size=32, num_workers=8, db=test_db)
    
    assert res_w8["replicated_memory_detected"] is True
    assert res_w8["peak_memory_mb"] > res_w0["peak_memory_mb"] * 3.0

def test_workload_planner_with_fallbacks(test_db):
    requested = [
        "aten::max_pool3d_with_indices",
        "aten::linalg_qr.out", # missing on MPS
        "aten::custom_hypothetical_op" # missing everywhere
    ]
    plan = plan_workload_execution("Test-Model", "mps", requested, db=test_db)
    assert plan["total_ops"] == 3
    assert plan["supported_ops_count"] == 1
    assert plan["fallback_ops_count"] == 2
    assert plan["coverage_score"] == 33.33

def test_deterministic_llm_advisory_offline():
    workload = {
        "title": "Vision-Model",
        "target_backend": "mps",
        "coverage_score": 60.0,
        "fallbacks": [{"op": "aten::linalg_qr.out", "target": "cpu"}]
    }
    adv = generate_fallback_analysis_advisory(workload)
    assert adv["status"] == "deterministic_offline"
    assert "findings" in adv
    assert len(adv["findings"]) >= 2
    assert "No external inference call was made" in adv["disclaimer"]
