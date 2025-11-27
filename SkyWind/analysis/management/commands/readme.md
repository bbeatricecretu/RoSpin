# SkyWind -- GEE Data Documentation

This document explains **exactly how every environmental attribute is
computed** inside the SkyWind backend --- following the real computation
flow from your `fetch_gee_data.py` and `gee_data.py`.

Each attribute includes:

-   **Data source**
-   **What it measures**
-   **Step-by-step computation** 
-   **Typical ranges & interpretation**

------------------------------------------------------------------------

# 1. Average Temperature (Region Level)

### **Source:**

ERA5-Land --- `temperature_2m`

### **Meaning:**

Average annual temperature at 2 meters above ground at the **region
center**.

### **How Computed:**

1.  Load ERA5-Land hourly temperature images for the whole year:

        ImageCollection('ECMWF/ERA5_LAND/HOURLY').select('temperature_2m')

2.  Filter by date: `YYYY-01-01 → YYYY-12-31`

3.  Compute the **mean image**:

        img = coll.mean()

4.  Create a GEE point from region center (lon, lat)

5.  Reduce temperature inside 1 km radius:

        reducer = mean()

6.  Convert Kelvin → Celsius:

        Celsius = Kelvin - 273.15

7.  Round to **2 decimals**.

### **Typical Values:**

-   Transylvania: **5--12°C**
-   Lowlands: **10--15°C**
-   Mountains: **0--7°C**

------------------------------------------------------------------------

# 2. Wind Speed (Zone Level)

### **Source:**

ERA5-Land --- `u_component_of_wind_10m`, `v_component_of_wind_10m`

### **Meaning:**

Annual mean wind speed at 10m height for each zone.

### **How Computed:**

1.  For each zone, compute the **zone center**:

        center_lat = (A.lat + B.lat + C.lat + D.lat) / 4
        center_lon = (A.lon + B.lon + C.lon + D.lon) / 4

2.  Round (lat, lon) to **5 decimals** to fix floating-key
    inconsistencies.

3.  Build an ERA5-Land mean image for the whole year.

4.  Wind speed is computed using:

        speed = sqrt(u*u + v*v)

5.  Reduce region at each zone center (scale = 1000 m).

6.  Values stored as:

    -   **speed (m/s)**, rounded to 2 decimals\
    -   If missing → set to **0.0**

### **Typical Values:**

-   Poor: **0--3 m/s**
-   Moderate: **3--6 m/s**
-   Good: **6--8 m/s**
-   Excellent: **8+ m/s**

------------------------------------------------------------------------

# 3. Wind Direction (Zone Level)

### **Source:**

ERA5-Land --- same wind components as above.

### **Meaning:**

Dominant annual wind direction (0--360 degrees).

### **How Computed:**

1.  With the same mean u and v:

2.  Compute direction using:

        direction = (180 / π) * atan2(u, v)

3.  Normalize:

        direction = (direction + 360) % 360

4.  Reduce at the zone center.

5.  Store rounded to **1 decimal**.

6.  If missing → `0.0`

### **Interpretation:**

-   **0°** = North\
-   **90°** = East\
-   **180°** = South\
-   **270°** = West

------------------------------------------------------------------------

# 4. DEM: Min/Max Altitude & Roughness

### **Source:**

Copernicus DEM GLO-30

### **Meaning:**

-   **min_alt**: lowest elevation in the zone\
-   **max_alt**: highest elevation\
-   **roughness**: terrain variability (std deviation)

### **How Computed:**

1.  Load DEM mosaic and select `"DEM"` band.

2.  Build a polygon for each zone using corner Points.

3.  Create FeatureCollection of all zone polygons.

4.  Combine reducers:

    -   `mean()`
    -   `minMax()`
    -   `stdDev()`

5.  Reduce DEM over each polygon:

        scale = 30 m

6.  Extract:

    -   `elevation_min → min_alt`
    -   `elevation_max → max_alt`
    -   `tri_stdDev → roughness`

7.  Round to **2 decimals**.

### **Typical Values:**

-   Plains: **150--400 m**
-   Hills: **400--900 m**
-   Mountains: **1000--2500 m**
-   Roughness:
    -   **0--3** = flat
    -   **4--8** = gentle hills
    -   **10+** = mountainous

------------------------------------------------------------------------

# 5. Air Density (Zone Level)

### **Source:**

ERA5-Land --- `surface_pressure` and `temperature_2m`

### **Meaning:**

Density of air (kg/m³), critical for wind power.

### **How Computed:**

1.  Load hourly ERA5-Land pressure + temperature.

2.  Compute annual mean.

3.  Apply formula:

        ρ = P / (R_d * T)
        R_d = 287.05

4.  ReduceRegions at zone polygon centroids.

5.  Store as **float**, rounded to 3 decimals.

### **Typical Values:**

-   Sea level cold: **1.25--1.30**
-   Inland warm: **1.15--1.22**
-   High mountains: **0.90--1.10**

------------------------------------------------------------------------

# 6. Wind Power Density (Zone Level)

