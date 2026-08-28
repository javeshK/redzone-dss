import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getDistrict, getHabitations, getRecommendation, getSites } from '../api/client';
import MapView from '../components/MapView';
import RecommendationCard from '../components/RecommendationCard';
import { useApp } from '../context/AppContext';
import { DEFAULT_LAYERS, HabitationSummary, PriorityClass, RecommendationResponse, SiteSummary } from '../types';

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
      <div className="planner-sidebar">
        <h2>Relocation Planner</h2>
        <p className="sidebar-desc">
          {sites.length} screened candidate sites · ranked by U_ij suitability.
          Capacity is first-order physical screening — not statutory allotment.
        </p>
        <input
          className="hab-search"
          type="search"
          placeholder="Search habitation…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="hab-filter"
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as PriorityClass | 'All')}
        >
          <option value="All">All priorities</option>
          <option value="Immediate">Immediate</option>
          <option value="Short-term">Short-term</option>
          <option value="Medium-term">Medium-term</option>
          <option value="Monitor">Monitor</option>
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
                {h.priority} · Pop {h.pop}
                {h.rec_site_id ? ` · → ${h.rec_site_id}` : ''}
              </span>
            </button>
          ))}
        </div>
      </div>
      <div className="planner-main">
        <div className="planner-map">
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
            <span className="legend-dot hab-dot" /> Selected habitation
            <span className="legend-dot site-rec" /> Recommended site
            <span className="legend-dot site-alt" /> Runner-up site
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
  );
}
