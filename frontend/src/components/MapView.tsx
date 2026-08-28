import { useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, Polyline, useMap } from 'react-leaflet';
import { LayerVisibility, PRIORITY_COLORS, ZONE_COLORS, HabitationSummary, SiteSummary } from '../types';

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

function extractPoints(geometry: GeoJSON.Geometry): [number, number][] {
  if (geometry.type === 'Point') {
    const [lon, lat] = geometry.coordinates;
    return [[lat, lon]];
  }
  if (geometry.type === 'MultiPoint') {
    return geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  }
  return [];
}

function extractLineStrings(geometry: GeoJSON.Geometry): [number, number][][] {
  if (geometry.type === 'LineString') {
    return [geometry.coordinates.map(([lon, lat]) => [lat, lon])];
  }
  if (geometry.type === 'MultiLineString') {
    return geometry.coordinates.map((line) => line.map(([lon, lat]) => [lat, lon]));
  }
  return [];
}

export default function MapView({
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

  return (
    <MapContainer center={center} zoom={10} style={{ height, width: '100%' }} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds bbox={bbox} />

      {layers.district && districtGeojson && (
        <GeoJSON
          data={districtGeojson}
          style={{ fillColor: 'transparent', color: '#2c3e50', weight: 2, dashArray: '6 4' }}
        />
      )}

      {layers.red_zones && redZones && (
        <GeoJSON data={redZones} style={zoneStyle} />
      )}

      {layers.streams && streams && streams.features.flatMap((f, i) =>
        extractLineStrings(f.geometry as GeoJSON.Geometry).map((positions, j) => (
          <Polyline
            key={`stream-${i}-${j}`}
            positions={positions}
            pathOptions={{ color: '#2980b9', weight: 2, opacity: 0.8 }}
          />
        ))
      )}

      {layers.landslides && landslides?.features.flatMap((f, i) =>
        extractPoints(f.geometry as GeoJSON.Geometry).map((center, j) => (
          <CircleMarker
            key={`ls-${i}-${j}`}
            center={center}
            radius={5}
            pathOptions={{ color: '#8e44ad', fillColor: '#8e44ad', fillOpacity: 0.8 }}
          >
            <Popup>Landslide inventory point</Popup>
          </CircleMarker>
        ))
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
            Priority: {h.priority}<br />
            H: {h.h.toFixed(2)} | V: {h.v.toFixed(2)}
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
              color: isRecommended ? '#c0392b' : '#16a085',
              fillColor: isRecommended ? '#e74c3c' : '#1abc9c',
              fillOpacity: 0.85,
              weight: isRecommended || isHighlighted ? 3 : 2,
            }}
          >
            <Popup>
              <strong>{s.name}</strong>
              {isRecommended && <><br /><em>Recommended site</em></>}
              <br />
              H: {s.h_mean.toFixed(2)}<br />
              Capacity available: {s.capacity_available}
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
