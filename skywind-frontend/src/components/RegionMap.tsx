"use client";

import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import { useEffect, useRef, useState } from "react";
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
  selectedZone: ZoneDetailsDTO | null;
  hoveredZoneId: number | null;
  onZoneSelect: (zoneId: number) => void;
  showWater: boolean;
  showGrid: boolean;
  showRelief: boolean;
  showWind: boolean;
  showAltitude: boolean;
  onAltitudeChange: (show: boolean) => void;
};

export default function RegionMap({
  region,
  zones,
  selectedZone,
  hoveredZoneId,
  onZoneSelect,
  showWater,
  showGrid,
  showRelief,
  showWind,
  showAltitude,
  onAltitudeChange
}: RegionMapProps) {
  const { center, A, B, C, D } = region;

  const [waterData, setWaterData] = useState<any>(null);
  const waterLayerRef = useRef<L.GeoJSON | null>(null);
  const gridLinesLayerRef = useRef<L.GeoJSON | null>(null);
  const gridSubstationsLayerRef = useRef<L.GeoJSON | null>(null);
  const [reliefTileUrl, setReliefTileUrl] = useState<string | null>(null);
  const reliefLayerRef = useRef<L.TileLayer | null>(null);

  // ======================= GRID ==============================

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
        visible={showWater}
      />

      <GridLayerInitializer
        gridData={gridData}
        gridLinesLayerRef={gridLinesLayerRef}
        gridSubstationsLayerRef={gridSubstationsLayerRef}
        visible={showGrid}
      />

      <ReliefLayerInitializer
        tileUrl={reliefTileUrl}
        reliefLayerRef={reliefLayerRef}
        visible={showRelief}
      />

      <WindLayer
        zones={zones}
        visible={showWind}
      />

      <AltitudeHoverHandler
        enabled={showAltitude}
        regionPolygon={regionPolygon as [number, number][]}
      />

      {/* REGION BORDER */}
      {regionPolygon.length === 4 && (
        <Polygon positions={regionPolygon as any} pathOptions={{ color: "#2a7f62", weight: 2 }} />
      )}

      {/* ZONES */}
      <ZonePolygons 
        zones={zones}
        selectedZone={selectedZone}
        hoveredZoneId={hoveredZoneId}
        onZoneSelect={onZoneSelect}
      />
    </MapContainer>
  );
}

/* ===================== ZONE POLYGONS COMPONENT ===================== */

function ZonePolygons({
  zones,
  selectedZone,
  hoveredZoneId,
  onZoneSelect,
}: {
  zones: ZoneDetailsDTO[];
  selectedZone: ZoneDetailsDTO | null;
  hoveredZoneId: number | null;
  onZoneSelect: (zoneId: number) => void;
}) {
  const map = useMap();
  const polygonRefs = useRef<{ [key: number]: L.Polygon }>({});

  // Bring hovered zone to front
  useEffect(() => {
    if (hoveredZoneId && polygonRefs.current[hoveredZoneId]) {
      polygonRefs.current[hoveredZoneId].bringToFront();
    }
  }, [hoveredZoneId]);

  return (
    <>
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

        const isSelected = selectedZone?.id === z.id;
        const isHovered = hoveredZoneId === z.id;

        return (
          <Polygon
            key={z.id}
            ref={(ref) => {
              if (ref) {
                polygonRefs.current[z.id] = ref as any;
              }
            }}
            positions={poly as any}
            eventHandlers={{ 
              click: () => onZoneSelect(z.id)
            }}
            pathOptions={{
              color: isHovered ? "#000000" : isSelected ? "#FFD700" : "white",
              weight: isHovered ? 5 : isSelected ? 3 : 1,
              fillColor: getZoneColor(z.potential),
              fillOpacity: isHovered ? 0.85 : isSelected ? 0.75 : 0.55,
              lineCap: "butt",
              lineJoin: "miter",
            }}
          />
        );
      })}
    </>
  );
}

/* ===================== WATER LAYER INIT ===================== */

function WaterLayerInitializer({
  waterData,
  waterLayerRef,
  visible,
}: {
  waterData: any;
  waterLayerRef: React.MutableRefObject<L.GeoJSON | null>;
  visible: boolean;
}) {
  const map = useMap();

  // Create layer
  useEffect(() => {
    if (!map || !waterData) return;

    if (waterLayerRef.current) {
      map.removeLayer(waterLayerRef.current);
    }

    try {
      const layer = L.geoJSON(waterData, {
        style: { color: "#1e90ff", weight: 2 },
      });

      waterLayerRef.current = layer;
      if (visible) layer.addTo(map);
    } catch (err) {
      console.error("Failed to create water layer:", err);
    }
  }, [map, waterData]);

  // Toggle visibility
  useEffect(() => {
    const layer = waterLayerRef.current;
    if (!map || !layer) return;

    if (visible) {
      if (!map.hasLayer(layer)) map.addLayer(layer);
    } else {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    }
  }, [map, visible, waterData]);

  return null;
}

