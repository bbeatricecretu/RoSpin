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
  const [reliefTileUrl, setReliefTileUrl] = useState<string | null>(null);
  const reliefLayerRef = useRef<L.TileLayer | null>(null);
  const [showAltitude, setShowAltitude] = useState(false);
  const altitudeMarkersRef = useRef<L.Marker[]>([]);

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

        if (json.error) {
          console.error("Relief generation error:", json.error);
          return;
        }

        if (json.tile_url) {
          setReliefTileUrl(json.tile_url);
        } else {
          console.warn("No tile_url in relief response:", json);
        }
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
        tileUrl={reliefTileUrl}
        reliefLayerRef={reliefLayerRef}
      />

      <MapLayerControl
        waterLayerRef={waterLayerRef}
        gridLinesLayerRef={gridLinesLayerRef}
        gridSubstationsLayerRef={gridSubstationsLayerRef}
        reliefLayerRef={reliefLayerRef}
        showAltitude={showAltitude}
        onAltitudeChange={setShowAltitude}
      />

      <AltitudeClickHandler
        enabled={showAltitude}
        altitudeMarkersRef={altitudeMarkersRef}
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
    if (!map || !gridData) {
      // Clean up if gridData is removed
      if (gridLinesLayerRef.current) {
        map?.removeLayer(gridLinesLayerRef.current);
        gridLinesLayerRef.current = null;
      }
      if (gridSubstationsLayerRef.current) {
        map?.removeLayer(gridSubstationsLayerRef.current);
        gridSubstationsLayerRef.current = null;
      }
      return;
    }

    try {
      // Remove previous layers
      if (gridLinesLayerRef.current) {
        map.removeLayer(gridLinesLayerRef.current);
        gridLinesLayerRef.current = null;
      }
      if (gridSubstationsLayerRef.current) {
        map.removeLayer(gridSubstationsLayerRef.current);
        gridSubstationsLayerRef.current = null;
      }

      // Create new line layer if lines data exists
      if (gridData.lines) {
        const lineLayer = L.geoJSON(gridData.lines, {
          style: {
            color: "#ff0000",
            weight: 2,
          }
        });
        gridLinesLayerRef.current = lineLayer;
      }

      // Create new substation layer if substations data exists
      if (gridData.substations) {
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
        gridSubstationsLayerRef.current = substLayer;
      }

    } catch (err) {
      console.error("Grid layer creation failed:", err);
    }
  }, [map, gridData, gridLinesLayerRef, gridSubstationsLayerRef]);

  return null;
}

function ReliefLayerInitializer({
  tileUrl,
  reliefLayerRef,
}: {
  tileUrl: string | null;
  reliefLayerRef: React.MutableRefObject<L.TileLayer | null>;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map || !tileUrl) {
      // Clean up if tileUrl is removed
      if (reliefLayerRef.current) {
        map?.removeLayer(reliefLayerRef.current);
        reliefLayerRef.current = null;
      }
      return;
    }

    try {
      // Remove previous layer if it exists
      if (reliefLayerRef.current) {
        map.removeLayer(reliefLayerRef.current);
        reliefLayerRef.current = null;
      }

      // Create new tile layer with the relief tiles
      // Google Earth Engine tiles may need authentication token
      const layer = L.tileLayer(tileUrl, {
        opacity: 0.8, // Higher opacity for increased contrast and visibility
        attribution: 'Elevation data: USGS SRTM',
        zIndex: 100, // Ensure it's above base map but below other layers
        tileSize: 256,
        maxZoom: 18,
      });

      reliefLayerRef.current = layer;
      // Note: Don't add to map here - MapLayerControl will handle visibility
    } catch (err) {
      console.error("Failed to create relief tile layer:", err);
    }
  }, [map, tileUrl, reliefLayerRef]);

  return null;
}

function AltitudeClickHandler({
  enabled,
  altitudeMarkersRef,
}: {
  enabled: boolean;
  altitudeMarkersRef: React.MutableRefObject<L.Marker[]>;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    const handleMapClick = async (e: L.LeafletMouseEvent) => {
      if (!enabled) return;

      const { lat, lng } = e.latlng;

      try {
        // Fetch elevation from backend
        const res = await fetch(
          `http://localhost:8000/api/elevation/?lat=${lat}&lon=${lng}`
        );
        const data = await res.json();

        if (data.error) {
          console.error("Elevation fetch error:", data.error);
          return;
        }

        const elevation = data.elevation;

        // Create a marker with elevation popup
        const marker = L.marker([lat, lng], {
          icon: L.divIcon({
            className: "elevation-marker",
            html: `<div style="
              background: rgba(255, 255, 255, 0.9);
              border: 2px solid #333;
              border-radius: 4px;
              padding: 4px 8px;
              font-weight: bold;
              font-size: 12px;
              box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            ">${elevation}m</div>`,
            iconSize: [60, 30],
            iconAnchor: [30, 15],
          }),
        });

        marker.bindPopup(
          `<div style="text-align: center;">
            <strong>Elevation</strong><br/>
            ${elevation} meters<br/>
            <small>Lat: ${lat.toFixed(6)}, Lon: ${lng.toFixed(6)}</small>
          </div>`
        ).openPopup();

        marker.addTo(map);
        altitudeMarkersRef.current.push(marker);
      } catch (err) {
        console.error("Failed to fetch elevation:", err);
      }
    };

    if (enabled) {
      map.on("click", handleMapClick);
    }

    return () => {
      map.off("click", handleMapClick);
    };
  }, [map, enabled, altitudeMarkersRef]);

  // Clean up markers when disabled
  useEffect(() => {
    if (!enabled && altitudeMarkersRef.current.length > 0) {
      altitudeMarkersRef.current.forEach((marker) => {
        map?.removeLayer(marker);
      });
      altitudeMarkersRef.current = [];
    }
  }, [enabled, map, altitudeMarkersRef]);

  return null;
}


