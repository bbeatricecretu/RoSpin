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

function getReliefColor(elev: number) {
  if (elev <= 200) return "#f7fcf5";
  if (elev <= 500) return "#c7e9c0";
  if (elev <= 1000) return "#74c476";
  if (elev <= 2000) return "#31a354";
  return "#006d2c";
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
  const gridLinesLayerRef = useRef<L.GeoJSON | null>(null);
  const gridSubstationsLayerRef = useRef<L.GeoJSON | null>(null);
  const [reliefData, setReliefData] = useState<any>(null);
  const reliefLayerRef = useRef<L.GeoJSON | null>(null);

  // ======================= GRID ==============================

  const [showGrid, setShowGrid] = useState(false);
  const [gridData, setGridData] = useState<any>(null);

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

  useEffect(() => {
    async function loadGrid() {
      try {
        const res = await fetch(`http://localhost:8000/api/regions/${region.id}/grid/`);
        const data = await res.json();

        if (!data || typeof data !== "object") return;

        setGridData(data);
      } catch (err) {
        console.error("GRID load error:", err);
      }
    }

    loadGrid();
  }, [region.id]);

  useEffect(() => {
    async function loadRelief() {
      try {
        const res = await fetch(
          `http://localhost:8000/api/regions/${region.id}/relief/`
        );
        const json = await res.json();

        if (!json || typeof json !== "object") {
          console.warn("Relief data invalid:", json);
          return;
        }

        setReliefData(json);
      } catch (err) {
        console.error("Relief load error:", err);
      }
    }

    loadRelief();
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

      <GridLayerInitializer
        gridData={gridData}
        gridLinesLayerRef={gridLinesLayerRef}
        gridSubstationsLayerRef={gridSubstationsLayerRef}
      />

      <ReliefLayerInitializer
        reliefData={reliefData}
        reliefLayerRef={reliefLayerRef}
      />

      <MapLayerControl
        waterLayerRef={waterLayerRef}
        gridLinesLayerRef={gridLinesLayerRef}
        gridSubstationsLayerRef={gridSubstationsLayerRef}
        reliefLayerRef={reliefLayerRef}
      />

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

function GridLayerInitializer({
  gridData,
  gridLinesLayerRef,
  gridSubstationsLayerRef
}: {
  gridData: any;
  gridLinesLayerRef: React.MutableRefObject<L.GeoJSON | null>;
  gridSubstationsLayerRef: React.MutableRefObject<L.GeoJSON | null>;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map || !gridData) return;

    try {
      // Remove previous layers
      if (gridLinesLayerRef.current) map.removeLayer(gridLinesLayerRef.current);
      if (gridSubstationsLayerRef.current) map.removeLayer(gridSubstationsLayerRef.current);

      // Create new line layer
      const lineLayer = L.geoJSON(gridData.lines, {
        style: {
          color: "#ff0000",
          weight: 2,
        }
      });

      // Create new substation layer
      const substLayer = L.geoJSON(gridData.substations, {
        pointToLayer: (_feature, latlng) =>
          L.circleMarker(latlng, {
            radius: 6,
            color: "#000",
            weight: 1,
            fillColor: "#ffff00",
            fillOpacity: 1,
          })
      });

      gridLinesLayerRef.current = lineLayer;
      gridSubstationsLayerRef.current = substLayer;

    } catch (err) {
      console.error("Grid layer creation failed:", err);
    }
  }, [map, gridData]);

  return null;
}

function ReliefLayerInitializer({
  reliefData,
  reliefLayerRef,
}: {
  reliefData: any;
  reliefLayerRef: React.MutableRefObject<L.GeoJSON | null>;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map || !reliefData) return;

    try {
      if (reliefLayerRef.current) {
        map.removeLayer(reliefLayerRef.current);
      }

      const layer = L.geoJSON(reliefData, {
        pointToLayer: (feature: any, latlng) => {
          const elev =
            feature?.properties?.DEM ??
            feature?.properties?.elevation ??
            0;
          const color = getReliefColor(elev);

          return L.circleMarker(latlng, {
            radius: 4,
            fillColor: color,
            color,
            weight: 0,
            fillOpacity: 0.8,
          });
        },
      });

      reliefLayerRef.current = layer;
    } catch (err) {
      console.error("Failed to create relief layer:", err);
    }
  }, [map, reliefData]);

  return null;
}


