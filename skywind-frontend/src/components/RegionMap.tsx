import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";
import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";
/* =======================================================
   CATEGORY-LOCKED GRADIENT COLOR FUNCTION
   Smooth nuance inside correct color band.
   ======================================================= */
function getZoneColor(potential: number) {
  const p = Math.max(0, Math.min(100, potential)); // clamp

  const ramp = (value: number, start: number, end: number) =>
    (value - start) / (end - start);

  // RED FAMILY (0–20)
  if (p < 20) {
    const t = ramp(p, 0, 20);
    return `hsl(0, 85%, ${35 + t * 20}%)`;
  }

  // ORANGE FAMILY (20–40)
  if (p < 40) {
    const t = ramp(p, 20, 40);
    return `hsl(${20 + t * 20}, 90%, ${40 + t * 20}%)`;
  }

  // YELLOW → YELLOW-GREEN (40–70)
  if (p < 70) {
    const t = ramp(p, 40, 70);
    return `hsl(${40 + t * 60}, 90%, ${45 + t * 20}%)`;
  }

  // GREEN FAMILY (70–100)
  const t = ramp(p, 70, 100);
  return `hsl(${100 + t * 40}, 85%, ${40 + t * 20}%)`;
}

type RegionMapProps = {
  region: RegionDetailsDTO;
  zones: ZoneDetailsDTO[];
  onZoneSelect: (zoneId: number) => void;
};

export default function RegionMap({ region, zones, onZoneSelect }: RegionMapProps) {
  const { center, A, B, C, D } = region;

  const regionPolygon: [number, number][] = [
    [A.lat, A.lon],
    [B.lat, B.lon],
    [C.lat, C.lon],
    [D.lat, D.lon],
  ];

  const mapCenter: [number, number] = [center.lat, center.lon];

  return (
    <MapContainer
      center={mapCenter}
      zoom={12}
      scrollWheelZoom={true}
      className="leaflet-container"
    >
      <TileLayer
        attribution="&copy; OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* REGION OUTLINE */}
      <Polygon positions={regionPolygon} pathOptions={{ color: "lime", weight: 3 }} />

      {/* ZONES */}
      {zones.map((z) => {
        const poly: [number, number][] = [
          [z.A.lat, z.A.lon],
          [z.B.lat, z.B.lon],
          [z.C.lat, z.C.lon],
          [z.D.lat, z.D.lon],
        ];

        return (
          <Polygon
            key={z.id}
            positions={poly}
            eventHandlers={{
              click: () => onZoneSelect(z.id),
            }}
            pathOptions={{
            color: "white",
            weight: 1,
            fillColor: getZoneColor(z.potential),
            fillOpacity: 0.85,
          }}

          />
        );
      })}
    </MapContainer>
  );
}
