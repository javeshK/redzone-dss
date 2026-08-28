import { useApp } from '../context/AppContext';
import SourceBadge from './SourceBadge';

export default function GlobalBanners() {
  const { dataSource, meta } = useApp();

  return (
    <div className="global-banners">
      {dataSource === 'loading' && (
        <div className="banner banner-info">Connecting to data services…</div>
      )}
      {dataSource === 'static' && (
        <div className="banner banner-warning">
          Static fallback mode — serving precomputed artifacts from /data/* (offline-capable).
        </div>
      )}
      {dataSource === 'api' && (
        <div className="banner banner-info">
          API mode — live read-only access to precomputed artifacts in out/.
        </div>
      )}
      {meta?.synthetic_data_used && (
        <div className="banner banner-warning">
          <SourceBadge provenance="SYNTHETIC" label="Synthetic / fallback data in use" />
          <span className="banner-text">
            Some layers use synthetic or degraded inputs. See Overview for source provenance.
          </span>
        </div>
      )}
      {meta?.degraded_mode && (
        <div className="banner banner-warning">
          Degraded hazard mode — rainfall proxy active; weights renormalized per MCA contract.
        </div>
      )}
    </div>
  );
}
