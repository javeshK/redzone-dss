import { memo, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, useMap } from 'react-leaflet';
import L, { type PathOptions } from 'leaflet';
import { LayerVisibility, PRIORITY_COLORS, ZONE_COLORS, HabitationSummary, SiteSummary } from '../types';
import { getPriorityPlainLabel } from '../utils/plainLanguage';

const MAX_LANDSLIDE_FEATURES = 500;
const MAX_STREAM_FEATURES = 300;

interface MapViewProps {
  bbox?: number[];
  districtGeojson?: GeoJSON.FeatureCollection;
  redZones?: GeoJSON.FeatureCollection;
  landslides?: GeoJSON.FeatureCollection;
  streams?: GeoJSON.FeatureCollection;
  habitations?: HabitationSummary[];
  sites?: SiteSummary[];
  layers: LayerVisibility;
  onHabitationClick?: (id: string) => void;
  selectedHabitationId?: string | null;
  highlightedSiteId?: string | null;
  recommendedSiteId?: string | null;
  height?: string;
}

function thinCollection(
  fc: GeoJSON.FeatureCollection | undefined,
  max: number
): GeoJSON.FeatureCollection | undefined {
  if (!fc?.features?.length || fc.features.length <= max) return fc;
  const step = Math.ceil(fc.features.length / max);
  return {
    ...fc,
    features: fc.features.filter((_, i) => i % step === 0).slice(0, max),
  };
}

function FitBounds({ bbox }: { bbox: number[] }) {
  const map = useMap();
  useEffect(() => {
    if (bbox.length === 4) {
      map.fitBounds([[bbox[1], bbox[0]], [bbox[3], bbox[2]]], { padding: [20, 20] });
    }
  }, [map, bbox]);
  return null;
}

const zoneStyle = (feature?: GeoJSON.Feature) => {
  const cls = (feature?.properties as Record<string, string>)?.zone_class ?? 'Yellow';
  const color = ZONE_COLORS[cls as keyof typeof ZONE_COLORS] ?? '#f1c40f';
  return { fillColor: color, fillOpacity: 0.35, color, weight: 1.5 };
};

const streamStyle: PathOptions = { color: '#4a7c9b', weight: 2, opacity: 0.75 };

function MapView({
  bbox = [78.75, 30.05, 79.55, 30.75],
  districtGeojson,
  redZones,
  landslides,
  streams,
  habitations = [],
  sites = [],
  layers,
  onHabitationClick,
  selectedHabitationId,
  highlightedSiteId,
  recommendedSiteId,
  height = '100%',
}: MapViewProps) {
  const center: [number, number] = [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2];

  const thinLandslides = useMemo(
    () => (layers.landslides ? thinCollection(landslides, MAX_LANDSLIDE_FEATURES) : undefined),
    [landslides, layers.landslides]
  );
  const thinStreams = useMemo(
    () => (layers.streams ? thinCollection(streams, MAX_STREAM_FEATURES) : undefined),
    [streams, layers.streams]
  );

  const landslidePointLayer = useMemo(
    () => (_feature: GeoJSON.Feature, latlng: L.LatLng) =>
      L.circleMarker(latlng, {
        radius: 4,
        color: '#6b5344',
        fillColor: '#8b7355',
        fillOpacity: 0.75,
        weight: 1,
      }),
    []
  );

  return (
    <MapContainer
      center={center}
      zoom={10}
      style={{ height, width: '100%' }}
      scrollWheelZoom
      preferCanvas
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds bbox={bbox} />

      {layers.district && districtGeojson && (
        <GeoJSON
          data={districtGeojson}
          style={{ fillColor: 'transparent', color: '#2d5a3d', weight: 2, dashArray: '6 4' }}
        />
      )}

      {layers.red_zones && redZones && (
        <GeoJSON data={redZones} style={zoneStyle} />
      )}

      {thinStreams && (
        <GeoJSON data={thinStreams} style={streamStyle} />
      )}

      {thinLandslides && (
        <GeoJSON data={thinLandslides} pointToLayer={landslidePointLayer} />
      )}

      {layers.habitations && habitations.map((h) => (
        <CircleMarker
          key={h.id}
          center={[h.lat, h.lon]}
          radius={selectedHabitationId === h.id ? 10 : 7}
          pathOptions={{
            color: PRIORITY_COLORS[h.priority],
            fillColor: PRIORITY_COLORS[h.priority],
            fillOpacity: 0.9,
            weight: selectedHabitationId === h.id ? 3 : 1,
          }}
          eventHandlers={{
            click: () => onHabitationClick?.(h.id),
          }}
        >
          <Popup>
            <strong>{h.name}</strong><br />
            {getPriorityPlainLabel(h.priority)}<br />
            {h.pct_red.toFixed(0)}% in danger zone
          </Popup>
        </CircleMarker>
      ))}

      {layers.sites && sites.map((s) => {
        const isRecommended = recommendedSiteId === s.id;
        const isHighlighted = highlightedSiteId === s.id;
        return (
          <CircleMarker
            key={s.id}
            center={[s.lat, s.lon]}
            radius={isRecommended ? 12 : isHighlighted ? 10 : 8}
            pathOptions={{
              color: isRecommended ? '#2d5a3d' : '#4a7c9b',
              fillColor: isRecommended ? '#3d7352' : '#5b8fa8',
              fillOpacity: 0.85,
              weight: isRecommended || isHighlighted ? 3 : 2,
            }}
          >
            <Popup>
              <strong>{s.name}</strong>
              {isRecommended && <><br /><em>Recommended relocation center</em></>}
              <br />
              Space for {s.capacity_available} people
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}

export default memo(MapView);
