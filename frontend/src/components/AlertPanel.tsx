import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAlerts } from '../api/client';
import { AlertData } from '../types';
import { simplifyAlertReason } from '../utils/plainLanguage';
import { t, translatePriority } from '../i18n';

export default function AlertPanel() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<AlertData | null>(null);

  useEffect(() => {
    getAlerts().then(setAlerts).catch(() => setAlerts({ alert_count: 0, alerts: [] }));
  }, []);

  if (!alerts || alerts.alert_count === 0) return null;

  return (
    <section className="card alert-panel">
      <h3>{t('overview.alerts')} ({alerts.alert_count})</h3>
      <ul className="alert-list">
        {alerts.alerts.slice(0, 5).map((a) => (
          <li key={a.id} className={`alert-item severity-${a.severity}`}>
            <div className="alert-item-header">
              <strong>{a.habitation_name}</strong>
              <span className={`hab-priority p-${a.priority.toLowerCase().replace('-', '')}`}>
                {translatePriority(a.priority)}
              </span>
            </div>
            <ul className="alert-reasons">
              {a.reasons.slice(0, 2).map((r, i) => (
                <li key={i} className="alert-reason">{simplifyAlertReason(r)}</li>
              ))}
            </ul>
            <button
              type="button"
              className="btn-secondary btn-small alert-action"
              onClick={() => navigate(`/planner/${a.habitation_id}`)}
            >
              {t('alert.viewPlan')}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
