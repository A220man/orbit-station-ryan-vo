import React, { useEffect, useState } from 'react';
import { CoverageMatrix } from './components/CoverageMatrix';
import { BenchmarkRunner } from './components/BenchmarkRunner';
import { WorkloadPlannerView } from './components/WorkloadPlannerView';
import { fetchOperators, fetchCoverage, OperatorResponse, CoverageResponse } from './api/client';

export const App: React.FC = () => {
  const [operators, setOperators] = useState<OperatorResponse[]>([]);
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const [selectedBackend, setSelectedBackend] = useState('mps');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (backend: string) => {
    try {
      setLoading(true);
      setError(null);
      const [opsData, covData] = await Promise.all([
        fetchOperators(),
        fetchCoverage(backend),
      ]);
      setOperators(opsData);
      setCoverage(covData);
    } catch (err: any) {
      setError(err.message || 'Failed to load system data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedBackend);
  }, [selectedBackend]);

  return (
    <div className="container">
      <header>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.75rem' }}>Orbit Station</h1>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)' }}>
              Ryan Vo | AI & Machine Learning &bull; PyTorch Dynamic Neural Network Acceleration Platform
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span className="badge badge-supported">Demo Mode: Active</span>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              v1.1.0 &bull; OIDC Ready
            </div>
          </div>
        </div>
      </header>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      {loading && !operators.length ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Connecting to execution engine...
        </div>
      ) : (
        <>
          <CoverageMatrix
            operators={operators}
            coverage={coverage}
            selectedBackend={selectedBackend}
            onSelectBackend={setSelectedBackend}
          />

          <div className="grid">
            <BenchmarkRunner />
            <WorkloadPlannerView />
          </div>
        </>
      )}

      <footer style={{ marginTop: '3rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        Built by Ryan Vo (<a href="mailto:ryandtvo@gmail.com" style={{ color: 'var(--accent)' }}>ryandtvo@gmail.com</a>) &bull; GitHub: A220man &bull; Orbit Station Platform
      </footer>
    </div>
  );
};

export default App;