### **Source:**

ERA5-Land --- wind + temperature + pressure combined

### **Meaning:**

Theoretical wind energy per square meter (W/m²).

### **How Computed:**

1.  Map function over all hourly images:

        speed = sqrt(u² + v²)
        rho = p / (R_d * T)
        power_density = 0.5 * rho * speed³

2.  Build an hourly collection of power density.

3.  Compute the **mean** of this collection.

4.  Reduce at each zone centroid (scale=1000).

5.  Round to **1 decimal**.

### **Typical Values (inland):**

-   Weak areas: **1--20 W/m²**
-   Decent sites: **50--200 W/m²**
-   Excellent sites: **250--400 W/m²**

------------------------------------------------------------------------

# 7. Land Cover Classification (Zone Level)

### **Source:**

ESA WorldCover v200

### **Meaning:**

Shows the dominant land cover inside the zone polygon.

### **How Computed:**

1.  Reduce with **frequencyHistogram()**:

        {40: 150, 30: 150, 20: 50}

2.  Find **max_count**.

3.  Extract all classes matching max_count.

4.  Convert class numbers → names using WORLD_COVER_CLASSES.

5.  When tied (most common case):

        Grassland, Cropland

6.  If histogram missing → empty string.

### **Typical Values:**

-   30: Grassland\
-   40: Cropland\
-   10: Tree cover\
-   50: Built-up

------------------------------------------------------------------------

# 8. Potential Scoring (Zone Level)

### **Meaning:**

A suitability index (0--100) used for ranking zones.

### **How Computed:**

1.  Normalize wind power:

        wpd = power_avg / 800
        wpd = min(wpd, 1.25)

2.  Compute roughness score:

        rough = 1 - min(roughness / 50, 1)

3.  Land penalty:

        ok = 1 if land_type NOT in excluded classes else 0

4.  Combine all factors:

        potential = 100 * (0.7 * wpd + 0.3 * rough) * ok

5.  Round to **1 decimal**.

### **Typical Ranges:**

-   0--20 = unsuitable\
-   20--40 = weak\
-   40--70 = good\
-   70--100 = excellent

------------------------------------------------------------------------

# 9. Infrastructure Accessibility (Zone Level)

### **Source:**

OpenStreetMap via Overpass API

### **Meaning:**

Infrastructure accessibility score (0--10) based on proximity to:
- Power substations and transmission lines (critical for grid connection)
- Major roads and motorways (for construction and maintenance access)

### **How Computed:**

1. Calculate zone center coordinates.

2. Query OpenStreetMap within 50km radius for:
   - Power substations (`power=substation`)
   - High-voltage transmission lines (`power=line`, 110kV-400kV)
   - Motorways (`highway=motorway`)
   - Major roads (`highway=trunk` or `primary`)

3. Calculate distance to nearest of each type.

4. Score each category (0-10) based on distance:
   - **Substations** (40% weight):
     - < 5km: 10 points
     - < 10km: 8 points
     - < 20km: 6 points
     - < 35km: 4 points
     - < 50km: 2 points
   - **Transmission lines** (30% weight):
     - < 2km: 10 points
     - < 5km: 8 points
     - < 10km: 6 points
   - **Major roads** (20% weight):
     - < 1km: 10 points
     - < 3km: 8 points
     - < 5km: 6 points
   - **Motorways** (10% weight):
     - < 5km: 10 points
     - < 15km: 7 points
     - < 30km: 4 points

5. Calculate weighted average and round to integer.

6. Store in `zone.infrastructure.index`.

### **Typical Values:**

- **0-2**: Very poor accessibility (remote areas)
- **3-4**: Poor accessibility (significant infrastructure investment needed)
- **5-6**: Moderate accessibility (feasible with planning)
- **7-8**: Good accessibility (favorable for development)
- **9-10**: Excellent accessibility (near existing infrastructure)

### **Notes:**

- Uses rate limiting (1 second delay per 10 zones) to avoid overwhelming OSM servers
- Includes retry logic for transient API errors
- Returns 0 if no infrastructure found within 50km radius

------------------------------------------------------------------------

# 10. Wind Rose (Region Level)

### **Meaning:**

Directional distribution of wind.\
Shows average wind strength for each of:

    N, NE, E, SE, S, SW, W, NW

### **How Computed :**

1.  For each zone, take:
    -   `wind_direction`
    -   `avg_wind_speed`
2.  Map direction → sector bucket
3.  Add wind speed to bucket list
4.  Compute average per bucket
5.  Save dictionary as JSON

------------------------------------------------------------------------

# 11. Region-Level Metrics

### **a) avg_potential**

Mean potential of all zones.

### **b) max_potential**

Zone with highest potential.

### **c) infrastructure_rating**

Average `infrastructure.index` across all zones in the region.

Reflects overall accessibility of the region for wind farm development.

### **d) index_average**

Average zone index (1..N).

### **e) rating**

A simple normalized score:

    rating = int(avg_potential * 10)

------------------------------------------------------------------------
