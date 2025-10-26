# ☀️ RoSpin – Solar Potential Mapping Project

Welcome!  
This repository will guide you step-by-step through the process of building **RoSpin**, a solar suitability analysis app that identifies the best areas for photovoltaic (PV) panel installation using satellite data.

Think of this as a structured learning path — you’ll not only build the tool, but also understand *why each step matters*.

---

## 🧭 Goal

You will develop an application that determines **optimal locations for solar panels** by combining satellite-derived data layers:

- 🌄 **Terrain slope/aspect** (from DEM)  
- ☀️ **Sunlight availability** (irradiance)  
- ☁️ **Cloud and weather patterns** (sunlight loss)  
- 🌿 **Land-use masks** (exclude forests, water, and urban areas)

🎯 **Output:** a **heatmap** of solar suitability + **geographic coordinates** of ideal installation sites.

---

## ⚙️ Stage 0 — Setup (Environment)

### Tools You’ll Need
- **Google Earth Engine (GEE)** — visual exploration & dataset access  
- **Python** (3.9+) with:
  - `rioxarray`, `xarray`, `rasterio`, `geopandas`, `matplotlib`
  - `xrspatial`, `whitebox`, `geemap`

### Why This Setup?
- **GEE** gives free cloud computation and easy access to global satellite data.  
- **Python** gives you control, automation, and the ability to build the final app.

---

## 🧩 Stage 1 — Input Data (Start Small, ~100×100 km AOI)

| What | Source | Resolution | Purpose |
|------|---------|-------------|---------|
| DEM | Copernicus DEM (GLO-30) | 30 m | slope, aspect |
| Sunlight | NASA POWER / ERA5 SSRD | ~25 km | average irradiance |
| Cloud cover | MODIS or VIIRS | 1 km | sunlight loss factor |
| Land cover | Sentinel-2 L2A (NDVI/NDWI) | 10 m | remove forests & water |

> 🧠 **Tip:** Always start with a small area of interest (AOI) before scaling up.

---

## 🧠 Stage 2 — Workflow Overview

```
DEM ──► slope/aspect ───┐
                        │
NASA POWER/ERA5 ─► irradiance ─┐
MODIS ─► cloud cover ──────────┤► weighted sum → Solar Suitability Index (0–1)
Sentinel-2 ─► NDVI/NDWI mask ─┘
```

Once processed, export your **raster** → build a **simple interactive map**.

---

## 🪜 Stage 3 — Step-by-Step Plan

### 1️⃣ Terrain Analysis
- Import DEM  
- Compute **slope** and **aspect** (in degrees):  
  ```
  slope_deg = arctan(√(dz/dx² + dz/dy²))
  aspect_deg = atan2(dz/dy, dz/dx)
  ```
- Mask slopes > 30° (impractical for construction)  
- Compute “southness” (ideal aspect ≈ 180° for N. Hemisphere)

---

### 2️⃣ Irradiance + Cloud
- Retrieve **annual solar radiation** (NASA POWER / ERA5)  
  → Units: J/m²; convert to kWh/m²/year  
- Retrieve **mean cloud fraction** (0–1, MODIS/VIIRS)  
  → Effective irradiance = `Irradiance × (1 − CloudFraction)`

---

### 3️⃣ Land Mask
- Use **Sentinel-2 L2A** reflectance  
- Compute:
  ```
  NDVI = (B8 − B4)/(B8 + B4)
  NDWI = (B3 − B8)/(B3 + B8)
  ```
- NDVI > 0.5 → vegetation → mask out  
- NDWI > 0.3 → water → mask out  

---

### 4️⃣ Normalize & Weight
Bring all scores into the 0–1 range.

```
irr_score  = normalized effective irradiance
slope_score = 1 − slope/30
southness   = exp(−(aspect − 180)² / (2 × 45²))

Suitability = 0.5 × irr_score + 0.3 × southness + 0.2 × slope_score
Suitability *= land_allowed_mask
```

---

### 5️⃣ Output
- Save final raster (`.tif` or COG format)  
- Extract top areas (`Suitability > 0.8`) → GeoJSON  
- Visualize quickly in GEE or with `geemap.Map()`

---

## 🧰 Stage 4 — Development Order

| Phase | Tool | Goal |
|-------|------|------|
| 1. Data exploration | **GEE** | Load DEM, Sentinel-2, ERA5; visualize individually |
| 2. Core computation | **Python notebooks** | Calculate slope/aspect and irradiance combination |
| 3. Integration | **Python script** | Build final suitability raster |
| 4. Visualization | **Streamlit / Leaflet** | Interactive heatmap |
| 5. Validation | **PVGIS / ground data** | Sanity-check irradiance values |

---

## 📍 Stage 5 — Deliverables

- `solar_pipeline.ipynb` — main processing notebook  
- `suitability_map.tif` — final raster output  
- `top_sites.geojson` — top potential areas  
- *(Optional)* `app.py` — simple interactive map  

---

## 🚦 Stage 6 — Finish Line

You’re done when you can:

- 🖱 **Click on any map point** to view slope, aspect, irradiance, and score  
- 📤 **Export top polygons** as GeoJSON  
- 🗺 **Visually confirm**: south-facing hills rank higher than north-facing ones  

---

## 🔑 Priorities for a Beginner

