import { MapContainer, TileLayer, Polygon, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";
import "leaflet/dist/leaflet.css";

import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";
import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";

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
      <Polygon positions={regionPolygon} pathOptions={{ color: "lime", weight: 3 }} />

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
