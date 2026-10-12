import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// Mock the API client
vi.mock('./api/client', () => ({
  fetchOperators: vi.fn().mockResolvedValue([
    {
      id: 1,
      op_name: 'aten::max_pool3d_with_indices',
      category: 'pooling',
      mps_status: 'supported',
      vulkan_status: 'missing',
      cpu_status: 'supported',
      cuda_status: 'supported',
      notes: 'Test op'
    }
  ]),
  fetchCoverage: vi.fn().mockResolvedValue({
    backend: 'mps',
    total_operators: 1,
    supported: 1,
    fallback: 0,
    missing: 0,
    coverage_rate: 100.0
  }),
  runBenchmark: vi.fn(),
  createWorkloadPlan: vi.fn(),
  fetchAdvisory: vi.fn()
}));

describe('Orbit Station Dashboard', () => {
  it('renders application title and author subtitle', async () => {
    render(<App />);
    expect(await screen.findByRole('heading', { level: 1, name: /Orbit Station/i })).toBeInTheDocument();
    expect(screen.getByText(/Ryan Vo \| AI & Machine Learning/i)).toBeInTheDocument();
  });

  it('displays the operator coverage matrix', async () => {
    render(<App />);
    expect(await screen.findByText(/Operator Coverage Matrix/i)).toBeInTheDocument();
    expect(screen.getByText(/aten::max_pool3d_with_indices/i)).toBeInTheDocument();
  });

  it('renders benchmark runner controls', async () => {
    render(<App />);
    expect(await screen.findByText(/Dynamic Execution Benchmark Runner/i)).toBeInTheDocument();
    expect(screen.getByText(/Run Simulation/i)).toBeInTheDocument();
  });
});
