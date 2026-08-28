import { RecommendationResponse } from '../types';

interface RecommendationCardProps {
  recommendation: RecommendationResponse | null;
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
}

const U_IJ_LABELS: Record<string, string> = {
  safety: 'Safety (1 − H)',
  distance: 'Distance proximity',
  road: 'Road access',
  healthcare: 'Healthcare access',
  school: 'School access',
  water: 'Water access',
  capacity_fit: 'Capacity fit',
};

function SiteCard({
  title,
  site,
  highlight,
}: {
  title: string;
  site: RecommendationResponse['top'];
  highlight?: boolean;
}) {
  return (
    <div className={`site-card${highlight ? ' site-card-top' : ''}`}>
      <h4>{title}: {site.site_name}</h4>
      <div className="site-score">U_ij suitability score: {site.score.toFixed(2)}</div>
      {!site.meets_capacity_threshold && (
        <div className="banner banner-warning compact">
          Below 0.5× population capacity — split relocation may be required
        </div>
      )}
      <div className="score-grid compact">
        <div className="score-item"><span>Site hazard (H)</span><span>{site.safety.toFixed(2)}</span></div>
        <div className="score-item"><span>Distance</span><span>{site.distance_km.toFixed(1)} km</span></div>
        <div className="score-item"><span>Road access</span><span>{site.road_access.toFixed(2)}</span></div>
        <div className="score-item"><span>Healthcare</span><span>{site.healthcare_access.toFixed(2)}</span></div>
        <div className="score-item"><span>Water</span><span>{site.water_access.toFixed(2)}</span></div>
        <div className="score-item"><span>School</span><span>{site.school_access.toFixed(2)}</span></div>
        <div className="score-item"><span>Capacity</span><span>{site.capacity}</span></div>
        <div className="score-item highlight-cap">
          <span>Available capacity</span>
          <span>{site.capacity_available}</span>
        </div>
      </div>
      <p className="capacity-note">First-order physical screening capacity</p>

      {site.explain && site.explain.length > 0 && (
        <>
          <h5>U_ij score breakdown</h5>
          <table className="explain-table compact">
            <thead>
              <tr><th>Factor</th><th>Value</th><th>Weight</th><th>Contribution</th></tr>
            </thead>
            <tbody>
              {site.explain.map((e) => (
                <tr key={e.factor}>
                  <td>{U_IJ_LABELS[e.factor] ?? e.factor}</td>
                  <td>{e.value.toFixed(2)}</td>
                  <td>{e.weight.toFixed(2)}</td>
                  <td>{e.contribution.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h5>Why this site?</h5>
      <ul className="reason-list">
        {site.reasons.map((r, i) => <li key={i}>{r}</li>)}
      </ul>
    </div>
  );
}

export default function RecommendationCard({ recommendation, loading, error, onRetry }: RecommendationCardProps) {
  if (loading) return <div className="panel loading">Loading recommendation…</div>;
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
    return <div className="panel empty">Select a habitation to view relocation recommendation.</div>;
  }

  return (
    <div className="panel recommendation-panel">
      <h2>Relocation Recommendation — {recommendation.hab_name}</h2>

      {recommendation.comparison && (
        <div className="comparison-panel">
          <h3>Top vs runner-up</h3>
          <div className="comparison-stats">
            <span>Δ U_ij: <strong>+{recommendation.comparison.score_delta.toFixed(2)}</strong></span>
            <span>Δ distance: <strong>{recommendation.comparison.distance_delta_km.toFixed(1)} km</strong></span>
            <span>Δ capacity: <strong>{recommendation.comparison.capacity_delta}</strong></span>
          </div>
          <ul className="reason-list">
            {recommendation.comparison.notes.map((note, i) => <li key={i}>{note}</li>)}
          </ul>
        </div>
      )}

      <div className="site-cards-grid">
        <SiteCard title="Recommended site" site={recommendation.top} highlight />
        {recommendation.runner_up && (
          <SiteCard title="Runner-up" site={recommendation.runner_up} />
        )}
      </div>
    </div>
  );
}
