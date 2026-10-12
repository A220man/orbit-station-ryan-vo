from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import OperatorRecord

DEFAULT_OPERATORS: List[Dict[str, Any]] = [
    {
        "op_name": "aten::max_pool3d_with_indices",
        "category": "pooling",
        "mps_status": "supported",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "3D volumetric pooling with index tracking for gradient backpropagation."
    },
    {
        "op_name": "aten::_linalg_solve_ex.result",
        "category": "linalg",
        "mps_status": "supported",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Direct linear system solver with info status code."
    },
    {
        "op_name": "aten::_standard_gamma",
        "category": "distribution",
        "mps_status": "missing",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Standard gamma random variate generator."
    },
    {
        "op_name": "aten::_upsample_bicubic2d_aa.out",
        "category": "vision",
        "mps_status": "supported",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Bicubic image spatial resampler with anti-aliasing filter."
    },
    {
        "op_name": "aten::linalg_qr.out",
        "category": "linalg",
        "mps_status": "missing",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "QR matrix decomposition with full/reduced mode options."
    },
    {
        "op_name": "aten::angle",
        "category": "math",
        "mps_status": "supported",
        "vulkan_status": "supported",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Element-wise complex argument calculation."
    },
    {
        "op_name": "aten::grid_sampler_3d",
        "category": "vision",
        "mps_status": "supported",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "3D volumetric grid sampling for spatial transformer architectures."
    },
    {
        "op_name": "aten::vdot",
        "category": "linalg",
        "mps_status": "supported",
        "vulkan_status": "supported",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Vector dot product over 1D tensors with conjugation."
    },
    {
        "op_name": "aten::linalg_cholesky_ex.L",
        "category": "linalg",
        "mps_status": "supported",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Cholesky factorization with boolean status verification."
    },
    {
        "op_name": "aten::_linalg_det.result",
        "category": "linalg",
        "mps_status": "supported",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Batch determinant calculation via LU factorization."
    },
    {
        "op_name": "aten::unique_dim",
        "category": "transform",
        "mps_status": "missing",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Unique element extraction across a specified dimension."
    },
    {
        "op_name": "aten::linalg_lu_solve.out",
        "category": "linalg",
        "mps_status": "supported",
        "vulkan_status": "missing",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Linear equations solution using LU factors."
    },
    {
        "op_name": "aten::native_dropout",
        "category": "regularization",
        "mps_status": "supported",
        "vulkan_status": "supported",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Fused pseudorandom dropout mask generation and element-wise multiplication."
    },
    {
        "op_name": "aten::convolution_2d",
        "category": "nn",
        "mps_status": "supported",
        "vulkan_status": "supported",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Standard 2D spatial convolution with dilation and grouping."
    },
    {
        "op_name": "aten::scaled_dot_product_attention",
        "category": "transformer",
        "mps_status": "supported",
        "vulkan_status": "fallback",
        "cpu_status": "supported",
        "cuda_status": "supported",
        "notes": "Flash/Fused multi-head attention kernel with causal mask support."
    }
]

def seed_operator_catalog(db: Session):
    existing_count = db.query(OperatorRecord).count()
    if existing_count == 0:
        for op_data in DEFAULT_OPERATORS:
            record = OperatorRecord(**op_data)
            db.add(record)
        db.commit()

def calculate_backend_coverage(db: Session, backend: str) -> Dict[str, Any]:
    records = db.query(OperatorRecord).all()
    total = len(records)
    if total == 0:
        return {"backend": backend, "coverage_rate": 0.0, "supported": 0, "fallback": 0, "missing": 0}

    supported_count = 0
    fallback_count = 0
    missing_count = 0

    col_map = {
        "mps": "mps_status",
        "vulkan": "vulkan_status",
        "cpu": "cpu_status",
        "cuda": "cuda_status"
    }
    col_attr = col_map.get(backend.lower(), "cpu_status")

    for r in records:
        status_val = getattr(r, col_attr)
        if status_val == "supported":
            supported_count += 1
        elif status_val == "fallback":
            fallback_count += 1
        else:
            missing_count += 1

    rate = round((supported_count + (fallback_count * 0.5)) / total * 100.0, 2)
    return {
        "backend": backend,
        "total_operators": total,
        "supported": supported_count,
        "fallback": fallback_count,
        "missing": missing_count,
        "coverage_rate": rate
    }
