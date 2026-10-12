export interface OperatorResponse {
  id: number;
  op_name: string;
  category: string;
  mps_status: 'supported' | 'missing' | 'fallback';
  vulkan_status: 'supported' | 'missing' | 'fallback';
  cpu_status: 'supported' | 'missing' | 'fallback';
  cuda_status: 'supported' | 'missing' | 'fallback';
  notes?: string;
}

export interface CoverageResponse {
  backend: string;
  total_operators: number;
  supported: number;
  fallback: number;
  missing: number;
  coverage_rate: number;
}

export interface BenchmarkResult {
  id?: number;
  workload_name: string;
  backend: string;
  batch_size: number;
  num_workers: number;
  mean_latency_ms: number;
  p95_latency_ms: number;
  throughput_samples_per_sec: number;
  peak_memory_mb: number;
  replicated_memory_detected: boolean;
  hardware_acceleration_efficiency: number;
}

export interface WorkloadPlan {
  id: number;
  title: string;
  target_backend: string;
  total_ops: number;
  supported_ops_count: number;
  fallback_ops_count: number;
  coverage_score: number;
  supported_nodes: Array<{ op: string; target: string }>;
  fallbacks: Array<{ op: string; target: string; notes?: string; reason?: string }>;
  is_hardware_accelerated: boolean;
}

export interface AdvisoryResponse {
  status: string;
  advisory_label: string;
  provider: string;
  model: string;
  findings: string[];
  disclaimer: string;
}

const API_BASE = '/api';

export async function fetchOperators(category?: string, search?: string): Promise<OperatorResponse[]> {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (search) params.append('search', search);
  const res = await fetch(`${API_BASE}/operators?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch operators');
  return res.json();
}

export async function fetchCoverage(backend: string): Promise<CoverageResponse> {
  const res = await fetch(`${API_BASE}/coverage/${backend}`);
  if (!res.ok) throw new Error(`Failed to fetch coverage for ${backend}`);
  return res.json();
}

export async function runBenchmark(
  workload_name: string,
  backend: string,
  batch_size: number,
  num_workers: number
): Promise<BenchmarkResult> {
  const res = await fetch(`${API_BASE}/benchmarks/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workload_name, backend, batch_size, num_workers }),
  });
  if (!res.ok) throw new Error('Failed to execute benchmark');
  return res.json();
}

export async function createWorkloadPlan(
  title: string,
  target_backend: string,
  requested_ops: string[]
): Promise<WorkloadPlan> {
  const res = await fetch(`${API_BASE}/plans/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, target_backend, requested_ops }),
  });
  if (!res.ok) throw new Error('Failed to create workload plan');
  return res.json();
}

export async function fetchAdvisory(plan_id: number): Promise<AdvisoryResponse> {
  const res = await fetch(`${API_BASE}/advisory/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan_id }),
  });
  if (!res.ok) throw new Error('Failed to fetch advisory report');
  return res.json();
}
