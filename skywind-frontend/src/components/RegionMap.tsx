import { MapContainer, TileLayer, Polygon } from "react-leaflet";
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
              fillColor: "rgba(0,255,0,0.3)",
              fillOpacity: 0.3,
            }}
          />
        );
      })}
    </MapContainer>
  );
}
