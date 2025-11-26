import { MapContainer, TileLayer, Polygon, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";
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

/* =======================================================
   CATEGORY-LOCKED GRADIENT COLOR FUNCTION
   Smooth nuance inside correct color band.
   ======================================================= */
function getZoneColor(potential: number) {
  const p = Math.max(0, Math.min(100, potential)); // clamp

  // Red category: 0–20
  if (p < 20) {
    const t = p / 20; // 0..1
    return `hsl(${0 + t * 10}, 90%, ${40 + t * 10}%)`;
    // shades of red → slightly lighter red
  }

  // Orange category: 20–40
  if (p < 40) {
    const t = (p - 20) / 20;
    return `hsl(${20 + t * 20}, 90%, ${45 + t * 10}%)`;
    // dark orange → bright orange
  }

  // Yellow-green category: 40–70
  if (p < 70) {
    const t = (p - 40) / 30;
    return `hsl(${40 + t * 60}, 85%, ${50 + t * 10}%)`;
    // orange-yellow → yellow → yellow-green
  }

  // Green category: 70–100
  const t = (p - 70) / 30;
  return `hsl(${100 + t * 40}, 85%, ${45 + t * 10}%)`;
  // green → brighter lime green
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
      zoom={11}
      scrollWheelZoom={true}
      className="leaflet-container"
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* REGION OUTLINE */}
      <Polygon
        positions={regionPolygon}
        pathOptions={{
          color: "#00b4d8",
          weight: 3,
          fillOpacity: 0,
        }}
      />

      {/* ZONES */}
      {zones.map((z) => {
        const poly: [number, number][] = [
          [z.A.lat, z.A.lon],
          [z.B.lat, z.B.lon],
          [z.C.lat, z.C.lon],
          [z.D.lat, z.D.lon],
        ];

        const zoneColor = getZoneColor(i, zones.length);

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
              color: "#ffffff",
              weight: 1,
              fillColor: zoneColor,
              fillOpacity: 0.4,
            }}
          >
            <Popup>
              <div style={{ minWidth: "150px" }}>
                <strong>Zone {z.index}</strong>
                <br />
                <small>Click to view details</small>
              </div>
            </Popup>
          </Polygon>
        );
      })}
    </MapContainer>
  );
}
