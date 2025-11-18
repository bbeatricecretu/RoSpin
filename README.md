# Description

## Overview
Satelite Wind ROSPIN is a collaborative project focused on identifying and mapping the most suitable locations for installing wind farms. The project integrates satellite data analysis, cloud-based processing, and geospatial visualization.

## Goal
To build an application that automatically processes satellite data using Google Earth Engine to evaluate wind energy potential across different regions. The system should help users visualize optimal wind farm sites based on environmental, geographic, and infrastructural criteria.

The user will provide input such as:

- A **set of coordinates** (a point and a range), **or**
- A **city or region name**, together with **minimum yearly energy output** or **minimum wind speed** requirements.

Based on this input, the system will generate a **list of suitable locations** for wind farms.  
Each result in the list will include:

- **Rating** — an overall suitability score for wind energy generation.  
- **Nearest Energy Accumulation or Storage Point** — the closest facility or area where the produced energy could be efficiently stored or transmitted.

When the user selects one of the locations, an **interactive map** will open, and that area will be **highlighted**, showing its position and context (e.g., nearby infrastructure or storage systems).
"""
## Core Components
- 🛰 **Data Collection:** Use satellite datasets (e.g., wind speed, elevation, land use, environmental layers).  
- ⚙️ **Data Processing:** Process data using tools like **ESA SNAP**, **Google Earth Engine**, or custom Python scripts.  
- 🧠 **Analysis Engine:** Apply algorithms (e.g., suitability analysis, thresholds, ML models) to identify ideal areas.  
- 🌍 **Front-End Application:** An interactive map interface that lets users explore potential wind farm locations.  
- ☁️ **Cloud Integration:** Use **Google Cloud Platform** for storage, APIs, and team collaboration.  
- 🐳 **Deployment:** Containerize components with **Docker** and manage infrastructure with **Kubernetes** if needed.  
- 🧩 **Collaboration:** Designed for a multi-member development team (front-end, back-end, data processing, deployment, etc.).

## Short Summary
> “We’re working on Satelite Wind ROSPIN, a project that uses satellite data and cloud tools to map the best areas for wind farms. It combines ESA SNAP or Earth Engine processing, data analysis, and an interactive map interface deployed in Google Cloud.”
"""


## 🔗 **Important Links**

1. **Google Earth Engine** — Main platform for most satellite and geospatial resources.  
   🌍 [https://earthengine.google.com/](https://earthengine.google.com/)

2. **Open-Meteo** — Provides wind speed and other meteorological data (no account required, easy to use).  
   💨 [https://open-meteo.com/](https://open-meteo.com/)

3. **Copernicus Browser** — Source for land surface and terrain data visualization and downloads.  
   🗺 [https://browser.dataspace.copernicus.eu/](https://browser.dataspace.copernicus.eu/)

4. **Copernicus Climate Data Store (CDS)** — API and datasets for wind direction and wind speed (ERA5, etc. ).  
   🌬 [https://cds.climate.copernicus.eu/api-how-to](https://cds.climate.copernicus.eu/api-how-to)

### 🧾 **Note**
Try creating accounts or testing access on these two platforms to explore available datasets:  
- [Copernicus Browser](https://browser.dataspace.copernicus.eu/?zoom=5&lat=50.16282&lng=20.78613&demSource3D=%22MAPZEN%22&cloudCoverage=30&dateMode)  
- [Copernicus Climate Data Store (CDS)](https://cds.climate.copernicus.eu/api-how-to)

