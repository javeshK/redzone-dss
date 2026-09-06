import { useState } from 'react';
import { HabitationDetail, ZONE_COLORS } from '../types';
import {
  getActionSteps,
  getPriorityPlainLabel,
  getRehabilitationReasons,
  getRiskSummary,
  getZonePlainLabel,
} from '../utils/plainLanguage';
import { t } from '../i18n';
import SourceBadge from './SourceBadge';

interface ExplainPanelProps {
  habitation: HabitationDetail | null;
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
  onViewRecommendation?: () => void;
  recommendedSiteName?: string;
}

const FACTOR_LABELS: Record<string, string> = {
  multi_hazard: 'Overall hazard (H)',
  vulnerability: 'Vulnerability (V)',
  pct_red_override: 'Red-zone override',
  h_hab_override: 'Hazard override',
  population: 'Population size',
  dependents: 'Dependents share',
  isolation: 'Isolation / road access',
  health_access: 'Health access gap',
  historical_exposure: 'Historical exposure',
};

function factorLabel(factor: string, note?: string) {
  const label = FACTOR_LABELS[factor] ?? factor;
  return note ? `${label} — ${note}` : label;
}

export default function ExplainPanel({
  habitation,
  loading,
  error,
  onRetry,
  onViewRecommendation,
  recommendedSiteName,
}: ExplainPanelProps) {
  const [showTechnical, setShowTechnical] = useState(false);

  if (loading) return <div className="panel loading">Loading…</div>;
  if (error) {
    return (
      <div className="panel error-panel">
        <p>{error}</p>
        {onRetry && (
          <button type="button" className="btn-primary" onClick={onRetry}>Retry</button>
        )}
      </div>
    );
  }
  if (!habitation) {
    return <div className="panel empty">{t('hab.selectPrompt')}</div>;
  }

  const zoneColor = ZONE_COLORS[habitation.zone_class];
  const rehabReasons = getRehabilitationReasons(habitation);
  const actionSteps = getActionSteps(habitation, !!(habitation.rec_site_id || onViewRecommendation));
  const hasRelocation = !!(habitation.rec_site_id || onViewRecommendation);

  return (
    <div className="panel explain-panel">
      <div className="panel-header">
        <h2>{habitation.name}</h2>
        <div className="panel-badges">
          <SourceBadge provenance={habitation.source ?? 'EXPERT_SCREENED'} />
        </div>
      </div>
      <p className="panel-meta">
        {habitation.block} · {habitation.pop} {t('label.people')}
      </p>

      <div className="badge-row">
        <div className={`priority-badge priority-${habitation.priority.toLowerCase().replace('-', '')}`}>
          {getPriorityPlainLabel(habitation.priority)}
        </div>
        <div className="zone-badge" style={{ borderColor: zoneColor, color: zoneColor }}>
          {getZonePlainLabel(habitation.zone_class)}
        </div>
      </div>

      <section className="plain-summary-card">
        <h3>{t('hab.whatThisMeans')}</h3>
        <p className="plain-summary-text">{getRiskSummary(habitation)}</p>
      </section>

      {(habitation.priority === 'Immediate' || habitation.priority === 'Short-term') && (
        <section className="plain-reasons-card">
          <h3>{t('hab.whyRelocate')}</h3>
          <ul className="plain-reason-list">
            {rehabReasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="action-steps-card">
        <h3>{t('hab.whatToDo')}</h3>
        <ol className="action-steps-list">
          {actionSteps.map((s) => (
            <li key={s.step} className={s.urgent ? 'action-urgent' : ''}>
              {s.text}
            </li>
          ))}
        </ol>
      </section>

      {hasRelocation && recommendedSiteName && (
        <section className="relocation-preview-card">
          <h3>{t('hab.recommendedCenter')}</h3>
          <p className="relocation-preview-name">{recommendedSiteName}</p>
        </section>
      )}

      {onViewRecommendation && (
        <button className="btn-primary btn-large" onClick={onViewRecommendation}>
          {t('hab.viewRelocation')}
        </button>
      )}

      <p className="explain-note">{t('hab.explainNote')}</p>

      <button
        type="button"
        className="btn-text technical-toggle"
        onClick={() => setShowTechnical((v) => !v)}
      >
        {showTechnical ? t('hab.hideTechnical') : t('hab.showTechnical')}
      </button>

      {showTechnical && (
        <div className="technical-details">
          <h3>{t('hab.technicalDetails')}</h3>
          <div className="score-grid">
            <div className="score-item">
              <span className="score-label">Overall hazard (H)</span>
              <span className="score-value">{habitation.h.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span className="score-label">Landslide (H_ls)</span>
              <span className="score-value">{habitation.h_ls.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span className="score-label">Flash-flood (H_ff)</span>
              <span className="score-value">{habitation.h_ff.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span className="score-label">Vulnerability (V)</span>
              <span className="score-value">{habitation.v.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span className="score-label">Priority (P)</span>
              <span className="score-value">{habitation.p.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span className="score-label">% in red zone</span>
              <span className="score-value">{habitation.pct_red.toFixed(1)}%</span>
            </div>
          </div>

          <table className="explain-table">
            <thead>
              <tr><th>Factor</th><th>Value</th><th>Weight</th><th>Contribution</th></tr>
            </thead>
            <tbody>
              {habitation.explain.map((e) => (
                <tr key={e.factor}>
                  <td>{factorLabel(e.factor, e.note)}</td>
                  <td>{typeof e.value === 'number' && e.factor.includes('pct') ? e.value.toFixed(1) : e.value.toFixed(2)}</td>
                  <td>{e.weight.toFixed(2)}</td>
                  <td>{e.contribution.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {habitation.vuln_explain.length > 0 && (
            <table className="explain-table">
              <thead>
                <tr><th>Vulnerability factor</th><th>Score</th><th>Weight</th><th>Contribution</th></tr>
              </thead>
              <tbody>
                {habitation.vuln_explain.map((e) => (
                  <tr key={e.factor}>
                    <td>{factorLabel(e.factor)}</td>
                    <td>{e.value.toFixed(2)}</td>
                    <td>{e.weight.toFixed(2)}</td>
                    <td>{e.contribution.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
