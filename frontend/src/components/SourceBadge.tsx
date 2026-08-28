import { Provenance } from '../types';

const LABELS: Record<Provenance, string> = {
  OFFICIAL: 'Official',
  OPEN_DATA: 'Open data',
  DERIVED: 'Derived model',
  EXPERT_SCREENED: 'Expert screened',
  SYNTHETIC: 'Synthetic',
};

const COLORS: Record<Provenance, string> = {
  OFFICIAL: '#2c3e50',
  OPEN_DATA: '#2980b9',
  DERIVED: '#8e44ad',
  EXPERT_SCREENED: '#16a085',
  SYNTHETIC: '#c0392b',
};

interface SourceBadgeProps {
  provenance?: Provenance;
  label?: string;
}

export default function SourceBadge({ provenance = 'DERIVED', label }: SourceBadgeProps) {
  return (
    <span
      className="source-badge"
      style={{ backgroundColor: COLORS[provenance] }}
      title={`Data provenance: ${LABELS[provenance]}`}
    >
      {label ?? LABELS[provenance]}
    </span>
  );
}
