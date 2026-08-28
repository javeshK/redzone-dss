import { LayerVisibility } from '../types';

interface LayerTogglesProps {
  layers: LayerVisibility;
  onToggle: (key: keyof LayerVisibility) => void;
}

const LABELS: Record<keyof LayerVisibility, string> = {
  district: 'District boundary',
  red_zones: 'Red zones',
  landslides: 'Landslide inventory',
  streams: 'Streams / rivers',
  habitations: 'Habitations',
  sites: 'Candidate sites',
};

export default function LayerToggles({ layers, onToggle }: LayerTogglesProps) {
  return (
    <div className="layer-toggles">
      <h3>Layers</h3>
      {(Object.keys(LABELS) as (keyof LayerVisibility)[]).map((key) => (
        <label key={key} className="layer-toggle-item">
          <input
            type="checkbox"
            checked={layers[key]}
            onChange={() => onToggle(key)}
          />
          {LABELS[key]}
        </label>
      ))}
      <div className="legend">
        <h4>Red-zone classes</h4>
        <div className="legend-item"><span className="swatch red" /> Red (H ≥ 0.70)</div>
        <div className="legend-item"><span className="swatch orange" /> Orange (0.50–0.70)</div>
        <div className="legend-item"><span className="swatch yellow" /> Yellow (0.30–0.50)</div>
        <div className="legend-item"><span className="swatch green" /> Green (&lt; 0.30)</div>
      </div>
    </div>
  );
}
