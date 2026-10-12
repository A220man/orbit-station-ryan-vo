import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"

def test_list_operators_endpoint():
    res = client.get("/api/operators")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 15

def test_filter_operators_by_category():
    res = client.get("/api/operators?category=linalg")
    assert res.status_code == 200
    data = res.json()
    assert all(item["category"] == "linalg" for item in data)

def test_get_backend_coverage_endpoint():
    res = client.get("/api/coverage/mps")
    assert res.status_code == 200
    data = res.json()
    assert data["backend"] == "mps"
    assert "coverage_rate" in data

def test_run_benchmark_endpoint():
    payload = {
        "workload_name": "ResNet-50",
        "backend": "mps",
        "batch_size": 32,
        "num_workers": 2
    }
    res = client.post("/api/benchmarks/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["workload_name"] == "ResNet-50"
    assert "mean_latency_ms" in data
    assert data["replicated_memory_detected"] is True

def test_create_workload_plan_endpoint():
    payload = {
        "title": "BERT-Encoder",
        "target_backend": "vulkan",
        "requested_ops": [
            "aten::scaled_dot_product_attention",
            "aten::native_dropout"
        ]
    }
    res = client.post("/api/plans/create", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "BERT-Encoder"
    assert "coverage_score" in data
    assert "id" in data

def test_advisory_analysis_endpoint():
    # First create plan
    create_res = client.post("/api/plans/create", json={
        "title": "Advisory-Target-Plan",
        "target_backend": "mps",
        "requested_ops": ["aten::_standard_gamma", "aten::angle"]
    })
    plan_id = create_res.json()["id"]

    adv_res = client.post("/api/advisory/analyze", json={"plan_id": plan_id})
    assert adv_res.status_code == 200
    adv_data = adv_res.json()
    assert adv_data["status"] == "deterministic_offline"
    assert len(adv_data["findings"]) > 0

def test_add_operator_endpoint():
    import uuid
    # Register a new custom operator with unique name
    unique_id = uuid.uuid4().hex[:8]
    new_op = {
        "op_name": f"aten::custom_op_test_{unique_id}",
        "category": "experimental",
        "mps_status": "missing",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Experimental kernel."
    }
    res = client.post("/api/operators", json=new_op)
    assert res.status_code in [200, 201]
    data = res.json()
    assert data["op_name"] == new_op["op_name"]

def test_malformed_benchmark_input():
    payload = {
        "workload_name": "Invalid",
        "batch_size": -1 # invalid
    }
    res = client.post("/api/benchmarks/run", json=payload)
    assert res.status_code == 422
