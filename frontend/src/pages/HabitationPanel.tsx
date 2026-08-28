import { useEffect, useMemo, useState } from 'react';

import { useParams, useNavigate } from 'react-router-dom';

import { getHabitations, getHabitation } from '../api/client';

import ExplainPanel from '../components/ExplainPanel';

import { useApp } from '../context/AppContext';

import { HabitationDetail, HabitationSummary, PriorityClass } from '../types';



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

  const [detail, setDetail] = useState<HabitationDetail | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState('');

  const [search, setSearch] = useState('');

  const [priorityFilter, setPriorityFilter] = useState<PriorityClass | 'All'>('All');



  useEffect(() => {

    getHabitations().then(setList).catch(() => {});

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



  return (

    <div className="page habitation-page">

      <div className="habitation-sidebar">

        <h2>Habitations</h2>

        <p className="sidebar-desc">

          {list.length} settlements · {immediateCount} Immediate priority

        </p>

        <input

          className="hab-search"

          type="search"

          placeholder="Search by name…"

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

              onClick={() => navigate(`/habitation/${h.id}`)}

            >

              <span className="hab-name">{h.name}</span>

              <span className="hab-meta">

                {h.block} · Pop {h.pop} · H {h.h.toFixed(2)} · {h.pct_red.toFixed(0)}% red

              </span>

              <span className={`hab-priority p-${h.priority.toLowerCase().replace('-', '')}`}>

                {h.priority}

              </span>

            </button>

          ))}

          {filtered.length === 0 && (

            <p className="sidebar-empty">No habitations match your filter.</p>

          )}

        </div>

      </div>

      <div className="habitation-detail">

        <ExplainPanel

          habitation={detail}

          loading={loading && !!id}

          error={error}

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

  );

}