function GridLayerInitializer({
  gridData,
  gridLinesLayerRef,
  gridSubstationsLayerRef,
  visible,
}: {
  gridData: any;
  gridLinesLayerRef: React.MutableRefObject<L.GeoJSON | null>;
  gridSubstationsLayerRef: React.MutableRefObject<L.GeoJSON | null>;
  visible: boolean;
}) {
  const map = useMap();

  // Create layers
  useEffect(() => {
    if (!map || !gridData) {
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
      if (gridLinesLayerRef.current) map.removeLayer(gridLinesLayerRef.current);
      if (gridSubstationsLayerRef.current) map.removeLayer(gridSubstationsLayerRef.current);

      if (gridData.lines) {
        const lineLayer = L.geoJSON(gridData.lines, {
          style: { color: "#ff0000", weight: 2 }
        });
        gridLinesLayerRef.current = lineLayer;
        if (visible) lineLayer.addTo(map);
      }

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
        if (visible) substLayer.addTo(map);
      }

    } catch (err) {
      console.error("Grid layer creation failed:", err);
    }
  }, [map, gridData]);

  // Toggle visibility
  useEffect(() => {
    if (!map) return;
    const lines = gridLinesLayerRef.current;
    const subst = gridSubstationsLayerRef.current;

    if (visible) {
      if (lines && !map.hasLayer(lines)) map.addLayer(lines);
      if (subst && !map.hasLayer(subst)) map.addLayer(subst);
    } else {
      if (lines && map.hasLayer(lines)) map.removeLayer(lines);
      if (subst && map.hasLayer(subst)) map.removeLayer(subst);
    }
  }, [map, visible, gridData]);

  return null;
}

function ReliefLayerInitializer({
  tileUrl,
  reliefLayerRef,
  visible,
}: {
  tileUrl: string | null;
  reliefLayerRef: React.MutableRefObject<L.TileLayer | null>;
  visible: boolean;
}) {
  const map = useMap();

  // Create layer
  useEffect(() => {
    if (!map || !tileUrl) {
      if (reliefLayerRef.current) {
        map?.removeLayer(reliefLayerRef.current);
        reliefLayerRef.current = null;
      }
      return;
    }

    try {
      if (reliefLayerRef.current) {
        map.removeLayer(reliefLayerRef.current);
      }

      const layer = L.tileLayer(tileUrl, {
        opacity: 0.8,
        attribution: 'Elevation data: USGS SRTM',
        zIndex: 100,
        tileSize: 256,
        maxZoom: 18,
      });

      reliefLayerRef.current = layer;
      if (visible) layer.addTo(map);
    } catch (err) {
      console.error("Failed to create relief tile layer:", err);
    }
  }, [map, tileUrl]);

  // Toggle visibility
  useEffect(() => {
    const layer = reliefLayerRef.current;
    if (!map || !layer) return;

    if (visible) {
      if (!map.hasLayer(layer)) map.addLayer(layer);
    } else {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    }
  }, [map, visible, tileUrl]);

  return null;
}

function isPointInPolygon(point: [number, number], vs: [number, number][]) {
  const x = point[0], y = point[1];
  let inside = false;
  for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
    const xi = vs[i][0], yi = vs[i][1];
    const xj = vs[j][0], yj = vs[j][1];
    const intersect = ((yi > y) !== (yj > y))
        && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

function AltitudeHoverHandler({
  enabled,
  regionPolygon,
}: {
  enabled: boolean;
  regionPolygon: [number, number][];
}) {
  const map = useMap();
  const tooltipRef = useRef<L.Tooltip | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!map) return;

    // Create tooltip once
    if (!tooltipRef.current) {
      tooltipRef.current = L.tooltip({
        permanent: true,
        direction: 'top',
        className: 'altitude-tooltip',
        offset: [0, -10],
        opacity: 0.9,
      });
    }

    const handleMouseMove = (e: L.LeafletMouseEvent) => {
      if (!enabled) return;

      const { lat, lng } = e.latlng;
      
      // Check if point is inside region
      if (!isPointInPolygon([lat, lng], regionPolygon)) {
        // If outside, hide tooltip
        if (tooltipRef.current && map.hasLayer(tooltipRef.current)) {
          map.removeLayer(tooltipRef.current);
        }
        return;
      }

      const tooltip = tooltipRef.current;

      if (!tooltip) return;

      // Update position immediately
      tooltip.setLatLng([lat, lng]);
      
      // If not added to map, add it
      if (!map.hasLayer(tooltip)) {
        tooltip.addTo(map);
        tooltip.setContent("Loading...");
      }

      // Debounce the API call
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(async () => {
        try {
          const res = await fetch(
            `http://localhost:8000/api/elevation/?lat=${lat}&lon=${lng}`
          );
          const data = await res.json();

          if (data.error) {
            tooltip.setContent("Error");
          } else {
            tooltip.setContent(`<b>${data.elevation} m</b>`);
          }
        } catch (err) {
          console.error("Elevation fetch error:", err);
          tooltip.setContent("Error");
        }
      }, 150); // 150ms debounce
    };

    const handleMouseOut = () => {
      if (tooltipRef.current && map.hasLayer(tooltipRef.current)) {
        map.removeLayer(tooltipRef.current);
      }
    };

    if (enabled) {
      map.on("mousemove", handleMouseMove);
      map.on("mouseout", handleMouseOut);
    } else {
      // Cleanup if disabled
      handleMouseOut();
    }

    return () => {
      map.off("mousemove", handleMouseMove);
      map.off("mouseout", handleMouseOut);
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      handleMouseOut();
    };
  }, [map, enabled, regionPolygon]);

  return null;
}

