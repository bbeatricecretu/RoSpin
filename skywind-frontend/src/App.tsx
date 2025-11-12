import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  GeoJSON,
  useMap,
} from "react-leaflet";
import L from "leaflet";

// --------- types ----------
type GeoJSONType = any;

// --------- marker icon fix (pentru Vite) ----------
const markerIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

// --------- fit pe GeoJSON ----------
function FitOnGeo({ data }: { data: GeoJSONType | null }) {
  const map = useMap();
  useEffect(() => {
    if (!data) return;
    const layer = L.geoJSON(data);
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.2));
    }
  }, [data, map]);
  return null;
}

// --------- LEGEND ----------
function Legend() {
  const map = useMap();

  useEffect(() => {
    const legend = new L.Control({ position: "bottomright" });

    (legend as any).onAdd = () => {
      const div = L.DomUtil.create("div", "wind-legend");
      div.style.background = "#111";
      div.style.color = "white";
      div.style.padding = "10px";
      div.style.borderRadius = "8px";
      div.style.boxShadow = "0 2px 10px rgba(0,0,0,0.3)";
      div.style.fontFamily = "system-ui, sans-serif";
      div.style.fontSize = "12px";
      div.style.lineHeight = "1.4";

      const rows = [
        { label: "No data", color: "#6b7280" },
        { label: "< 4 m/s", color: "#22d3ee" },
        { label: "4–6 m/s", color: "#10b981" },
        { label: "6–8 m/s", color: "#f59e0b" },
        { label: "> 8 m/s", color: "#ef4444" },
      ];

      const item = (c: string, t: string) =>
        `<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
           <span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:${c};border:1px solid rgba(255,255,255,0.2)"></span>
           <span>${t}</span>
         </div>`;

      div.innerHTML =
        `<div style="font-weight:600;margin-bottom:6px;">Wind speed</div>` +
        rows.map(r => item(r.color, r.label)).join("");

      return div;
    };

    legend.addTo(map);
    return () => { legend.remove(); };
  }, [map]);

  return null;
}

// --------- MAIN APP ----------
export default function App() {
  const [geo, setGeo] = useState<GeoJSONType | null>(null);
  const [center, setCenter] = useState<[number, number]>([46.77, 23.62]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const gj = await fetch(`${import.meta.env.VITE_API_URL}/api/zones-geojson-detailed/`);
        if (!gj.ok) throw new Error(`zones HTTP ${gj.status}`);
        setGeo(await gj.json());

        const c = await fetch(`${import.meta.env.VITE_API_URL}/api/region-center/`);
        if (!c.ok) throw new Error(`center HTTP ${c.status}`);
        const cjson = await c.json();
        setCenter([cjson.lat, cjson.lon]);
      } catch (e: any) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div style={{ height: "100vh", background: "#111", color: "white" }}>
      <h1 style={{ padding: 12, margin: 0 }}>SkyWind — Map</h1>

      <div
        style={{
          height: "calc(100vh - 64px)",
          display: "grid",
          gridTemplateColumns: "auto 340px",
          gap: 12,
          padding: 12,
          boxSizing: "border-box",
          alignItems: "center",
        }}
      >
        {/* --- MAP --- */}
        <div
          style={{
            height: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: "min(560px, 70vw)",
              height: "min(560px, 70vw)",
            }}
          >
            {!loading && !error && (
              <MapContainer
                center={center}
                zoom={11}
                style={{ width: "100%", height: "100%", borderRadius: 8 }}
              >
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                {geo && <FitOnGeo data={geo} />}

                {/* --- POLIGOANE --- */}
                {geo && (
                  <GeoJSON
                    data={geo}
                    filter={(feature) => feature?.geometry?.type !== "Point"}
                    style={(feature: any) => {
                      const w = feature?.properties?.avg_wind_speed;
                      const color =
                        w == null ? "#6b7280" :
                        w > 8 ? "#ef4444" :
                        w > 6 ? "#f59e0b" :
                        w > 4 ? "#10b981" :
                                "#22d3ee";
                      return {
                        color,
                        weight: 2,
                        fillColor: color,
                        fillOpacity: 0.25,
                      };
                    }}
                    onEachFeature={(feature, layer) => {
                      const p: any = feature?.properties || {};
                      const id = p.id ?? feature?.id ?? "zone";
                      const t = p.avg_temperature ?? "–";
                      const w = p.avg_wind_speed ?? "–";
                      const html = `
                        <div style="font-family: system-ui; line-height:1.4">
                          <b>Zone ${id}</b><br/>
                          🌡️ Avg temp: <b>${t}</b><br/>
                          💨 Wind: <b>${w}</b>
                        </div>
                      `;
                      layer.bindPopup(html);
                    }}
                  />
                )}

                {/* --- MARKER CENTRAL --- */}
                <Marker position={center} icon={markerIcon}>
                  <Popup>Region center<br/>lat: {center[0]}, lon: {center[1]}</Popup>
                </Marker>

                {/* --- LEGENDA --- */}
                <Legend />
              </MapContainer>
            )}
            {loading && <p style={{ padding: 12 }}>Loading…</p>}
            {error && <p style={{ padding: 12, color: "salmon" }}>Error: {error}</p>}
          </div>
        </div>

        {/* --- SIDEBAR --- */}
        <aside
          style={{
            height: "100%",
            background: "#181818",
            borderRadius: 8,
            padding: 12,
            overflow: "auto",
            boxSizing: "border-box",
          }}
        >
          <p style={{ marginTop: 0 }}>
            {loading && "Loading…"}
            {error && <span style={{ color: "salmon" }}>{error}</span>}
            {!loading && !error && (
              <>
                <b>Polygons:</b>{" "}
                {Array.isArray(geo?.features) ? geo.features.length : "?"}
                <br />
                <b>Center:</b> {center[0].toFixed(3)}, {center[1].toFixed(3)}
              </>
            )}
          </p>
          <small style={{ opacity: 0.7 }}>
            (Afișez doar poligoanele + markerul centrului; punctele sunt ascunse)
          </small>
        </aside>
      </div>
    </div>
  );
}