1. Start with **Google Earth Engine** — explore datasets visually.  
2. Export small AOIs and process locally in Python.  
3. Only once the index logic works → build the app interface.

---

## 💥 Optional Advanced Steps

- Integrate **PVLIB** for tilt-corrected irradiance simulation.  
- Add **grid distance** or **land-cost** layers.  
- Experiment with **multi-criteria decision analysis (AHP)** for weighting.  

---

## 📁 Recommended Project Structure

```
solar_potential_app/
│
├── 00_docs/
│   ├── README.md
│   ├── data_sources.md
│   └── methodology.md
│
├── 01_exploration_GEE/
│   ├── solar_exploration_script.js
│   ├── sentinel2_visualization.js
│   ├── dem_terrain_test.js
│   └── notes_exploration.md
│
├── 02_raw_data/
│   ├── dem/
│   ├── irradiance/
│   ├── clouds/
│   ├── sentinel2/
│   └── aoi/
│
├── 03_preprocessing/
│   ├── 01_merge_reproject.ipynb
│   ├── 02_compute_slope_aspect.ipynb
│   ├── 03_compute_masks.ipynb
│   ├── utils_reproject.py
│   └── utils_visuals.py
│
├── 04_processing/
│   ├── 01_compute_scores.ipynb
│   ├── 02_suitability_index.ipynb
│   ├── 03_extract_top_sites.ipynb
│   ├── config.yaml
│   └── pipeline.py
│
├── 05_outputs/
│   ├── suitability_raster.tif
│   ├── top_sites.geojson
│   ├── plots/
│   │   ├── slope_histogram.png
│   │   ├── irradiance_map.png
│   │   └── final_heatmap.png
│   └── validation/
│       └── comparison_PVGIS.csv
│
├── 06_app/
│   ├── app.py
│   ├── assets/
│   │   └── style.css
│   └── sample_map.html
│
├── environment.yml
├── .gitignore
└── LICENSE
```

---

## 🧩 How to Progress Through the Folders

### 1️⃣ `01_exploration_GEE`
Explore in Earth Engine.  
Understand DEM, clouds, and irradiance visually.  
Export a small AOI (~50×50 km) as GeoTIFFs → `/02_raw_data/`.

> 🎯 *Goal:* Build intuition, not perfect code.

---

### 2️⃣ `02_raw_data`
Keep all raw satellite exports here — unmodified.  
Use clear, consistent names like:

```
dem_copernicus_cluj_30m.tif
irradiance_nasapower_cluj_2023.tif
cloud_viirs_mean_2018_2023.tif
```

> 🧭 *Rule:* Never edit files in this folder.

---

### 3️⃣ `03_preprocessing`
Align and clean everything — same CRS, same resolution.  
Outputs include:

```
dem_aligned.tif
slope.tif
aspect.tif
cloud_mean_aligned.tif
irradiance_aligned.tif
landmask.tif
```

> ✅ *Goal:* Perfect alignment and unit consistency.

---

### 4️⃣ `04_processing`
Combine all preprocessed layers.  
Use `config.yaml` for weights and thresholds.  
Run your pipeline:

```
python pipeline.py --aoi cluj.geojson --weights config.yaml
```

> ⚙️ *Goal:* Fully automated solar suitability map for any AOI.

---

### 5️⃣ `05_outputs`
Store all final outputs and quick visualizations.  
Organize plots and results by run/date.

> 🧪 *Goal:* Reproducible science and easy reporting.

---

### 6️⃣ `06_app`
Create a simple app (Streamlit, Dash, or Leaflet).  
Start minimal: display your `suitability_raster.tif`.  
Add a map click → show slope, irradiance, and score.  
Later, integrate an energy-yield calculator.

> 🧭 *Goal:* Turn data into a clear, interactive story.

---

## ⚙️ File Progression Checklist

| Phase | Input | Output | File |
|-------|--------|--------|------|
| GEE exploration | Raw datasets | `.tif` exports | `/01_exploration_GEE/*.js` |
| Terrain | DEM | slope, aspect | `03_preprocessing/02_compute_slope_aspect.ipynb` |
| Cloud/Irradiance | MODIS, NASA POWER | irradiance_eff | `03_preprocessing/01_merge_reproject.ipynb` |
| Land Mask | Sentinel-2 | landmask | `03_preprocessing/03_compute_masks.ipynb` |
| Suitability | all preprocessed layers | final raster | `04_processing/02_suitability_index.ipynb` |
| App | suitability raster | interactive map | `06_app/app.py` |

---

## 🧠 Practical Advice

- Keep your AOI small (≈ 50×50 km) while testing.  
- Visualize after every major step to catch alignment issues early.  
- Store weights, thresholds, and file paths in `config.yaml` — makes re-runs consistent.  
- Use Git to version-control notebooks in `/03_preprocessing` and `/04_processing`.

---

## ✅ End Condition

You’ve completed the project when:

1. `python pipeline.py` → produces `suitability_raster.tif`  
2. `streamlit run 06_app/app.py` → launches an interactive map  
3. `top_sites.geojson` opens in QGIS and visually matches expectations  

---

> 🧑‍🏫 **Instructor’s Note:**  
> This project is not just about building a solar map — it’s about mastering how to structure, process, and validate satellite data step-by-step.  
> Treat every stage as a mini-milestone, and you’ll end up with a project you can proudly demo or expand into real research.
