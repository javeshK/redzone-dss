import { Kpis } from '../types';

interface KpiCardsProps {
  kpis: Kpis;
  loading?: boolean;
}

export default function KpiCards({ kpis, loading }: KpiCardsProps) {
  if (loading) return <div className="kpi-grid loading">Loading KPIs…</div>;

  const cards = [
    { label: 'Habitations', value: kpis.habitation_count },
    { label: 'Immediate priority', value: kpis.immediate_count, highlight: true },
    { label: 'Short-term', value: kpis.short_term_count },
    { label: 'Candidate sites', value: kpis.site_count },
    { label: 'Red-zone area (ha)', value: kpis.red_zone_area_ha.toLocaleString() },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((c) => (
        <div key={c.label} className={`kpi-card${c.highlight ? ' highlight' : ''}`}>
          <div className="kpi-value">{c.value}</div>
          <div className="kpi-label">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
