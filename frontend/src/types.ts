export type PriorityClass = 'Immediate' | 'Short-term' | 'Medium-term' | 'Monitor';
export type ZoneClass = 'Red' | 'Orange' | 'Yellow' | 'Green';
export type Provenance = 'OFFICIAL' | 'OPEN_DATA' | 'DERIVED' | 'EXPERT_SCREENED' | 'SYNTHETIC';

export interface ExplainFactor {
  factor: string;
  value: number;
  weight: number;
  contribution: number;
  note?: string;
}

export interface HabitationSummary {
  id: string;
  name: string;
  block: string;
  pop: number;
  lat: number;
  lon: number;
  h_ls: number;
  h_ff: number;
  h: number;
  v: number;
  p: number;
  priority: PriorityClass;
  pct_red: number;
  zone_class: ZoneClass;
  rec_site_id?: string;
  rec_score?: number;
  source?: Provenance;
  hazard_source?: string;
}

export interface HabitationDetail extends HabitationSummary {
  explain: ExplainFactor[];
  vuln_explain: ExplainFactor[];
  why_site: string[];
}

export interface SiteSummary {
  id: string;
  name: string;
  lat: number;
  lon: number;
  h_mean: number;
  slope_mean_deg: number;
  area_ha: number;
  capacity: number;
  capacity_available: number;
  existing_population: number;
  f_road: number;
  f_water: number;
  f_health: number;
  source?: Provenance;
  screening_note?: string;
}

export interface SiteRecommendation {
  site_id: string;
  site_name: string;
  score: number;
  safety: number;
  distance_km: number;
  road_access: number;
  healthcare_access: number;
  water_access: number;
  school_access: number;
  capacity: number;
  capacity_available: number;
  reasons: string[];
  explain?: ExplainFactor[];
  meets_capacity_threshold?: boolean;
}

export interface RecommendationComparison {
  score_delta: number;
  distance_delta_km: number;
  capacity_delta: number;
  notes: string[];
}

export interface RecommendationResponse {
  hab_id: string;
  hab_name: string;
  top: SiteRecommendation;
  runner_up?: SiteRecommendation;
  comparison?: RecommendationComparison;
}

export interface SourceMeta {
  layer: string;
  provenance: Provenance;
  url?: string;
  note?: string;
}

export interface Kpis {
  habitation_count: number;
  immediate_count: number;
  short_term_count: number;
  medium_term_count: number;
  monitor_count: number;
  site_count: number;
  red_zone_area_ha: number;
  district_area_ha: number;
}

export interface MetaResponse {
  district: string;
  generated_at: string;
  data_as_of?: string;
  pipeline_version?: string;
  model_version: string;
  weights_version: string;
  degraded_mode: boolean;
  synthetic_data_used: boolean;
  sources: SourceMeta[];
  limitations: string[];
  kpis: Kpis;
}

export interface AlertItem {
  id: string;
  habitation_id: string;
  habitation_name: string;
  severity: string;
  priority: PriorityClass;
  h: number;
  h_ff: number;
  pct_red: number;
  reasons: string[];
  action: string;
}

export interface AlertData {
  generated_at?: string;
  alert_count: number;
  alerts: AlertItem[];
}

export interface ScenarioResponse {
  factor: number;
  rainfall_factor: number;
  has_rainfall: boolean;
  h_min: number;
  h_max: number;
  h_mean: number;
  habitations: Array<{
    id: string;
    name: string;
    h_ls: number;
    h_ff: number;
    h: number;
    zone_class: ZoneClass;
  }>;
  note?: string;
}

export interface RefreshStatus {
  last_run?: string;
  success: boolean;
  duration_s?: number;
  pipeline_version: string;
}

export interface DistrictResponse {
  name: string;
  state: string;
  district_code: string;
  bbox: number[];
  geojson: GeoJSON.FeatureCollection;
  meta: MetaResponse;
}

export interface HealthResponse {
  status: string;
  district: string;
  model_version: string;
  data_loaded: boolean;
}

export interface LayerVisibility {
  district: boolean;
  red_zones: boolean;
  landslides: boolean;
  streams: boolean;
  habitations: boolean;
  sites: boolean;
}

export const DEFAULT_LAYERS: LayerVisibility = {
  district: true,
  red_zones: true,
  landslides: true,
  streams: true,
  habitations: true,
  sites: true,
};

export const PRIORITY_COLORS: Record<PriorityClass, string> = {
  Immediate: '#c0392b',
  'Short-term': '#e67e22',
  'Medium-term': '#f1c40f',
  Monitor: '#27ae60',
};

export const ZONE_COLORS: Record<ZoneClass, string> = {
  Red: '#c0392b',
  Orange: '#e67e22',
  Yellow: '#f1c40f',
  Green: '#27ae60',
};
