import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";
import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";

/* =======================================================
   SIMPLE + PROFESSIONAL GIS COLOR SCALE
   ======================================================= */
function getZoneColor(potential: number) {
  const p = Math.max(0, Math.min(100, potential));

  if (p < 20)   return "rgba(255, 80, 80, 0.80)";     // strong red
  if (p < 40)   return "rgba(255, 140, 60, 0.80)";    // strong orange
  if (p < 60)   return "rgba(255, 200, 80, 0.80)";    // strong yellow
  if (p < 80)   return "rgba(140, 200, 90, 0.85)";    // strong light green

  return "rgba(90, 180, 90, 0.90)";                   // strong green
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
      <Polygon
        positions={regionPolygon}
        pathOptions={{ color: "#2a7f62", weight: 2 }}
      />

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
              fillOpacity: 0.55,
            }}
          />
        );
      })}
    </MapContainer>
  );
}