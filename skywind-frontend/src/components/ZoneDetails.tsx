import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";
import "./ZoneDetails.css";

export default function ZoneDetails({ zone, minDomain = 0, maxDomain = 2500 }: { zone: ZoneDetailsDTO, minDomain?: number, maxDomain?: number }) {
  return (
    <div className="zone-details-wrapper">
      <h2 className="zone-title">Zone #{zone.zone_index}</h2>

      {/* POTENTIAL */}
      <div className="detail-card potential-card">
        <h3>📈 Potential</h3>
        <p className="potential-value">{zone.potential.toFixed(1)} / 100</p>
      </div>

      {/* WIND */}
      <div className="detail-card">
        <h3>🌬️ Wind</h3>
        <div className="wind-visual-row">
          <div className="wind-info">
            <p style={{ marginBottom: '4px' }}><strong>Speed:</strong> {zone.avg_wind_speed} m/s</p>
            <p><strong>Direction:</strong> {zone.wind_direction}°</p>
          </div>
          
          <svg className="wind-rose-svg" viewBox="0 0 100 100">
            {/* Circle background */}
            <circle cx="50" cy="50" r="45" fill="#f9f9f9" stroke="#ddd" strokeWidth="1" />
            
            {/* Cardinal Points */}
            <text x="50" y="15" className="wind-rose-text">N</text>
            <text x="50" y="90" className="wind-rose-text">S</text>
            <text x="88" y="52" className="wind-rose-text">E</text>
            <text x="12" y="52" className="wind-rose-text">W</text>

            {/* Arrow Group - Rotated */}
            <g transform={`rotate(${zone.wind_direction}, 50, 50)`}>
              {/* Arrow Shaft */}
              <line x1="50" y1="75" x2="50" y2="25" stroke="#e74c3c" strokeWidth="3" strokeLinecap="round" />
              {/* Arrow Head */}
              <path d="M 50 20 L 44 32 L 56 32 Z" fill="#e74c3c" />
            </g>
          </svg>
        </div>
      </div>

      {/* ALTITUDE */}
      <div className="detail-card">
        <h3>🏔️ Altitude</h3>
        <p style={{ marginBottom: '6px' }}><strong>Roughness:</strong> {zone.roughness}</p>
        <div style={{ display: 'flex', gap: '24px' }}>
          <p><strong>Min:</strong> {zone.min_alt} m</p>
          <p><strong>Max:</strong> {zone.max_alt} m</p>
        </div>

        <div className="altitude-slider-container">
           <div className="altitude-slider-track">
              <div 
                className="altitude-slider-range"
                style={{
                  left: `${Math.max(0, Math.min(100, ((zone.min_alt - minDomain) / (maxDomain - minDomain)) * 100))}%`,
                  width: `${Math.max(0, Math.min(100, ((zone.max_alt - zone.min_alt) / (maxDomain - minDomain)) * 100))}%`
                }}
              />
           </div>
           <div className="altitude-slider-labels">
             <span>{Math.round(minDomain)}m</span>
             <span>{Math.round(maxDomain)}m</span>
           </div>
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

    </div>
  );
}
