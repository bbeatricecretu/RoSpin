import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";

export default function ZoneDetails({ zone }: { zone: ZoneDetailsDTO }) {
  return (
      <div className="zone-details-container">
          <h3>Zone #{zone.zone_index}</h3>

          <h4>Corners</h4>
          <p>A: {zone.A.lat}, {zone.A.lon}</p>
          <p>B: {zone.B.lat}, {zone.B.lon}</p>
          <p>C: {zone.C.lat}, {zone.C.lon}</p>
          <p>D: {zone.D.lat}, {zone.D.lon}</p>

          <h4>Wind</h4>
          <p>Speed: {zone.avg_wind_speed} m/s</p>
          <p>Direction: {zone.wind_direction}°</p>

          <h4>Altitude</h4>
          <p>Min: {zone.min_alt} m</p>
          <p>Max: {zone.max_alt} m</p>
          <p>Roughness: {zone.roughness}</p>

          <h4>Air & Power</h4>
          <p>Air density: {zone.air_density}</p>
          <p>Power density: {zone.power_avg} W/m²</p>

          <h4>Land</h4>
          <div className="land-type-list">
            {Object.keys(zone.land_type).length > 0 ? (
              Object.entries(zone.land_type).map(([type, percent]) => (
                <p key={type}>{type}: {percent}%</p>
              ))
            ) : (
              <p>No land data</p>
            )}
          </div>
          <p>Potential: {zone.potential}</p>

          <h4>Infrastructure</h4>
          <p>Index: {zone.infrastructure.index}</p>
          <p>km_jud: {zone.infrastructure.km_jud}</p>
          <p>km_nat: {zone.infrastructure.km_nat}</p>
          <p>km_euro: {zone.infrastructure.km_euro}</p>
          <p>km_auto: {zone.infrastructure.km_auto}</p>
      </div>
  );
}

