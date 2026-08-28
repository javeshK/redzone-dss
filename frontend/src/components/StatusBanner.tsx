import { useEffect, useState } from 'react';
import { isUsingApi, resetApiCheck } from '../api/client';
import { getHealth } from '../api/client';

export default function StatusBanner() {
  const [mode, setMode] = useState<'loading' | 'api' | 'static'>('loading');

  useEffect(() => {
    resetApiCheck();
    getHealth()
      .then(() => setMode(isUsingApi() ? 'api' : 'static'))
      .catch(() => setMode('static'));
  }, []);

  if (mode === 'loading') return null;

  return (
    <div className={`banner ${mode === 'static' ? 'banner-warning' : 'banner-info'}`}>
      {mode === 'api'
        ? 'Connected to API — live data from precomputed artifacts.'
        : 'Static fallback mode — loading from /data/*.geojson (offline-capable).'}
    </div>
  );
}
