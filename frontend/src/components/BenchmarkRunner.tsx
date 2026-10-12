import React, { useState } from 'react';
import { runBenchmark, BenchmarkResult } from '../api/client';

export const BenchmarkRunner: React.FC = () => {
  const [workloadName, setWorkloadName] = useState('Transformer-Attention-Layer');
  const [backend, setBackend] = useState('mps');
  const [batchSize, setBatchSize] = useState(32);
  const [numWorkers, setNumWorkers] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BenchmarkResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await runBenchmark(workloadName, backend, batchSize, numWorkers);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Benchmark execution failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Dynamic Execution Benchmark Runner</h2>
      <p style={{ color: 'var(--text-muted)' }}>
        Simulates runtime latency distributions, throughput scaling, and DataLoader worker memory overhead.
      </p>

      <form onSubmit={handleExecute} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Workload Profile</label>
          <input
            type="text"
            value={workloadName}
            onChange={(e) => setWorkloadName(e.target.value)}
            style={{ width: '100%' }}
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Hardware Backend</label>
          <select value={backend} onChange={(e) => setBackend(e.target.value)} style={{ width: '100%' }}>
            <option value="mps">Apple MPS</option>
            <option value="vulkan">Vulkan Compute</option>
            <option value="cpu">Host CPU</option>
            <option value="cuda">NVIDIA CUDA</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Batch Size</label>
          <input
            type="number"
            min={1}
            max={512}
            value={batchSize}
            onChange={(e) => setBatchSize(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>
            DataLoader Workers (num_workers)
          </label>
          <input
            type="number"
            min={0}
            max={32}
            value={numWorkers}
            onChange={(e) => setNumWorkers(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button type="submit" disabled={loading} style={{ width: '100%', height: '38px' }}>
            {loading ? 'Evaluating...' : 'Run Simulation'}
          </button>
        </div>
      </form>

      {error && <div style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error}</div>}

      {result && (
        <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
          <h3 style={{ marginTop: 0 }}>Execution Telemetry</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Mean Latency</span>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{result.mean_latency_ms} ms</div>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>P95 Latency</span>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{result.p95_latency_ms} ms</div>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Throughput</span>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--accent)' }}>
                {result.throughput_samples_per_sec} <span style={{ fontSize: '0.9rem' }}>samples/s</span>
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Peak Memory</span>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: result.replicated_memory_detected ? 'var(--danger)' : 'var(--success)' }}>
                {result.peak_memory_mb} MB
              </div>
            </div>
          </div>

          {result.replicated_memory_detected && (
            <div style={{ marginTop: '1rem', padding: '0.75rem', borderRadius: '0.375rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5' }}>
              <strong>Memory Replication Warning (#13246):</strong> Child worker processes have cloned dataset memory in user space. Mitigate by pinning tensors directly into shared memory.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
