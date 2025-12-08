import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";

export default function RegionDetails({ region }: { region: RegionDetailsDTO }) {
  return (
      <div className="region-details-container">
          <h3>Center</h3>
          <p>Lat: {region.center.lat}</p>
          <p>Lon: {region.center.lon}</p>

          <h3>Corners</h3>
          <p>A: {region.A.lat}, {region.A.lon}</p>
          <p>B: {region.B.lat}, {region.B.lon}</p>
          <p>C: {region.C.lat}, {region.C.lon}</p>
          <p>D: {region.D.lat}, {region.D.lon}</p>

          <h3>Region Stats</h3>
          <p>Avg temperature: {region.avg_temperature.toFixed(2)} °C</p>
          <p>Rating: {region.rating}</p>
          <p>Avg potential: {region.avg_potential.toFixed(2)}</p>
          <p>Infrastructure rating: {region.infrastructure_rating.toFixed(2)}</p>
          <p>Index average: {region.index_average.toFixed(2)}</p>
          <p>Best zone: {region.max_potential_zone}</p>

          {}<h3>Wind Rose</h3>
          <pre>{JSON.stringify(region.wind_rose, null, 2)}</pre>
      </div>
  );
}
