import type {
  DistrictResponse,
  HabitationDetail,
  HabitationSummary,
  HealthResponse,
  MetaResponse,
  RecommendationResponse,
  SiteSummary,
} from '../types';

const API_BASE = '/api';
const STATIC_BASE = '/data';

let apiAvailable: boolean | null = null;

async function checkApi(): Promise<boolean> {
  if (apiAvailable !== null) return apiAvailable;
  try {
    const r = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
    apiAvailable = r.ok;
  } catch {
    apiAvailable = false;
  }
  return apiAvailable;
}

async function fetchWithFallback<T>(apiPath: string, staticPath: string): Promise<T> {
  const useApi = await checkApi();
  if (useApi) {
    try {
      const r = await fetch(`${API_BASE}${apiPath}`);
      if (r.ok) return r.json();
    } catch {
      apiAvailable = false;
    }
  }
  const r = await fetch(`${STATIC_BASE}${staticPath}`);
  if (!r.ok) throw new Error(`Failed to load ${staticPath}`);
  return r.json();
}

export async function getHealth(): Promise<HealthResponse> {
  return fetchWithFallback<HealthResponse | MetaResponse>('/health', '/meta.json').then(
    (data) => {
      if ('status' in data) return data as HealthResponse;
      const meta = data as MetaResponse;
      return {
        status: 'ok',
        district: meta.district,
        model_version: meta.model_version,
        data_loaded: true,
      };
    }
  );
}

export async function getDistrict(): Promise<DistrictResponse> {
  const useApi = await checkApi();
  if (useApi) {
    try {
      const r = await fetch(`${API_BASE}/district`);
      if (r.ok) return r.json();
    } catch {
      apiAvailable = false;
    }
  }
  const [district, meta] = await Promise.all([
    fetch(`${STATIC_BASE}/district.geojson`).then((r) => r.json()),
    fetch(`${STATIC_BASE}/meta.json`).then((r) => r.json()),
  ]);
  const props = district.features?.[0]?.properties ?? {};
  const coords = district.features?.[0]?.geometry?.coordinates?.[0] ?? [];
  const lons = coords.map((c: number[]) => c[0]);
  const lats = coords.map((c: number[]) => c[1]);
  return {
    name: props.name ?? 'Rudraprayag',
    state: props.state ?? 'Uttarakhand',
    district_code: props.district_code ?? 'UT_RUD',
    bbox: lons.length
      ? [Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)]
      : [78.75, 30.05, 79.55, 30.75],
    geojson: district,
    meta,
  };
}

export async function getHabitations(): Promise<HabitationSummary[]> {
  const useApi = await checkApi();
  if (useApi) {
    try {
      const r = await fetch(`${API_BASE}/habitations`);
      if (r.ok) return r.json();
    } catch {
      apiAvailable = false;
    }
  }
  const fc = await fetch(`${STATIC_BASE}/habitations.geojson`).then((r) => r.json());
  return fc.features.map((f: GeoJSON.Feature) => {
    const p = f.properties as Record<string, unknown>;
    const [lon, lat] = (f.geometry as GeoJSON.Point).coordinates;
    return {
      id: p.id,
      name: p.name,
      block: p.block,
      pop: p.pop,
      lat,
      lon,
      h_ls: p.h_ls,
      h_ff: p.h_ff,
      h: p.h,
      v: p.v,
      p: p.p,
      priority: p.priority,
      pct_red: p.pct_red,
      zone_class: p.zone_class,
      rec_site_id: p.rec_site_id,
      rec_score: p.rec_score,
      source: p.source,
      hazard_source: p.hazard_source,
    };
  }) as HabitationSummary[];
}

export async function getHabitation(id: string): Promise<HabitationDetail> {
  const useApi = await checkApi();
  if (useApi) {
    try {
      const r = await fetch(`${API_BASE}/habitations/${id}`);
      if (r.ok) return r.json();
    } catch {
      apiAvailable = false;
    }
  }
  const fc = await fetch(`${STATIC_BASE}/habitations.geojson`).then((r) => r.json());
  const feat = fc.features.find(
    (f: GeoJSON.Feature) => (f.properties as Record<string, unknown>).id === id
  );
  if (!feat) throw new Error(`Habitation ${id} not found`);
  const p = feat.properties as Record<string, unknown>;
  const [lon, lat] = (feat.geometry as GeoJSON.Point).coordinates;
  return {
    id: p.id as string,
    name: p.name as string,
    block: p.block as string,
    pop: p.pop as number,
    lat,
    lon,
    h_ls: p.h_ls as number,
    h_ff: p.h_ff as number,
    h: p.h as number,
    v: p.v as number,
    p: p.p as number,
    priority: p.priority as HabitationDetail['priority'],
    pct_red: p.pct_red as number,
    zone_class: p.zone_class as HabitationDetail['zone_class'],
      rec_site_id: p.rec_site_id as string | undefined,
      rec_score: p.rec_score as number | undefined,
      source: p.source as HabitationDetail['source'],
      hazard_source: p.hazard_source as string | undefined,
      explain: (p.explain as HabitationDetail['explain']) ?? [],
      vuln_explain: (p.vuln_explain as HabitationDetail['vuln_explain']) ?? [],
      why_site: (p.why_site as string[]) ?? [],
  };
}

export async function getLayer(name: string): Promise<GeoJSON.FeatureCollection> {
  return fetchWithFallback<GeoJSON.FeatureCollection>(`/layers/${name}`, `/${name}.geojson`);
}

export async function getSites(): Promise<SiteSummary[]> {
  const useApi = await checkApi();
  if (useApi) {
    try {
      const r = await fetch(`${API_BASE}/sites`);
      if (r.ok) return r.json();
    } catch {
      apiAvailable = false;
    }
  }
  const fc = await fetch(`${STATIC_BASE}/sites.geojson`).then((r) => r.json());
  return fc.features.map((f: GeoJSON.Feature) => {
    const p = f.properties as Record<string, unknown>;
    const [lon, lat] = (f.geometry as GeoJSON.Point).coordinates;
    return {
      id: p.id,
      name: p.name,
      lat,
      lon,
      h_mean: p.h_mean,
      slope_mean_deg: p.slope_mean_deg,
      area_ha: p.area_ha,
      capacity: p.capacity,
      capacity_available: p.capacity_available,
      existing_population: p.existing_population,
      f_road: p.f_road,
      f_water: p.f_water,
      f_health: p.f_health,
      source: p.source,
      screening_note: p.screening_note,
    };
  }) as SiteSummary[];
}

export async function getRecommendation(habId: string): Promise<RecommendationResponse> {
  const useApi = await checkApi();
  if (useApi) {
    try {
      const r = await fetch(`${API_BASE}/recommend/${habId}`);
      if (r.ok) return r.json();
    } catch {
      apiAvailable = false;
    }
  }
  const recs = await fetch(`${STATIC_BASE}/recommendations.json`).then((r) => r.json());
  const rec = recs.recommendations[habId];
  if (!rec) throw new Error(`Recommendation for ${habId} not found`);
  return rec as RecommendationResponse;
}

export function isUsingApi(): boolean | null {
  return apiAvailable;
}

export function resetApiCheck() {
  apiAvailable = null;
}
