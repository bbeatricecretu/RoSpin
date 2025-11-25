import { MapContainer, TileLayer, Polygon, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";
import "leaflet/dist/leaflet.css";
import type { RegionComputeResponseDTO } from "../dtos/RegionComputeResponseDTO";

type RegionMapProps = {
  region: RegionComputeResponseDTO;
  onZoneSelect: (zone: any) => void;
};

// Helper function to get color based on zone index (for visualization)
// In a real app, this would be based on actual potential/rating data
function getZoneColor(index: number, totalZones: number): string {
  // Create a gradient from blue (low) to green (high) based on position
  const ratio = index / totalZones;
  
  if (ratio < 0.3) {
    return "#3b82f6"; // Blue - lower potential
  } else if (ratio < 0.6) {
    return "#10b981"; // Green - medium potential
  } else {
    return "#f59e0b"; // Orange - higher potential
  }
}

// Component to fit map bounds to region
function FitBounds({ corners }: { corners: RegionComputeResponseDTO["corners"] }) {
  const map = useMap();
  
  useEffect(() => {
    const bounds: [number, number][] = [
      [corners.A.lat, corners.A.lon],
      [corners.B.lat, corners.B.lon],
      [corners.C.lat, corners.C.lon],
      [corners.D.lat, corners.D.lon],
    ];
    
    map.fitBounds(bounds, { padding: [50, 50] });
  }, [map, corners]);
  
  return null;
}

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
      zoom={11}
      scrollWheelZoom={true}
      className="leaflet-container"
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <FitBounds corners={corners} />

      {/* Region Boundary */}
      <Polygon
        positions={regionPolygon}
        pathOptions={{
          color: "#3b82f6",
          weight: 3,
          fillColor: "transparent",
          fillOpacity: 0,
          dashArray: "10, 5",
        }}
      >
        <Popup>
          <div style={{ textAlign: "center" }}>
            <strong>Region Boundary</strong>
            <br />
            {zones.length} zones
          </div>
        </Popup>
      </Polygon>

      {/* Zone Polygons */}
      {zones.map((z, i) => {
        const polygon: [number, number][] = [
          [z.A.lat, z.A.lon],
          [z.B.lat, z.B.lon],
          [z.C.lat, z.C.lon],
          [z.D.lat, z.D.lon],
        ];

        const zoneColor = getZoneColor(i, zones.length);

        return (
          <Polygon
            key={i}
            positions={polygon}
            eventHandlers={{
              click: () => onZoneSelect(z),
              mouseover: (e) => {
                const layer = e.target;
                layer.setStyle({
                  weight: 3,
                  fillOpacity: 0.6,
                });
              },
              mouseout: (e) => {
                const layer = e.target;
                layer.setStyle({
                  weight: 1,
                  fillOpacity: 0.4,
                });
              },
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
