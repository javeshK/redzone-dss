import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDistrict, getLayer, getHabitations, getSites, getRainfallScenario } from '../api/client';
import MapView from '../components/MapView';
import LayerToggles from '../components/LayerToggles';
import PageError from '../components/PageError';
import { useApp } from '../context/AppContext';
import { HabitationSummary, SiteSummary } from '../types';
import { t, translatePriority } from '../i18n';

const SCENARIO_FACTORS = [1.0, 1.2, 1.5] as const;

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
  const [rainfallFactor, setRainfallFactor] = useState<number>(1.0);
  const [scenarioActive, setScenarioActive] = useState(false);
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

  useEffect(() => {
    if (rainfallFactor === 1.0) {
      setScenarioActive(false);
      getHabitations().then((habs) => {
        setLocalHabs(habs);
        setHabitations(habs);
      });
      return;
    }
    setScenarioActive(true);
    getRainfallScenario(rainfallFactor)
      .then((scenario) => {
        setLocalHabs((prev) =>
          prev.map((hab) => {
            const updated = scenario.habitations.find((s) => s.id === hab.id);
            if (!updated) return hab;
            return { ...hab, h: updated.h, h_ls: updated.h_ls, h_ff: updated.h_ff, zone_class: updated.zone_class };
          })
        );
      })
      .catch(() => setScenarioActive(false));
  }, [rainfallFactor, setHabitations]);

  const handleHabitationClick = (id: string) => {
    setSelectedHabitationId(id);
    navigate(`/habitation/${id}`);
  };

  if (loading) return <div className="page loading">Loading map…</div>;
  if (error) return <PageError message={error} onRetry={() => { refreshAppData(); loadMap(); }} />;

  return (
    <div className="page map-page">
      <div className="map-sidebar">
        <div className="scenario-control card">
          <h3>{t('map.scenario')}</h3>
          <input
            type="range"
            min={0}
            max={SCENARIO_FACTORS.length - 1}
            step={1}
            value={SCENARIO_FACTORS.indexOf(rainfallFactor as typeof SCENARIO_FACTORS[number])}
            onChange={(e) => setRainfallFactor(SCENARIO_FACTORS[Number(e.target.value)])}
          />
          <span className="scenario-factor">{rainfallFactor}x rainfall</span>
        </div>
        {scenarioActive && (
          <div className="banner banner-warning scenario-banner">
            {t('map.scenarioBanner')}
          </div>
        )}
        <LayerToggles layers={layers} onToggle={toggleLayer} />
        <div className="hab-list">
          <h3>{t('map.habitations')}</h3>
          {habitations.map((h) => (
            <button
              key={h.id}
              className={`hab-item${selectedHabitationId === h.id ? ' selected' : ''}`}
              onClick={() => handleHabitationClick(h.id)}
            >
              <span className="hab-name">{h.name}</span>
              <span className={`hab-priority p-${h.priority.toLowerCase().replace('-', '')}`}>
                {translatePriority(h.priority)}
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
