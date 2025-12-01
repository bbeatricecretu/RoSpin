import { useEffect, useState } from "react";

export default function SavedRegionsPage() {
  const [saved, setSaved] = useState<any[]>([]);

  useEffect(() => {
    const data = localStorage.getItem("savedRegions");
    if (data) setSaved(JSON.parse(data));
  }, []);

  return (
    <div style={{ padding: "40px" }}>
      <h1 style={{ color: "var(--primary)" }}>Saved Regions</h1>

      {saved.length === 0 ? (
        <p>No saved regions yet.</p>
      ) : (
        <ul>
          {saved.map((r, idx) => (
            <li key={idx}>
              <b>Region #{r.id}</b> — lat {r.lat}, lon {r.lon}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}