"use client";

import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import { useEffect, useRef, useState } from "react";
import { MapLayerControl } from "./map/MapLayerControl";
import { GeoJSON, useMap } from "react-leaflet";
import L from "leaflet";

import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";
import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";

/* ======================= COLOR SCALE ======================= */
function getZoneColor(p: number) {
  p = Math.max(0, Math.min(100, p));
  if (p < 20) return "rgba(255,80,80,0.8)";
  if (p < 40) return "rgba(255,140,60,0.8)";
  if (p < 60) return "rgba(255,200,80,0.8)";
  if (p < 80) return "rgba(140,200,90,0.85)";
  return "rgba(90,180,90,0.9)";
}

type RegionMapProps = {
  region: RegionDetailsDTO;
  zones: ZoneDetailsDTO[];
  onZoneSelect: (zoneId: number) => void;
};

export default function RegionMap({ region, zones, onZoneSelect }: RegionMapProps) {
  const { center, A, B, C, D } = region;

  const [waterData, setWaterData] = useState<any>(null);
  const waterLayerRef = useRef<L.GeoJSON | null>(null);

  /* ======================= LOAD WATER ======================= */
  useEffect(() => {
    async function loadWater() {
      try {
        const res = await fetch(
          `http://localhost:8000/api/regions/${region.id}/water/`
        );
        const json = await res.json();

        // Guard against invalid data
        if (!json || typeof json !== "object") {
          console.warn("Water data invalid:", json);
          return;
        }

        setWaterData(json);
      } catch (err) {
        console.error("Failed loading water", err);
      }
    }

    loadWater();
  }, [region.id]);

  const regionPolygon = [
    [A?.lat, A?.lon],
    [B?.lat, B?.lon],
    [C?.lat, C?.lon],
    [D?.lat, D?.lon],
  ].filter((p) => p[0] && p[1]); // Remove invalid coords

  const mapCenter: [number, number] = [center.lat, center.lon];

  return (
    <MapContainer
      center={mapCenter}
      zoom={12}
      scrollWheelZoom={true}
      className="leaflet-container"
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      <WaterLayerInitializer
        waterData={waterData}
        waterLayerRef={waterLayerRef}
      />

      <MapLayerControl waterLayerRef={waterLayerRef} />

      {/* REGION BORDER */}
      {regionPolygon.length === 4 && (
        <Polygon positions={regionPolygon as any} pathOptions={{ color: "#2a7f62", weight: 2 }} />
      )}

      {/* ZONES */}
      {zones.map((z) => {
        const poly = [
          [z.A?.lat, z.A?.lon],
          [z.B?.lat, z.B?.lon],
          [z.C?.lat, z.C?.lon],
          [z.D?.lat, z.D?.lon],
        ].filter((p) => p[0] && p[1]);

        if (poly.length !== 4) {
          console.warn("Invalid zone polygon", z.id, poly);
          return null;
        }

        return (
          <Polygon
            key={z.id}
            positions={poly as any}
            eventHandlers={{ click: () => onZoneSelect(z.id) }}
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

/* ===================== WATER LAYER INIT ===================== */

function WaterLayerInitializer({
  waterData,
  waterLayerRef,
}: {
  waterData: any;
  waterLayerRef: React.MutableRefObject<L.GeoJSON | null>;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map || !waterData) return;

    try {
      if (waterLayerRef.current) {
        map.removeLayer(waterLayerRef.current);
      }

      const layer = L.geoJSON(waterData, {
        style: { color: "#1e90ff", weight: 2 },
      });

      waterLayerRef.current = layer;
    } catch (err) {
      console.error("Failed to create water layer:", err);
    }
  }, [map, waterData]);

  return null;
}
