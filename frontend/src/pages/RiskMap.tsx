import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDistrict, getLayer, getHabitations, getSites, getRainfallScenario } from '../api/client';
import MapView from '../components/MapView';
import LayerToggles from '../components/LayerToggles';
import PageError from '../components/PageError';
import { useApp } from '../context/AppContext';
import { HabitationSummary, RainfallScenarioMode, SiteSummary } from '../types';
import { t, translatePriority } from '../i18n';

const SCENARIO_FACTORS = [1.0, 1.2, 1.5] as const;
const DEFAULT_HISTORICAL_DATE = '2013-06-16';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function applyScenarioHabs(
  prev: HabitationSummary[],
  scenario: { habitations: Array<{ id: string; h: number; h_ls: number; h_ff: number; zone_class: HabitationSummary['zone_class'] }> },
): HabitationSummary[] {
  return prev.map((hab) => {
    const updated = scenario.habitations.find((s) => s.id === hab.id);
    if (!updated) return hab;
    return { ...hab, h: updated.h, h_ls: updated.h_ls, h_ff: updated.h_ff, zone_class: updated.zone_class };
  });
}

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
  const [scenarioMode, setScenarioMode] = useState<RainfallScenarioMode>('baseline');
  const [scenarioDate, setScenarioDate] = useState(DEFAULT_HISTORICAL_DATE);
  const [scenarioActive, setScenarioActive] = useState(false);
  const [scenarioNote, setScenarioNote] = useState('');
  const [scenarioError, setScenarioError] = useState('');
  const [layersLoading, setLayersLoading] = useState(false);
  const navigate = useNavigate();

  const loadMap = useCallback(() => {
    setLoading(true);
    setError('');
    Promise.all([getDistrict(), getHabitations(), getSites()])
      .then(([district, habs, siteList]) => {
        setBbox(district.bbox);
        setDistrictGeojson(district.geojson);
        setLocalHabs(habs);
        setHabitations(habs);
        setSites(siteList);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [setHabitations]);

  useEffect(() => {
    loadMap();
  }, [loadMap]);

  useEffect(() => {
    const needs: Promise<void>[] = [];
    setLayersLoading(true);

    if (layers.red_zones && !redZones) {
      needs.push(getLayer('red_zones').then(setRedZones));
    }
    if (layers.landslides && !landslides) {
      needs.push(getLayer('landslides').then(setLandslides));
    }
    if (layers.streams && !streams) {
      needs.push(getLayer('streams').then(setStreams));
    }

    if (needs.length === 0) {
      setLayersLoading(false);
      return;
    }

    Promise.all(needs)
      .catch(() => {})
      .finally(() => setLayersLoading(false));
  }, [layers.red_zones, layers.landslides, layers.streams, redZones, landslides, streams]);

  const runScenario = useCallback(() => {
    const isBaseline = scenarioMode === 'baseline' && rainfallFactor === 1.0;
    if (isBaseline) {
      setScenarioActive(false);
      setScenarioNote('');
      setScenarioError('');
      getHabitations().then((habs) => {
        setLocalHabs(habs);
        setHabitations(habs);
      });
      return;
    }

    setScenarioError('');
    getRainfallScenario(rainfallFactor, {
      mode: scenarioMode,
      date: scenarioMode === 'baseline' ? undefined : scenarioDate,
    })
      .then((scenario) => {
        setScenarioActive(true);
        setScenarioNote(scenario.note ?? t('map.scenarioBanner'));
        setLocalHabs((prev) => applyScenarioHabs(prev, scenario));
      })
      .catch((e) => {
        setScenarioError(e instanceof Error ? e.message : 'Scenario failed');
        setScenarioActive(false);
      });
  }, [rainfallFactor, scenarioMode, scenarioDate, setHabitations]);

  useEffect(() => {
    runScenario();
  }, [runScenario]);

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
          <label className="scenario-label">
            {t('map.scenarioMode')}
            <select
              className="hab-filter"
              value={scenarioMode}
              onChange={(e) => {
                const mode = e.target.value as RainfallScenarioMode;
                setScenarioMode(mode);
                if (mode === 'forecast') setScenarioDate(todayIso());
                if (mode === 'historical') setScenarioDate(DEFAULT_HISTORICAL_DATE);
              }}
            >
              <option value="baseline">{t('map.mode.baseline')}</option>
              <option value="historical">{t('map.mode.historical')}</option>
              <option value="forecast">{t('map.mode.forecast')}</option>
            </select>
          </label>
          {scenarioMode !== 'baseline' && (
            <label className="scenario-label">
              {t('map.scenarioDate')}
              <input
                type="date"
                className="hab-filter"
                value={scenarioDate}
                onChange={(e) => setScenarioDate(e.target.value)}
              />
            </label>
          )}
          <label className="scenario-label">
            {t('map.scenario')} ×
            <input
              type="range"
              min={0}
              max={SCENARIO_FACTORS.length - 1}
              step={1}
              value={SCENARIO_FACTORS.indexOf(rainfallFactor as typeof SCENARIO_FACTORS[number])}
              onChange={(e) => setRainfallFactor(SCENARIO_FACTORS[Number(e.target.value)])}
            />
            <span className="scenario-factor">{rainfallFactor}x</span>
          </label>
          <p className="scenario-hint">{t('map.scenarioNote')}</p>
        </div>
        {scenarioActive && (
          <div className="banner banner-warning scenario-banner">
            {scenarioNote || t('map.scenarioBanner')}
          </div>
        )}
        {scenarioError && (
          <div className="banner banner-warning scenario-banner">{scenarioError}</div>
        )}
        {layersLoading && (
          <div className="banner banner-info compact">Loading map layers…</div>
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
