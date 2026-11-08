import React, { useState, useEffect } from 'react';
import { fetchBenchmarkHistory, BenchmarkResult, exportBenchmarks, downloadBlob } from '../api/client';

export const BenchmarkHistory: React.FC = () => {
  const [history, setHistory] = useState<BenchmarkResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(20);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchBenchmarkHistory(limit);
      setHistory(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load benchmark history';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [limit]);

  const getBackendColor = (backend: string) => {
    switch (backend) {
      case 'mps':
        return 'var(--accent)';
      case 'cuda':
        return 'var(--success)';
      case 'vulkan':
        return 'var(--warning)';
      case 'cpu':
      default:
        return 'var(--text-muted)';
    }
  };

  const formatNumber = (num: number) => num.toLocaleString(undefined, { maximumFractionDigits: 2 });

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Benchmark History</h2>
          <p style={{ color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
            Past benchmark simulations for comparison and trend analysis
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Limit:
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              style={{ marginLeft: '0.5rem', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border-color)', background: '#1e293b', color: '#f8fafc' }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
          <button
            onClick={loadHistory}
            disabled={loading}
            style={{ background: '#334155', color: '#f8fafc', border: 'none', padding: '0.5rem 1rem', borderRadius: '0.375rem', cursor: loading ? 'not-allowed' : 'pointer', fontSize: '0.85rem', opacity: loading ? 0.6 : 1 }}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ color: 'var(--danger)', marginBottom: '1rem', padding: '0.75rem', background: '#3d1a1a', borderRadius: '0.375rem', border: '1px solid var(--danger)' }}>
          {error}
        </div>
      )}

      {loading && history.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
          Loading benchmark history...
        </div>
      )}

      {!loading && history.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
          No benchmark history found. Run a simulation from the Benchmark Runner to populate history.
        </div>
      )}

      {!loading && history.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-color)', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem' }}>#</th>
                <th style={{ padding: '0.75rem' }}>Workload</th>
                <th style={{ padding: '0.75rem' }}>
                  <span style={{ color: 'var(--accent)' }}>●</span> Backend
                </th>
                <th style={{ padding: '0.75rem' }}>Batch</th>
                <th style={{ padding: '0.75rem' }}>Workers</th>
                <th style={{ padding: '0.75rem' }}>Latency (ms)</th>
                <th style={{ padding: '0.75rem' }}>P95 (ms)</th>
                <th style={{ padding: '0.75rem' }}>Throughput (samples/s)</th>
                <th style={{ padding: '0.75rem' }}>Peak Memory (MB)</th>
                <th style={{ padding: '0.75rem' }}>Replication</th>
                <th style={{ padding: '0.75rem' }}>Efficiency (%)</th>
              </tr>
            </thead>
            <tbody>
              {history.map((bench, idx) => (
                <tr key={bench.id ?? idx} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.15s' }}>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    {bench.id ?? idx + 1}
                  </td>
                  <td style={{ padding: '0.75rem', fontWeight: 500 }}>{bench.workload_name}</td>
                  <td style={{ padding: '0.75rem' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '0.25rem',
                        background: `${getBackendColor(bench.backend)}22`,
                        color: getBackendColor(bench.backend),
                        fontWeight: 600,
                        fontSize: '0.8rem',
                        textTransform: 'uppercase'
                      }}
                    >
                      {bench.backend}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>{bench.batch_size}</td>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>{bench.num_workers}</td>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace', fontWeight: 500 }}>{formatNumber(bench.mean_latency_ms)}</td>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>{formatNumber(bench.p95_latency_ms)}</td>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace', fontWeight: 500, color: 'var(--success)' }}>{formatNumber(bench.throughput_samples_per_sec)}</td>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>
                    {formatNumber(bench.peak_memory_mb)}
                    {bench.replicated_memory_detected && (
                      <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', color: 'var(--warning)', fontWeight: 600, background: '#3d351a', padding: '0.1rem 0.35rem', borderRadius: '0.2rem' }}>
                        REPLICATED
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                    {bench.replicated_memory_detected ? (
                      <span style={{ color: 'var(--danger)' }}>⚠ Yes</span>
                    ) : (
                      <span style={{ color: 'var(--success)' }}>✓ No</span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace', fontWeight: 500 }}>
                    {bench.hardware_acceleration_efficiency}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && history.length > 0 && (
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', justifyContent: 'flex-end' }}>
          <button
            onClick={async () => {
              try {
                const blob = await exportBenchmarks('json');
                downloadBlob(blob, 'benchmark_history.json');
              } catch (err) {
                console.error('Export failed:', err);
              }
            }}
            style={{ background: '#334155', color: '#f8fafc', border: 'none', padding: '0.5rem 1rem', borderRadius: '0.375rem', cursor: 'pointer', fontSize: '0.85rem' }}
          >
            Export JSON
          </button>
          <button
            onClick={async () => {
              try {
                const blob = await exportBenchmarks('csv');
                downloadBlob(blob, 'benchmark_history.csv');
              } catch (err) {
                console.error('Export failed:', err);
              }
            }}
            style={{ background: '#334155', color: '#f8fafc', border: 'none', padding: '0.5rem 1rem', borderRadius: '0.375rem', cursor: 'pointer', fontSize: '0.85rem' }}
          >
            Export CSV
          </button>
        </div>
      )}
    </div>
  );
};
