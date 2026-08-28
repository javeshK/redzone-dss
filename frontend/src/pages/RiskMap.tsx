import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDistrict, getLayer, getHabitations, getSites } from '../api/client';
import MapView from '../components/MapView';
import LayerToggles from '../components/LayerToggles';
import PageError from '../components/PageError';
import { useApp } from '../context/AppContext';
import { HabitationSummary, SiteSummary } from '../types';

export default function RiskMap() {
  const { layers, toggleLayer, selectedHabitationId, setSelectedHabitationId, setHabitations, refreshAppData } = useApp();
  const [bbox, setBbox] = useState<number[]>([78.75, 30.05, 79.55, 30.75]);
  const [districtGeojson, setDistrictGeojson] = useState<GeoJSON.FeatureCollection>();
  const [redZones, setRedZones] = useState<GeoJSON.FeatureCollection>();
  const [landslides, setLandslides] = useState<GeoJSON.FeatureCollection>();
  const [streams, setStreams] = useState<GeoJSON.FeatureCollection>();
  const [habitations, setLocalHabs] = useState<HabitationSummary[]>([]);
  const [sites, setSites] = useState<SiteSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const loadMap = () => {
    setLoading(true);
    setError('');
    Promise.all([
      getDistrict(),
      getLayer('red_zones'),
      getLayer('landslides'),
      getLayer('streams'),
      getHabitations(),
      getSites(),
    ])
      .then(([district, rz, ls, st, habs, siteList]) => {
        setBbox(district.bbox);
        setDistrictGeojson(district.geojson);
        setRedZones(rz);
        setLandslides(ls);
        setStreams(st);
        setLocalHabs(habs);
        setHabitations(habs);
        setSites(siteList);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadMap();
  }, [setHabitations]);

  const handleHabitationClick = (id: string) => {
    setSelectedHabitationId(id);
    navigate(`/habitation/${id}`);
  };

  if (loading) return <div className="page loading">Loading map…</div>;
  if (error) return <PageError message={error} onRetry={() => { refreshAppData(); loadMap(); }} />;

  return (
    <div className="page map-page">
      <div className="map-sidebar">
        <LayerToggles layers={layers} onToggle={toggleLayer} />
        <div className="hab-list">
          <h3>Habitations</h3>
          {habitations.map((h) => (
            <button
              key={h.id}
              className={`hab-item${selectedHabitationId === h.id ? ' selected' : ''}`}
              onClick={() => handleHabitationClick(h.id)}
            >
              <span className="hab-name">{h.name}</span>
              <span className={`hab-priority p-${h.priority.toLowerCase().replace('-', '')}`}>
                {h.priority}
              </span>
            </button>
          ))}
        </div>
      </div>
      <div className="map-container">
        <MapView
          bbox={bbox}
          districtGeojson={districtGeojson}
          redZones={redZones}
          landslides={landslides}
          streams={streams}
          habitations={habitations}
          sites={sites}
          layers={layers}
          onHabitationClick={handleHabitationClick}
          selectedHabitationId={selectedHabitationId}
        />
      </div>
    </div>
  );
}
