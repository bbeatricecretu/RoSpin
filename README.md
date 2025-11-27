Satellite Wind ROSPIN is a collaborative geospatial intelligence tool designed to map optimal locations for wind energy infrastructure. By integrating Google Earth Engine and Open-Meteo data, the application allows users to analyze specific regions for wind energy suitability based on environmental conditions and proximity to energy storage.
📋 Table of Contents
 * System Architecture
 * How It Works
 * Key Features
 * Tech Stack
 * Data Sources
 * Installation
🏗 System Architecture
The system aggregates data from multiple satellite providers, processes it via a Python backend, and renders the results on an interactive frontend map.
> ![PLACEHOLDER: Architecture Diagram]
> Recommendation: A diagram showing the flow of data: User Input -> Python API -> Fetching Data (GEE/Open-Meteo) -> Processing -> React Frontend.
> 
⚙️ How It Works
1. Define the Zone
The user inputs specific coordinates and dimensions to define the Area of Interest (AOI).
 * Latitude & Longitude: Center point of the search.
 * Side (km): The width of the square zone.
 * Grid Split: The granularity of the analysis (e.g., splitting the zone into a 5x5 grid).
> ![PLACEHOLDER: Screenshot of Input Form]
> Recommendation: A screenshot of your sidebar or modal where the user types in the coordinates and grid parameters. This shows the user interface is clean and usable.
> 
2. Automated Analysis
The system divides the defined area into the requested grid cells. For each cell, it queries satellite data to calculate:
 * Average wind speed consistency.
 * Terrain suitability (elevation/slope).
 * Distance to the nearest infrastructure.
3. Visualizing Results
The application generates a heatmap overlay on the map. Users can click on specific grid cells to view detailed metrics and the Nearest Energy Accumulation Point.
> ![PLACEHOLDER: Interactive Map Screenshot]
> Recommendation: The "Money Shot." A screenshot of the map with the grid overlay colored by suitability (e.g., green for good, red for bad) and a popup open showing details for one specific cell.
> 
✨ Key Features
 * Dynamic Grid Segmentation: Users have full control over the size and resolution of the analysis area.
 * Suitability Scoring: Automatic 0-100 rating for every grid cell based on multi-variable criteria.
 * Infrastructure Context: Automatically locates and visualizes the nearest energy storage or transmission points.
 * Interactive Visualization: A responsive map interface allowing deep exploration of potential sites.
🛠 Tech Stack
| Component | Technology | Description |
|---|---|---|
| Data Processing | Python, Pandas | Core logic for grid calculations and data aggregation. |
| Geospatial Engine | Google Earth Engine (GEE) | Retrieval of land surface and terrain data. |
| Meteorology | Open-Meteo API | Real-time and historical wind speed data. |
| Frontend | React / Leaflet | Interactive map interface. |
| Containerization | Docker | Consistent environment deployment. |
📡 Data Sources
This project relies on the following open-science platforms:
 * Google Earth Engine — Visit Platform
   * Primary source for terrain and environmental layers.
 * Open-Meteo — Visit Platform
   * Source for wind speed and meteorological trends.
 * Copernicus Climate Data Store (CDS) — Visit Platform
   * Advanced historical climate data (ERA5).
🚀 Installation
Prerequisites
 * Docker Desktop installed
 * Python 3.9+
 * Google Earth Engine Account (for API authentication)
Quick Start
1. Clone the repository
git clone https://github.com/your-username/satellite-wind-rospin.git
cd satellite-wind-rospin

2. Set up Environment Variables
Create a .env file in the root directory:
GEE_API_KEY=your_key_here
OPEN_METEO_API_KEY=optional_if_needed

3. Run with Docker
docker-compose up --build

4. Access the App
Open your browser and navigate to http://localhost:5173