import React, { useState } from 'react';
import { createWorkloadPlan, fetchAdvisory, WorkloadPlan, AdvisoryResponse } from '../api/client';

export const WorkloadPlannerView: React.FC = () => {
  const [title, setTitle] = useState('ResNet50-Vulkan-Port');
  const [targetBackend, setTargetBackend] = useState('vulkan');
  const [opsInput, setOpsInput] = useState('aten::convolution_2d, aten::native_dropout, aten::scaled_dot_product_attention');
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<WorkloadPlan | null>(null);
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null);
  const [advisoryLoading, setAdvisoryLoading] = useState(false);

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAdvisory(null);
    try {
      const ops = opsInput.split(',').map((s) => s.trim()).filter(Boolean);
      const data = await createWorkloadPlan(title, targetBackend, ops);
      setPlan(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFetchAdvisory = async () => {
    if (!plan) return;
    setAdvisoryLoading(true);
    try {
      const adv = await fetchAdvisory(plan.id);
      setAdvisory(adv);
    } catch (err) {
      console.error(err);
    } finally {
      setAdvisoryLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Workload Graph & Execution Planner</h2>
      <p style={{ color: 'var(--text-muted)' }}>
        Decomposes dynamic computation graphs, flags missing operations, and plans host CPU fallback partitions.
      </p>

      <form onSubmit={handleCreatePlan} style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 200px', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Plan Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{ width: '100%' }}
              required
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Target Backend</label>
            <select value={targetBackend} onChange={(e) => setTargetBackend(e.target.value)} style={{ width: '100%' }}>
              <option value="mps">Apple MPS</option>
              <option value="vulkan">Vulkan Compute</option>
              <option value="cpu">Host CPU</option>
              <option value="cuda">NVIDIA CUDA</option>
            </select>
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Requested Operators (comma-separated)</label>
          <input
            type="text"
            value={opsInput}
            onChange={(e) => setOpsInput(e.target.value)}
            style={{ width: '100%' }}
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Synthesizing...' : 'Synthesize Execution Graph'}
        </button>
      </form>

      {plan && (
        <div style={{ background: '#0f172a', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ margin: 0 }}>Plan: {plan.title}</h3>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Target: {plan.target_backend.toUpperCase()} | Coverage Score: <strong>{plan.coverage_score}%</strong>
              </span>
            </div>
            <button onClick={handleFetchAdvisory} disabled={advisoryLoading} style={{ background: '#334155', color: '#f8fafc' }}>
              {advisoryLoading ? 'Evaluating...' : 'Get Opt-In Advisory'}
            </button>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <h4 style={{ margin: '0.5rem 0', color: 'var(--success)' }}>Native Execution Nodes ({plan.supported_nodes.length})</h4>
            {plan.supported_nodes.length === 0 ? (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No native nodes mapped.</span>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {plan.supported_nodes.map((node, i) => (
                  <span key={i} className="badge badge-supported" style={{ fontFamily: 'monospace' }}>
                    {node.op}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div>
            <h4 style={{ margin: '0.5rem 0', color: 'var(--warning)' }}>Synthesized Host Fallback Nodes ({plan.fallbacks.length})</h4>
            {plan.fallbacks.length === 0 ? (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No fallbacks required. Fully accelerated.</span>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {plan.fallbacks.map((node, i) => (
                  <span key={i} className="badge badge-fallback" style={{ fontFamily: 'monospace' }}>
                    {node.op} &rarr; Host CPU
                  </span>
                ))}
              </div>
            )}
          </div>

          {advisory && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', borderRadius: '0.375rem', background: '#1e293b', border: '1px solid var(--accent)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <strong style={{ color: 'var(--accent)' }}>{advisory.advisory_label}</strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Provider: {advisory.provider} ({advisory.model})</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                {advisory.findings.map((finding, idx) => (
                  <li key={idx} style={{ marginBottom: '0.25rem', fontSize: '0.9rem' }}>{finding}</li>
                ))}
              </ul>
              <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                {advisory.disclaimer}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