function WindLayer({
  zones,
  visible,
}: {
  zones: ZoneDetailsDTO[];
  visible: boolean;
}) {
  const map = useMap();
  const markersRef = useRef<L.Marker[]>([]);
  const [zoom, setZoom] = useState<number>(12);

  // Track zoom level
  useEffect(() => {
    if (!map) return;
    setZoom(map.getZoom());
    
    const onZoom = () => {
      setZoom(map.getZoom());
    };
    
    map.on('zoomend', onZoom);
    return () => {
      map.off('zoomend', onZoom);
    };
  }, [map]);

  useEffect(() => {
    if (!map) return;

    // Clear existing markers
    markersRef.current.forEach((m) => map.removeLayer(m));
    markersRef.current = [];

    if (!visible || zones.length === 0) return;

    // Calculate arrow size based on zoom
    // Base size 18px at zoom 12
    const scale = Math.pow(1.1, zoom - 12); 
    const size = Math.max(10, Math.min(50, 18 * scale));

    // 1. Precompute vectors for all zone centers
    const controlPoints = zones.map((z) => {
      const centerLat = (z.A.lat + z.B.lat + z.C.lat + z.D.lat) / 4;
      const centerLon = (z.A.lon + z.B.lon + z.C.lon + z.D.lon) / 4;
      
      // Meteorological Wind Direction (0=N, 90=E) is "FROM".
      // We want to show "TO" (Flow).
      // Flow direction = wind_direction + 180.
      // Math Angle (0=E, 90=N) = 90 - FlowDirection
      const flowDir = z.wind_direction + 180;
      const mathAngleDeg = 90 - flowDir;
      const rad = (mathAngleDeg * Math.PI) / 180;
      
      const u = z.avg_wind_speed * Math.cos(rad);
      const v = z.avg_wind_speed * Math.sin(rad);

      return { lat: centerLat, lon: centerLon, u, v };
    });

    zones.forEach((z) => {
      // 4x4 grid per zone for denser field like the reference image
      const steps = 4; 
      
      for (let i = 0; i < steps; i++) {
        for (let j = 0; j < steps; j++) {
          const u_pos = (i + 0.5) / steps; 
          const v_pos = (j + 0.5) / steps;

          // Interpolate position within the zone
          const latTop = z.A.lat + (z.B.lat - z.A.lat) * u_pos;
          const lonTop = z.A.lon + (z.B.lon - z.A.lon) * u_pos;
          const latBot = z.D.lat + (z.C.lat - z.D.lat) * u_pos;
          const lonBot = z.D.lon + (z.C.lon - z.D.lon) * u_pos;
          
          const lat = latTop + (latBot - latTop) * v_pos;
          const lon = lonTop + (lonBot - lonTop) * v_pos;

          // 2. Inverse Distance Weighting (IDW) Interpolation
          let sumU = 0;
          let sumV = 0;
          let sumW = 0;

          for (const cp of controlPoints) {
            const d2 = (lat - cp.lat) ** 2 + (lon - cp.lon) ** 2;
            
            // Weight = 1 / distance^p
            // p=2 (d2) is standard but decays fast, making local zone dominate.
            // p=1.2 makes the field much smoother and influenced by neighbors.
            const dist = Math.sqrt(d2);
            const w = 1 / (Math.pow(dist, 1.2) + 1e-9);
            
            sumU += cp.u * w;
            sumV += cp.v * w;
            sumW += w;
          }

          const finalU = sumU / sumW;
          const finalV = sumV / sumW;

          // Convert back to angle
          const angleRad = Math.atan2(finalV, finalU);
          const angleDeg = (angleRad * 180) / Math.PI;
          
          // Rotation for CSS (0=North, 90=East)
          // Rotation = 90 - MathAngle
          const rotation = 90 - angleDeg;

          // Create arrow icon
          // Simple line arrow style (vector field style)
          const icon = L.divIcon({
            className: 'wind-arrow-icon',
            html: `<div style="transform: rotate(${rotation}deg); width: ${size}px; height: ${size}px; display: flex; justify-content: center; align-items: center;">
              <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 21V3M12 3L5 10M12 3L19 10" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>`,
            iconSize: [size, size],
            iconAnchor: [size/2, size/2],
          });

          const marker = L.marker([lat, lon], {
            icon: icon,
            interactive: false,
          });

          marker.addTo(map);
          markersRef.current.push(marker);
        }
      }
    });

  }, [map, zones, visible, zoom]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      markersRef.current.forEach((m) => map?.removeLayer(m));
    };
  }, [map]);

  return null;
}


