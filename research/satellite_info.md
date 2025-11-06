# Satellite info
## A. Platforme principale (gratuite și oficiale)

| Platformă | Ce oferă | Ce poți face / accesa | Link |
|------------|-----------|------------------------|------|
| **Copernicus Data Space Ecosystem (CDSE)** | toate misiunile Sentinel (1–5P) | descarci imagini Sentinel-1 (radar), Sentinel-2 (optice), Sentinel-3 (oceane & temperatură), Sentinel-5P (aer) | [dataspace.copernicus.eu](https://dataspace.copernicus.eu) |
| **WEkEO DIAS portal cloud ESA** | procesare direct în browser | [wekeo.eu](https://wekeo.eu) |
| **CREODIAS / ONDA-DIAS** | acces rapid la colecții mari de date Sentinel și Copernicus DEM | bune pentru descărcări automate (API) | [creodias.eu](https://creodias.eu) / [onda-dias.eu](https://onda-dias.eu) |
| **Google Earth Engine (GEE)** | platformă cloud cu sute de colecții satelitare | calcule NDVI, pante, radiație, vânt etc. direct online fără descărcare | [earthengine.google.com](https://earthengine.google.com) |
| **NASA LP DAAC / USGS EarthExplorer** | misiunile Landsat, MODIS, ECOSTRESS | date brute + produse derivate (LST, vegetație, radiație) | [earthexplorer.usgs.gov](https://earthexplorer.usgs.gov) / [lpdaac.usgs.gov](https://lpdaac.usgs.gov) |
| **Microsoft Planetary Computer (MPC)** | colecții Sentinel, Landsat, DEM în format STAC/COG | analiză geospațială rapidă în Python | — |

### Pentru vânt, se folosesc în special:
- **Sentinel-1 (SAR)** → măsoară mișcarea suprafeței mării (folosit în modele de vânt)
- **ERA5 (ECMWF)** → reanalize climatice (viteza și direcția vântului)
- **Open-Meteo API** → vânt la sol / 100 m altitudine (rapid și simplu)
- **Copernicus Climate Data Store (CDS)** → date atmosferice detaliate

🔗 **Linkuri utile:**
- [https://dataspace.copernicus.eu](https://dataspace.copernicus.eu)
- [https://wekeo.eu](https://wekeo.eu)
- [https://creodias.eu](https://creodias.eu)
- [https://www.onda-dias.eu](https://www.onda-dias.eu)
- [https://earthengine.google.com](https://earthengine.google.com)
- [https://earthexplorer.usgs.gov](https://earthexplorer.usgs.gov)
- [https://lpdaac.usgs.gov](https://lpdaac.usgs.gov)

---

## STRUCTURA BAZEI DE DATE (pentru energie eoliană)

Scopul: stocarea informațiilor geospațiale pentru fiecare zonă analizată (celulă) + scorurile de potrivire pentru turbine.

---

### 🧱 A. Structura logică (tabele principale)

#### 🗺 Tabel: `locations` (zone / celule de analiză)

| Câmp | Tip | Descriere | Resurse |
|------|-----|------------|----------|
| `id` | INTEGER / SERIAL | identificator unic | — |
| `latitude` | FLOAT | coordonata latitudinală | — |
| `longitude` | FLOAT | coordonata longitudinală | — |
| `altitude` | FLOAT | altitudine (m) | [Copernicus DEM](https://dataspace.copernicus.eu) / [Earth Engine](https://earthengine.google.com) |
| `slope` | FLOAT | panta (°) | [Copernicus DEM](https://earthengine.google.com) |
| `ndvi` | FLOAT | vegetation index (0–1) (NDVI) | [Sentinel-2](https://earthengine.google.com) |
| `land_cover` | TEXT / SMALLINT | tip teren (0 = apă, 1 = pădure, 2 = câmp etc.) | [Sentinel-2](https://earthengine.google.com) |

---

#### 🧮 Tabel: `sources` (opțional – metadate)

| Câmp | Tip | Descriere |
|------|-----|------------|
| `dataset` | TEXT | numele dataset-ului (ex. ERA5, Sentinel-1, Copernicus DEM) |
| `resolution_m` | INTEGER | rezoluția spațială (ex. 1000 m) |
| `update_freq` | TEXT | zilnic / lunar |
| `data_format` | TEXT | GeoTIFF / NetCDF / API |
| `access_platform` | TEXT | ex. Google Earth Engine |

---

#### 🌬 Tabel: `wind_stats` (analize temporale)

| Câmp | Tip | Descriere | Sursă |
|------|-----|------------|--------|
| `wind_speed` | FLOAT | viteza medie a vântului (m/s) | [Open-Meteo](https://open-meteo.com), [ERA5](https://cds.climate.copernicus.eu) |
| `wind_dir` | FLOAT | direcția medie a vântului (°) | [ERA5 API](https://cds.climate.copernicus.eu/api-how-to) |
| `rugosity` | FLOAT | netezimea terenului (0–1) | Sentinel-1 |
| `wind_score` | FLOAT | scor final 0–100 (rezultat final) | calcul intern |

---

#### ⏱ Tabel: `wind_time_series` (exemplu temporal)

| Câmp | Tip | Descriere |
|------|-----|------------|
| `location_id` | FK → `locations.id` | legătură cu locația |
| `timestamp` | DATE | data observației |
| `wind_speed` | FLOAT | m/s |
| `wind_dir` | FLOAT | grade |
| `temperature` | FLOAT | °C |
| `humidity` | FLOAT | % |

---

### 🔢 B. Formatul fișierelor (înainte de import în DB)

- De la GEE / ERA5: `.csv` sau `.geojson` cu coloane:  
  `lat`, `lon`, `wind_speed`, `slope`, `ndvi`, `altitude`
- Convertibil în SQL sau shapefile pentru QGIS
- Poți importa în PostgreSQL + PostGIS cu:
  ```bash
  shp2pgsql -I wind_data.shp public.wind_data | psql -U user -d database
