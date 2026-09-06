import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getDistrict, getHabitations, getRecommendation, getSites } from '../api/client';
import MapView from '../components/MapView';
import RecommendationCard from '../components/RecommendationCard';
import WorkflowSteps from '../components/WorkflowSteps';
import { useApp } from '../context/AppContext';
import {
  DEFAULT_LAYERS,
  HabitationSummary,
  PriorityClass,
  RecommendationResponse,
  SiteSummary,
} from '../types';
import { getHabitationListSubtitle, getPriorityPlainLabel } from '../utils/plainLanguage';
import { t, tf } from '../i18n';

const PRIORITY_ORDER: Record<PriorityClass, number> = {
  Immediate: 0,
  'Short-term': 1,
  'Medium-term': 2,
  Monitor: 3,
};

const PLANNER_LAYERS = {
  ...DEFAULT_LAYERS,
  red_zones: false,
  landslides: false,
  streams: false,
};

export default function RelocationPlanner() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { refreshAppData } = useApp();
  const [list, setList] = useState<HabitationSummary[]>([]);
  const [sites, setSites] = useState<SiteSummary[]>([]);
  const [bbox, setBbox] = useState<number[]>([78.75, 30.05, 79.55, 30.75]);
  const [districtGeojson, setDistrictGeojson] = useState<GeoJSON.FeatureCollection>();
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<PriorityClass | 'All'>('All');

  const siteNameById = useMemo(() => {
    const map: Record<string, string> = {};
    for (const s of sites) map[s.id] = s.name;
    return map;
  }, [sites]);

  useEffect(() => {
    Promise.all([getHabitations(), getSites(), getDistrict()])
      .then(([habs, siteList, district]) => {
        setList(habs);
        setSites(siteList);
        setBbox(district.bbox);
        setDistrictGeojson(district.geojson);
      })
      .catch(() => {});
  }, []);

  const loadRecommendation = (habId: string) => {
    setLoading(true);
    setError('');
    getRecommendation(habId)
      .then(setRecommendation)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!id) {
      setRecommendation(null);
      return;
    }
    loadRecommendation(id);
  }, [id]);

  const filtered = useMemo(() => {
    return list
      .filter((h) => priorityFilter === 'All' || h.priority === priorityFilter)
      .filter((h) => h.name.toLowerCase().includes(search.toLowerCase()))
      .sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority] || a.name.localeCompare(b.name));
  }, [list, search, priorityFilter]);

  const selectedHab = id ? list.find((h) => h.id === id) : undefined;
  const recommendedSiteId = recommendation?.top.site_id ?? null;
  const runnerUpSiteId = recommendation?.runner_up?.site_id ?? null;

  return (
    <div className="page planner-page">
      <WorkflowSteps current="planner" habitationName={selectedHab?.name} />
      <div className="page-columns">
        <div className="planner-sidebar">
          <h2>{t('reloc.sidebarTitle')}</h2>
          <p className="sidebar-desc">
            {tf('reloc.sidebarDesc', { count: sites.length })}
          </p>
          <input
            className="hab-search"
            type="search"
            placeholder={t('hab.search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            className="hab-filter"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value as PriorityClass | 'All')}
          >
            <option value="All">All priorities</option>
            <option value="Immediate">{t('priority.immediate')}</option>
            <option value="Short-term">{t('priority.shortterm')}</option>
            <option value="Medium-term">{t('priority.mediumterm')}</option>
            <option value="Monitor">{t('priority.monitor')}</option>
          </select>
          <div className="hab-list-scroll">
            {filtered.map((h) => (
              <button
                key={h.id}
                className={`hab-item${id === h.id ? ' selected' : ''}`}
                onClick={() => navigate(`/planner/${h.id}`)}
              >
                <span className="hab-name">{h.name}</span>
                <span className="hab-meta">
                  {getHabitationListSubtitle(
                    h,
                    h.rec_site_id ? siteNameById[h.rec_site_id] : undefined,
                  )}
                </span>
                <span className={`hab-priority p-${h.priority.toLowerCase().replace('-', '')}`}>
                  {getPriorityPlainLabel(h.priority)}
                </span>
              </button>
            ))}
          </div>
        </div>
        <div className="planner-main">
          <div className="planner-map">
            <p className="planner-map-caption">{t('reloc.mapLegend')}</p>
            <MapView
              bbox={bbox}
              districtGeojson={districtGeojson}
              habitations={selectedHab ? [selectedHab] : []}
              sites={sites}
              layers={{ ...PLANNER_LAYERS, habitations: !!selectedHab, sites: true }}
              selectedHabitationId={id}
              recommendedSiteId={recommendedSiteId}
              highlightedSiteId={runnerUpSiteId}
              height="280px"
            />
            <div className="planner-map-legend">
              <span className="legend-dot hab-dot" /> Your village
              <span className="legend-dot site-rec" /> Go here (recommended)
              <span className="legend-dot site-alt" /> Backup option
            </div>
          </div>
          <div className="planner-detail">
            <RecommendationCard
              recommendation={recommendation}
              loading={loading}
              error={error}
              onRetry={id ? () => { refreshAppData(); loadRecommendation(id); } : undefined}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
