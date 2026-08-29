import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDistrict, triggerRefresh } from '../api/client';
import KpiCards from '../components/KpiCards';
import PageError from '../components/PageError';
import SourceBadge from '../components/SourceBadge';
import AlertPanel from '../components/AlertPanel';
import { useApp } from '../context/AppContext';
import { DistrictResponse } from '../types';
import { t } from '../i18n';

const IS_DEV = import.meta.env.DEV;

export default function Overview() {
  const { meta, refreshAppData } = useApp();
  const [data, setData] = useState<DistrictResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    setError('');
    getDistrict()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await triggerRefresh();
      await refreshAppData();
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Refresh failed');
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <div className="page loading">Loading overview…</div>;
  if (error) return <PageError message={error} onRetry={() => { refreshAppData(); load(); }} />;

  const displayMeta = data?.meta ?? meta;
  const lastUpdated = displayMeta?.data_as_of ?? displayMeta?.generated_at;

  return (
    <div className="page overview-page">
      <div className="page-header">
        <h2>{data!.name} District — Decision Support Overview</h2>
        <p className="page-desc">
          Multi-hazard red-zone identification, habitation vulnerability scoring,
          and explainable relocation recommendations for vulnerable settlements.
        </p>
        {lastUpdated && (
          <p className="last-updated">
            <strong>{t('overview.lastUpdated')}:</strong>{' '}
            {new Date(lastUpdated).toLocaleString()}
            {displayMeta?.pipeline_version && (
              <span className="pipeline-version"> (pipeline v{displayMeta.pipeline_version})</span>
            )}
          </p>
        )}
        {IS_DEV && (
          <button
            className="btn-secondary refresh-btn"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing…' : t('overview.refresh')}
          </button>
        )}
      </div>

      {displayMeta && <KpiCards kpis={displayMeta.kpis} />}

      <AlertPanel />

      <div className="overview-grid">
        <section className="card">
          <h3>System Status</h3>
          <ul className="info-list">
            <li><strong>District:</strong> {displayMeta?.district ?? data!.name}, Uttarakhand</li>
            <li><strong>Model version:</strong> {displayMeta?.model_version}</li>
            <li><strong>Weights version:</strong> {displayMeta?.weights_version}</li>
            <li><strong>Generated:</strong> {displayMeta ? new Date(displayMeta.generated_at).toLocaleString() : '—'}</li>
            <li><strong>Hazards:</strong> Landslide + Cloudburst / flash-flood</li>
          </ul>
        </section>

        <section className="card">
          <h3>Data Sources &amp; Provenance</h3>
          <ul className="source-list">
            {displayMeta?.sources.map((s) => (
              <li key={s.layer}>
                <strong>{s.layer}</strong>
                <SourceBadge provenance={s.provenance} />
                {s.note && <span className="source-note">{s.note}</span>}
              </li>
            ))}
          </ul>
        </section>

        <section className="card full-width">
          <h3>Limitations</h3>
          <ul className="limitation-list">
            {displayMeta?.limitations.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </section>
      </div>

      <div className="action-bar">
        <button className="btn-primary" onClick={() => navigate('/map')}>
          Open Risk Map
        </button>
        <button className="btn-secondary" onClick={() => navigate('/habitation')}>
          View Habitations
        </button>
        <button className="btn-secondary" onClick={() => navigate('/planner')}>
          Relocation Planner
        </button>
      </div>
    </div>
  );
}
