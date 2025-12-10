import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";
import "./ZoneDetails.css";

export default function ZoneDetails({ zone }: { zone: ZoneDetailsDTO }) {
  return (
    <div className="zone-details-wrapper">
      <h2 className="zone-title">Zone #{zone.zone_index}</h2>

      {/* WIND */}
      <div className="detail-card">
        <h3>🌬️ Wind</h3>
        <div className="detail-grid">
          <p><strong>Speed:</strong> {zone.avg_wind_speed} m/s</p>
          <p><strong>Direction:</strong> {zone.wind_direction}°</p>
        </div>
      </div>

      {/* ALTITUDE */}
      <div className="detail-card">
        <h3>🏔️ Altitude</h3>
        <div className="detail-grid">
          <p><strong>Min:</strong> {zone.min_alt} m</p>
          <p><strong>Max:</strong> {zone.max_alt} m</p>
          <p><strong>Roughness:</strong> {zone.roughness}</p>
        </div>
      </div>

      {/* AIR & POWER */}
      <div className="detail-card">
        <h3>⚡ Air & Power</h3>
        <div className="detail-grid">
          <p><strong>Air Density:</strong> {zone.air_density}</p>
          <p><strong>Power Density:</strong> {zone.power_avg} W/m²</p>
        </div>
      </div>

      {/* LAND TYPE */}
      <div className="detail-card">
        <h3>🌿 Land Composition</h3>
        <div className="land-tags">
          {Object.keys(zone.land_type).length > 0 ? (
            Object.entries(zone.land_type).map(([type, percent]) => (
              <span key={type} className="land-tag">
                {type} — {percent}%
              </span>
            ))
          ) : (
            <p>No land data</p>
          )}
        </div>
      </div>

      {/* POTENTIAL */}
      <div className="detail-card potential-card">
        <h3>📈 Potential</h3>
        <p className="potential-value">{zone.potential.toFixed(1)} / 100</p>
      </div>
    </div>
  );
}
