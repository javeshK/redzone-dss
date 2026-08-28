import { HabitationDetail, ZONE_COLORS } from '../types';

import SourceBadge from './SourceBadge';



interface ExplainPanelProps {

  habitation: HabitationDetail | null;

  loading?: boolean;

  error?: string;

  onRetry?: () => void;
  onViewRecommendation?: () => void;

}



const FACTOR_LABELS: Record<string, string> = {

  multi_hazard: 'Multi-hazard (H)',

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

}: ExplainPanelProps) {

  if (loading) return <div className="panel loading">Loading habitation…</div>;

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

    return (

      <div className="panel empty">

        Select a habitation on the map or from the list to view scores and explanation.

      </div>

    );

  }



  const zoneColor = ZONE_COLORS[habitation.zone_class];



  return (

    <div className="panel explain-panel">

      <div className="panel-header">

        <h2>{habitation.name}</h2>

        <div className="panel-badges">

          <SourceBadge provenance={habitation.source ?? 'EXPERT_SCREENED'} />

          {habitation.hazard_source && (

            <span className="source-badge badge-derived">Hazard: {habitation.hazard_source}</span>

          )}

        </div>

      </div>

      <p className="panel-meta">{habitation.block} · Population {habitation.pop}</p>



      <div className="badge-row">

        <div className={`priority-badge priority-${habitation.priority.toLowerCase().replace('-', '')}`}>

          {habitation.priority}

        </div>

        <div className="zone-badge" style={{ borderColor: zoneColor, color: zoneColor }}>

          {habitation.zone_class} zone

        </div>

      </div>



      <div className="score-grid">

        <div className="score-item">

          <span className="score-label">Multi-hazard (H)</span>

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

          <span className="score-label">Priority score (P)</span>

          <span className="score-value">{habitation.p.toFixed(2)}</span>

        </div>

        <div className="score-item">

          <span className="score-label">% in Red Zone</span>

          <span className="score-value">{habitation.pct_red.toFixed(1)}%</span>

        </div>

      </div>



      <h3>Why this priority?</h3>

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

        <>

          <h3>Vulnerability breakdown</h3>

          <p className="panel-desc">

            Five-factor weighted score (missing factors renormalized per MCA contract).

          </p>

          <table className="explain-table">

            <thead>

              <tr><th>Factor</th><th>Score</th><th>Weight</th><th>Contribution</th></tr>

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

        </>

      )}



      {onViewRecommendation && habitation.rec_site_id && (

        <button className="btn-primary" onClick={onViewRecommendation}>

          View Relocation Recommendation

        </button>

      )}

    </div>

  );

}

