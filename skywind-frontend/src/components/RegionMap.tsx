import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type{ RegionComputeResponseDTO } from "../dtos/RegionComputeResponseDTO";

type RegionMapProps = {
  region: RegionComputeResponseDTO;
  onZoneSelect: (zone: any) => void;
};

export default function RegionMap({ region, onZoneSelect }: RegionMapProps) {
  const { center, corners, zones } = region;

  const regionPolygon: [number, number][] = [
    [corners.A.lat, corners.A.lon],
    [corners.B.lat, corners.B.lon],
    [corners.C.lat, corners.C.lon],
    [corners.D.lat, corners.D.lon],
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

      <Polygon positions={regionPolygon} pathOptions={{ color: "lime", weight: 3 }} />

      {zones.map((z, i) => {
        const polygon: [number, number][] = [
          [z.A.lat, z.A.lon],
          [z.B.lat, z.B.lon],
          [z.C.lat, z.C.lon],
          [z.D.lat, z.D.lon],
        ];

        return (
          <Polygon
            key={i}
            positions={polygon}
            eventHandlers={{
              click: () => onZoneSelect(z),
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
