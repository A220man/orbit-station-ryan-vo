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
    assert data["version"] == "1.1.0"

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

import json
from unittest.mock import patch, MagicMock

def test_export_operators_json():
    res = client.get("/api/operators/export?format=json")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 15
    assert data[0]["op_name"] == "aten::max_pool3d_with_indices"

def test_export_operators_csv():
    res = client.get("/api/operators/export?format=csv")
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    content = res.text
    assert "op_name,category" in content
    assert "aten::max_pool3d_with_indices" in content

def test_export_benchmarks_json():
    # First create a benchmark
    client.post("/api/benchmarks/run", json={
        "workload_name": "Export-Test",
        "backend": "cpu",
        "batch_size": 16,
        "num_workers": 0
    })
    res = client.get("/api/benchmarks/export?format=json&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["workload_name"] == "Export-Test"

def test_export_benchmarks_csv():
    res = client.get("/api/benchmarks/export?format=csv&limit=5")
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    content = res.text
    assert "workload_name,backend" in content

def test_export_plans_json():
    # First create a plan
    client.post("/api/plans/create", json={
        "title": "Export-Plan",
        "target_backend": "mps",
        "requested_ops": ["aten::angle"]
    })
    res = client.get("/api/plans/export?format=json&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "Export-Plan"

def test_export_plans_csv():
    res = client.get("/api/plans/export?format=csv&limit=5")
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    content = res.text
    assert "title,target_backend" in content

def test_full_workflow_operator_to_advisory():
    """
    End-to-end integration test crossing the real HTTP boundary:
    1. List operators
    2. Get MPS coverage
    3. Create workload plan with mixed supported/missing ops
    4. Run benchmark simulation
    5. Request deterministic advisory
    6. Export all artifacts
    """
    # Step 1: List operators
    ops_res = client.get("/api/operators")
    assert ops_res.status_code == 200
    operators = ops_res.json()
    assert len(operators) >= 15

    # Step 2: Get backend coverage
    cov_res = client.get("/api/coverage/mps")
    assert cov_res.status_code == 200
    coverage = cov_res.json()
    assert coverage["backend"] == "mps"
    assert coverage["coverage_rate"] > 50.0

    # Step 3: Create workload plan
    requested_ops = [
        "aten::max_pool3d_with_indices",  # supported on MPS
        "aten::_standard_gamma",          # missing on MPS
        "aten::angle",                    # supported on MPS
        "aten::unique_dim"                # missing on MPS
    ]
    plan_res = client.post("/api/plans/create", json={
        "title": "Integration-Test-Plan",
        "target_backend": "mps",
        "requested_ops": requested_ops
    })
    assert plan_res.status_code == 200
    plan = plan_res.json()
    plan_id = plan["id"]
    assert plan["total_ops"] == 4
    assert plan["supported_ops_count"] == 2
    assert plan["fallback_ops_count"] == 2
    assert plan["coverage_score"] == 50.0

    # Step 4: Run benchmark
    bench_res = client.post("/api/benchmarks/run", json={
        "workload_name": "Integration-Benchmark",
        "backend": "mps",
        "batch_size": 32,
        "num_workers": 4
    })
    assert bench_res.status_code == 200
    benchmark = bench_res.json()
    assert benchmark["workload_name"] == "Integration-Benchmark"
    assert benchmark["backend"] == "mps"
    assert benchmark["replicated_memory_detected"] is True
    assert benchmark["peak_memory_mb"] > 1000

    # Step 5: Request deterministic advisory (offline mode)
    adv_res = client.post("/api/advisory/analyze", json={"plan_id": plan_id})
    assert adv_res.status_code == 200
    advisory = adv_res.json()
    assert advisory["status"] == "deterministic_offline"
    assert "No external inference call was made" in advisory["disclaimer"]
    assert len(advisory["findings"]) >= 2

    # Step 6: Export all artifacts
    ops_export = client.get("/api/operators/export?format=json")
    assert ops_export.status_code == 200
    
    bench_export = client.get("/api/benchmarks/export?format=json&limit=5")
    assert bench_export.status_code == 200
    
    plans_export = client.get("/api/plans/export?format=json&limit=5")
    assert plans_export.status_code == 200

@patch("httpx.Client")
def test_llm_advisory_with_openai_compatible_mock(mock_client_class):
    """Test LLM advisory path with mocked OpenAI-compatible provider."""
    # Create a plan first
    plan_res = client.post("/api/plans/create", json={
        "title": "LLM-Test-Plan",
        "target_backend": "vulkan",
        "requested_ops": ["aten::scaled_dot_product_attention", "aten::convolution_2d"]
    })
    plan_id = plan_res.json()["id"]

    # Mock successful OpenAI-compatible response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "1. Optimize memory layout for Vulkan tensor cores\n2. Fuse attention + convolution kernels\n3. Profile GPU utilization with nsys"
            }
        }]
    }
    mock_response.raise_for_status = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    # Need to set LLM_API_KEY for this test
    from app.core.config import settings
    original_key = settings.llm_api_key
    settings.llm_api_key = "test-key-placeholder-do-not-use-real-credentials"
    settings.llm_provider = "openai-compatible"
    try:
        adv_res = client.post("/api/advisory/analyze", json={
            "plan_id": plan_id,
            "custom_prompt": "Focus on memory optimization"
        })
        assert adv_res.status_code == 200
        advisory = adv_res.json()
        assert advisory["status"] == "success"
        assert advisory["provider"] == "openai-compatible"
        assert len(advisory["findings"]) == 3
        assert "Optimize memory layout" in advisory["findings"][0]
        mock_client.post.assert_called_once()
    finally:
        settings.llm_api_key = original_key

