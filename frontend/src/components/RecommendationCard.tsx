import { useState } from 'react';
import { RecommendationResponse } from '../types';
import {
  getPlainSiteReasons,
  getRelocationHeadline,
  simplifyReason,
} from '../utils/plainLanguage';
import { t, tf } from '../i18n';

interface RecommendationCardProps {
  recommendation: RecommendationResponse | null;
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
}

function SiteCard({
  title,
  site,
  highlight,
  showTechnical,
}: {
  title: string;
  site: RecommendationResponse['top'];
  highlight?: boolean;
  showTechnical: boolean;
}) {
  const plainReasons = getPlainSiteReasons(site);

  return (
    <div className={`site-card${highlight ? ' site-card-top' : ''}`}>
      <div className="site-card-header">
        <span className="site-card-label">{title}</span>
        <h4 className="site-card-name">{site.site_name}</h4>
      </div>

      <div className="site-highlights">
        <div className="site-highlight">
          <span className="site-highlight-label">{t('label.distance')}</span>
          <span className="site-highlight-value">
            {tf('reloc.distance', { km: site.distance_km.toFixed(1) })}
          </span>
        </div>
        <div className="site-highlight">
          <span className="site-highlight-label">{t('label.people')}</span>
          <span className="site-highlight-value">
            {tf('reloc.capacity', { avail: site.capacity_available })}
          </span>
        </div>
      </div>

      {!site.meets_capacity_threshold && (
        <div className="banner banner-warning compact">{t('reloc.capacityWarn')}</div>
      )}

      <h5>{t('reloc.whyThisSite')}</h5>
      <ul className="reason-list plain-reason-list">
        {plainReasons.map((r, i) => (
          <li key={i}>{r}</li>
        ))}
      </ul>

      {showTechnical && (
        <div className="technical-details compact">
          <div className="score-grid compact">
            <div className="score-item">
              <span>Site hazard (H)</span>
              <span>{site.safety.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span>Road</span>
              <span>{site.road_access.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span>Healthcare</span>
              <span>{site.healthcare_access.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span>Water</span>
              <span>{site.water_access.toFixed(2)}</span>
            </div>
            <div className="score-item">
              <span>Total capacity</span>
              <span>{site.capacity}</span>
            </div>
            <div className="score-item highlight-cap">
              <span>Available</span>
              <span>{site.capacity_available}</span>
            </div>
          </div>
          {site.explain && site.explain.length > 0 && (
            <table className="explain-table compact">
              <thead>
                <tr><th>Factor</th><th>Value</th><th>Weight</th><th>Contribution</th></tr>
              </thead>
              <tbody>
                {site.explain.map((e) => (
                  <tr key={e.factor}>
                    <td>{e.factor}</td>
                    <td>{e.value.toFixed(2)}</td>
                    <td>{e.weight.toFixed(2)}</td>
                    <td>{e.contribution.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <ul className="reason-list technical-reason-list">
            {site.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function RecommendationCard({
  recommendation,
  loading,
  error,
  onRetry,
}: RecommendationCardProps) {
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
  if (!recommendation) {
    return <div className="panel empty">{t('reloc.selectPrompt')}</div>;
  }

  const comparisonNotes = recommendation.comparison?.notes
    .map(simplifyReason)
    .filter(Boolean) ?? [];

  return (
    <div className="panel recommendation-panel">
      <h2>{t('reloc.title')}</h2>
      <p className="relocation-headline">{getRelocationHeadline(recommendation)}</p>

      {comparisonNotes.length > 0 && (
        <div className="comparison-panel">
          <h3>{t('reloc.compare')}</h3>
          <ul className="reason-list plain-reason-list">
            {comparisonNotes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="site-cards-grid">
        <SiteCard
          title={t('reloc.goHere')}
          site={recommendation.top}
          highlight
          showTechnical={showTechnical}
        />
        {recommendation.runner_up && (
          <SiteCard
            title={t('reloc.backup')}
            site={recommendation.runner_up}
            showTechnical={showTechnical}
          />
        )}
      </div>

      <p className="explain-note">{t('hab.explainNote')}</p>

      <button
        type="button"
        className="btn-text technical-toggle"
        onClick={() => setShowTechnical((v) => !v)}
      >
        {showTechnical ? t('hab.hideTechnical') : t('hab.showTechnical')}
      </button>
    </div>
  );
}
