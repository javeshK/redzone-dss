import { useEffect, useState } from 'react';
import { getAlerts } from '../api/client';
import { AlertData } from '../types';
import { t } from '../i18n';

export default function AlertPanel() {
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
            <strong>{a.habitation_name}</strong>
            <span className={`hab-priority p-${a.priority.toLowerCase().replace('-', '')}`}>
              {a.priority}
            </span>
            <ul>
              {a.reasons.slice(0, 2).map((r, i) => (
                <li key={i} className="alert-reason">{r}</li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  );
}