@patch("httpx.Client")
def test_llm_advisory_anthropic_mock(mock_client_class):
    """Test LLM advisory path with mocked Anthropic provider."""
    plan_res = client.post("/api/plans/create", json={
        "title": "Anthropic-Test",
        "target_backend": "cuda",
        "requested_ops": ["aten::convolution_2d"]
    })
    plan_id = plan_res.json()["id"]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [{"text": "1. Use tensor cores\n2. Enable FP8\n3. Batch inference"}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    from app.core.config import settings
    original_key = settings.llm_api_key
    original_provider = settings.llm_provider
    settings.llm_api_key = "test-key-placeholder-do-not-use-real-credentials"
    settings.llm_provider = "anthropic"
    try:
        adv_res = client.post("/api/advisory/analyze", json={"plan_id": plan_id})
        assert adv_res.status_code == 200
        advisory = adv_res.json()
        assert advisory["status"] == "success"
        assert advisory["provider"] == "anthropic"
        assert len(advisory["findings"]) == 3
    finally:
        settings.llm_api_key = original_key
        settings.llm_provider = original_provider

@patch("httpx.Client")
def test_llm_advisory_gemini_mock(mock_client_class):
    """Test LLM advisory path with mocked Gemini provider."""
    plan_res = client.post("/api/plans/create", json={
        "title": "Gemini-Test",
        "target_backend": "cpu",
        "requested_ops": ["aten::angle"]
    })
    plan_id = plan_res.json()["id"]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "1. Vectorize CPU ops\n2. Use MKL\n3. Parallelize batches"}]}
        }]
    }
    mock_response.raise_for_status = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    from app.core.config import settings
    original_key = settings.llm_api_key
    original_provider = settings.llm_provider
    settings.llm_api_key = "test-key-placeholder-do-not-use-real-credentials"
    settings.llm_provider = "gemini"
    try:
        adv_res = client.post("/api/advisory/analyze", json={"plan_id": plan_id})
        assert adv_res.status_code == 200
        advisory = adv_res.json()
        assert advisory["status"] == "success"
        assert advisory["provider"] == "gemini"
        assert len(advisory["findings"]) == 3
    finally:
        settings.llm_api_key = original_key
        settings.llm_provider = original_provider

@patch("httpx.Client")
def test_advisory_error_handling_on_provider_failure(mock_client_class):
    """Test graceful fallback when LLM provider returns error."""
    plan_res = client.post("/api/plans/create", json={
        "title": "Error-Test",
        "target_backend": "mps",
        "requested_ops": ["aten::angle"]
    })
    plan_id = plan_res.json()["id"]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"
    import httpx
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "429 Rate limit", request=MagicMock(), response=mock_response
    )
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    from app.core.config import settings
    original_key = settings.llm_api_key
    settings.llm_api_key = "test-key-placeholder-do-not-use-real-credentials"
    settings.llm_provider = "openai-compatible"
    try:
        adv_res = client.post("/api/advisory/analyze", json={"plan_id": plan_id})
        assert adv_res.status_code == 200
        advisory = adv_res.json()
        assert advisory["status"] == "provider_error"
        assert "external service failed" in advisory["disclaimer"].lower()
    finally:
        settings.llm_api_key = original_key

