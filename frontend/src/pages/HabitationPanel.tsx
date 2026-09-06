import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getHabitations, getHabitation, getSites } from '../api/client';
import ExplainPanel from '../components/ExplainPanel';
import WorkflowSteps from '../components/WorkflowSteps';
import { useApp } from '../context/AppContext';
import { HabitationDetail, HabitationSummary, PriorityClass, SiteSummary } from '../types';
import { getHabitationListSubtitle, getPriorityPlainLabel } from '../utils/plainLanguage';
import { t, tf } from '../i18n';

const PRIORITY_ORDER: Record<PriorityClass, number> = {
  Immediate: 0,
  'Short-term': 1,
  'Medium-term': 2,
  Monitor: 3,
};

export default function HabitationPanel() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { setSelectedHabitationId, refreshAppData } = useApp();
  const [list, setList] = useState<HabitationSummary[]>([]);
  const [sites, setSites] = useState<SiteSummary[]>([]);
  const [detail, setDetail] = useState<HabitationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<PriorityClass | 'All'>('All');

  const siteNameById = useMemo(() => {
    const map: Record<string, string> = {};
    for (const s of sites) map[s.id] = s.name;
    return map;
  }, [sites]);

  useEffect(() => {
    Promise.all([getHabitations(), getSites()])
      .then(([habs, siteList]) => {
        setList(habs);
        setSites(siteList);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!id) {
      setDetail(null);
      setLoading(false);
      return;
    }
    setSelectedHabitationId(id);
    setLoading(true);
    setError('');
    getHabitation(id)
      .then(setDetail)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, setSelectedHabitationId]);

  const filtered = useMemo(() => {
    return list
      .filter((h) => priorityFilter === 'All' || h.priority === priorityFilter)
      .filter((h) => h.name.toLowerCase().includes(search.toLowerCase()))
      .sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority] || a.name.localeCompare(b.name));
  }, [list, search, priorityFilter]);

  const immediateCount = list.filter((h) => h.priority === 'Immediate').length;
  const recommendedSiteName = detail?.rec_site_id ? siteNameById[detail.rec_site_id] : undefined;

  return (
    <div className="page habitation-page">
      <WorkflowSteps current="habitation" habitationName={detail?.name} />
      <div className="page-columns">
        <div className="habitation-sidebar">
          <h2>{t('hab.sidebarTitle')}</h2>
          <p className="sidebar-desc">
            {tf('hab.sidebarDesc', { count: list.length, urgent: immediateCount })}
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
                onClick={() => navigate(`/habitation/${h.id}`)}
              >
                <span className="hab-name">{h.name}</span>
                <span className="hab-meta">
                  {getHabitationListSubtitle(h, h.rec_site_id ? siteNameById[h.rec_site_id] : undefined)}
                </span>
                <span className={`hab-priority p-${h.priority.toLowerCase().replace('-', '')}`}>
                  {getPriorityPlainLabel(h.priority)}
                </span>
              </button>
            ))}
            {filtered.length === 0 && (
              <p className="sidebar-empty">No villages match your filter.</p>
            )}
          </div>
        </div>
        <div className="habitation-detail">
          <ExplainPanel
            habitation={detail}
            loading={loading && !!id}
            error={error}
            recommendedSiteName={recommendedSiteName}
            onRetry={id ? () => {
              refreshAppData();
              setLoading(true);
              setError('');
              getHabitation(id)
                .then(setDetail)
                .catch((e) => setError(e.message))
                .finally(() => setLoading(false));
            } : undefined}
            onViewRecommendation={id ? () => navigate(`/planner/${id}`) : undefined}
          />
        </div>
      </div>
    </div>
  );
}
