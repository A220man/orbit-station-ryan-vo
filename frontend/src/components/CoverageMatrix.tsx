import React, { useState } from 'react';
import { OperatorResponse, CoverageResponse } from '../api/client';

interface Props {
  operators: OperatorResponse[];
  coverage: CoverageResponse | null;
  selectedBackend: string;
  onSelectBackend: (backend: string) => void;
}

export const CoverageMatrix: React.FC<Props> = ({
  operators,
  coverage,
  selectedBackend,
  onSelectBackend,
}) => {
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  const filtered = operators.filter((op) => {
    const matchesSearch = op.op_name.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = categoryFilter ? op.category === categoryFilter : true;
    return matchesSearch && matchesCategory;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'supported':
        return <span className="badge badge-supported">Supported</span>;
      case 'fallback':
        return <span className="badge badge-fallback">Host Fallback</span>;
      default:
        return <span className="badge badge-missing">Missing</span>;
    }
  };

  const categories = Array.from(new Set(operators.map((o) => o.category)));

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Operator Coverage Matrix</h2>
          <p style={{ color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
            Empirical PyTorch operator availability across hardware backends
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Target Backend:</label>
          <select value={selectedBackend} onChange={(e) => onSelectBackend(e.target.value)}>
            <option value="mps">Apple Silicon (MPS)</option>
            <option value="vulkan">Vulkan Agnostic</option>
            <option value="cpu">Host CPU</option>
            <option value="cuda">NVIDIA CUDA</option>
          </select>
        </div>
      </div>

      {coverage && (
        <div style={{ display: 'flex', gap: '1.5rem', background: '#0f172a', padding: '1rem', borderRadius: '0.5rem', marginBottom: '1.5rem' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Coverage Rate</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent)' }}>{coverage.coverage_rate}%</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Supported</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--success)' }}>{coverage.supported}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Fallback</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--warning)' }}>{coverage.fallback}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Missing</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--danger)' }}>{coverage.missing}</div>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <input
          type="text"
          placeholder="Filter by op name (e.g. linalg, max_pool)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1 }}
        />
        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Operator Name</th>
              <th>Category</th>
              <th>MPS Status</th>
              <th>Vulkan Status</th>
              <th>CPU Status</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((op) => (
              <tr key={op.id}>
                <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{op.op_name}</td>
                <td><span className="badge" style={{ background: '#334155' }}>{op.category}</span></td>
                <td>{getStatusBadge(op.mps_status)}</td>
                <td>{getStatusBadge(op.vulkan_status)}</td>
                <td>{getStatusBadge(op.cpu_status)}</td>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{op.notes}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No operators match your filter criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
