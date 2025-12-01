import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./SavedRegionsPage.css";

import { getRegionDetails } from "../services/RegionAPI";
import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";

export default function SavedRegionsPage() {
  const navigate = useNavigate();

  const [savedIds, setSavedIds] = useState<number[]>([]);
  const [regions, setRegions] = useState<RegionDetailsDTO[]>([]);
  const [loading, setLoading] = useState(true);

  // Load saved IDs from localStorage
  useEffect(() => {
    const list = JSON.parse(localStorage.getItem("savedRegions") || "[]");
    setSavedIds(list);
  }, []);

  // Fetch region summaries
  useEffect(() => {
    async function loadDetails() {
      if (savedIds.length === 0) {
        setLoading(false);
        return;
      }

      const arr: RegionDetailsDTO[] = [];

      for (const id of savedIds) {
        try {
          const r = await getRegionDetails(id);
          if (r) arr.push(r);
        } catch {
          console.warn(`Region ${id} not found`);
        }
      }

      setRegions(arr);
      setLoading(false);
    }

    loadDetails();
  }, [savedIds]);

  // Remove saved region
  function removeRegion(id: number) {
    const filtered = savedIds.filter((x) => x !== id);
    localStorage.setItem("savedRegions", JSON.stringify(filtered));
    setSavedIds(filtered);
    setRegions((prev) => prev.filter((r) => r.id !== id));
  }

  if (loading)
    return (
      <div className="saved-wrapper">
        <p>Loading saved regions...</p>
      </div>
    );

  return (
    <div className="saved-wrapper">
      <h1 className="saved-title">Saved Regions</h1>

      {regions.length === 0 && (
        <div className="empty-box">
          <p>No saved regions yet.</p>
          <button onClick={() => navigate("/generate")}>Generate One</button>
        </div>
      )}

      <div className="saved-list">
        {regions.map((r) => (
          <div key={r.id} className="saved-card">
            
            <div className="saved-info">
              <h3>Region #{r.id}</h3>
              <p><strong>Avg Potential:</strong> {r.avg_potential.toFixed(1)} / 100</p>
              <p><strong>Rating:</strong> {r.rating.toFixed(1)}</p>
            </div>

            <div className="saved-actions">
              <button
                className="view-btn"
                onClick={() =>
                  navigate(`/region/${r.id}`, { state: { region_id: r.id } })
                }
              >
                View
              </button>

              <button
                className="delete-btn"
                onClick={() => removeRegion(r.id)}
              >
                Remove
              </button>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}