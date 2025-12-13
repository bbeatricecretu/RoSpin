# SkyWind

SkyWind is a collaborative geospatial intelligence tool designed to map optimal locations for wind energy infrastructure. By integrating Google Earth Engine, the application allows users to analyze specific regions for wind energy suitability based on environmental conditions and proximity to energy storage.

## 📋 Table of Contents
 * [System Architecture](https://github.com/bbeatricecretu/RoSpin/edit/main/README.md#-system-architecture)
 * [How It Works](https://github.com/bbeatricecretu/RoSpin/edit/main/README.md#%EF%B8%8F-how-it-works)
 * [Key Features](https://github.com/bbeatricecretu/RoSpin/edit/main/README.md#-key-features)
 * [Tech Stack](https://github.com/bbeatricecretu/RoSpin/edit/main/README.md#-tech-stack)
 * [Data Sources](https://github.com/bbeatricecretu/RoSpin/edit/main/README.md#-data-sources)
 * [Installation](https://github.com/bbeatricecretu/RoSpin/edit/main/README.md#-installation)

## 🏗 System Architecture
The system aggregates data from multiple satellite providers, processes it via a Python backend, and renders the results on an interactive frontend map.


<img width="900" height="695" alt="image" src="https://github.com/user-attachments/assets/5ff48eda-3ec7-4d27-8392-9fd2e06ce20a" />


## ⚙️ How It Works

### 1. Define the Zone
The user begins by defining the Area of Interest (AOI) using the sidebar inputs:
* **Latitude & Longitude:** Sets the center point of the search.
* **Side (km):** Defines the total width of the square zone.
* **Grid Split:** Determines the analysis granularity (e.g., splitting the zone into a 5x5 grid).

<img width="3012" height="1635" alt="Screenshot 2025-12-11 114210" src="https://github.com/user-attachments/assets/92acf85e-28ac-4d4f-b6f8-70eab4173b3f" />
<img width="3024" height="1637" alt="Screenshot 2025-12-11 114130" src="https://github.com/user-attachments/assets/b5bff509-3199-48c7-aee4-3da0ed80f92f" />
<img width="3061" height="1790" alt="Screenshot 2025-12-11 141746" src="https://github.com/user-attachments/assets/493cc8ae-4414-4dd5-812b-6619abe6dc34" />


### 2. Automated Analysis
Once triggered, the system divides the area into the requested grid cells. For each cell, it queries satellite data via **Google Earth Engine** to calculate:
* **Wind Potential:** Average wind speed consistency.
* **Terrain Suitability:** Elevation and slope feasibility.
* **Infrastructure Context:** Distance to the nearest valid infrastructure point.

### 3. Visualizing Results
The application generates a heatmap overlay on the map, coloring zones by their suitability score. Users can click on specific grid cells to view detailed metrics and the vector path to the **Nearest Energy Accumulation Point**.

![Map Visualization](https://github.com/user-attachments/assets/60be5ae7-8e48-41d2-b53b-60e43ed46eb1)

## ✨ Key Features
 * **Dynamic Grid Segmentation**: Users have full control over the size and resolution of the analysis area.
 * **Suitability Scoring**: Automatic 0-100 rating for every grid cell based on multi-variable criteria.
 * **Infrastructure Context**: Automatically locates and visualizes the nearest energy storage or transmission points.
 * **Interactive Visualization**: A responsive map interface allowing deep exploration of potential sites.
## 🛠 Tech Stack

* **Frontend:** React 19, TypeScript, Vite, Leaflet, MapLibre
* **Backend:** Python, Django 5, Google Earth Engine (GEE), Geemap
* **Infrastructure:** PostgreSQL 15, Docker

## 📡 Data Sources
* **ERA5-Land** : Fetches hourly wind_speed, wind_direction, temperature_2m, and surface_pressure to calculate air density and wind power potential.
* **Copernicus** : Uses the GLO-30 (30m global) dataset to analyze elevation, slope, and terrain roughness (TRI) for site feasibility.
* **WorldCover v200** : Land Use: Analyzes land classification at 10m resolution to automatically filter out unsuitable areas (e.g., water bodies, urban zones, protected wetlands).

## 🚀 Installation
Prerequisites
 * Docker Desktop installed
 * Python 3.9+
 * Google Earth Engine Account (for API authentication)

Quick Start
```
1.
# Install the library locally if you haven't already
pip install earthengine-api

# Run the authentication flow (opens a browser window)
earthengine authenticate

2. Clone the repository
git clone https://github.com/bbeatricecretu/RoSpin
cd RoSpin

3. Run with Docker
docker-compose up --build

4. Access the App
Open your browser and navigate to http://localhost:5173
```
