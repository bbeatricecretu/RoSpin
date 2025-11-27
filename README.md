#  Satelite Wind ROSPIN

## 🧭 Description

### Overview
Satelite Wind ROSPIN is a collaborative project focused on identifying and mapping the most suitable locations for installing wind farms. The project integrates satellite data analysis, cloud-based processing, and geospatial visualization.

### Goal
To build an application that automatically processes satellite data using Google Earth Engine to evaluate wind energy potential across different regions. The system helps users visualize optimal wind farm sites based on environmental, geographic, and infrastructural criteria.

The user provides input such as:

- A **set of coordinates** (a point and a range), **or**
- A **city or region name**, with **minimum yearly energy output** or **minimum wind speed** requirements.

Based on this input, the system generates a **list of suitable locations** for wind farms.  
Each result in the list includes:

- **Rating** — an overall suitability score for wind energy generation.  
- **Nearest Energy Accumulation or Storage Point** — the closest facility or area for efficient energy storage or transmission.

When the user selects one of the locations, an **interactive map** will open, highlighting that area along with its geographic and infrastructural context.

---

## ⚙️ Core Components
- 🛰 **Data Collection:** Satellite datasets (wind speed, elevation, land use, environment).  
- ⚙️ **Data Processing:** Using **ESA SNAP**, **Google Earth Engine**, and custom Python scripts.  
- 🧠 **Analysis Engine:** Suitability analysis, thresholds, ML-based scoring.  
- 🌍 **Front-End Application:** Interactive map for exploring results.  
- ☁️ **Cloud Integration:** **Google Cloud Platform** for storage, APIs, and collaboration.  
- 🐳 **Deployment:** Docker for containerization; Kubernetes optional for orchestration.  
- 🧩 **Collaboration:** Multi-member team (front-end, back-end, data, deployment).

---

## 🧾 Short Summary
> “Satelite Wind ROSPIN uses satellite data and cloud computing to map the best areas for wind farms. It combines ERA5 with Earth Engine processing, data analysis, and an interactive map deployed via Docker and Google Cloud.”


---

## ⚙️ FULL SETUP (FIRST TIME ONLY)


### 1️⃣ Clone the project and build containers
```bash
git clone https://github.com/bbeatricecretu/RoSpin.git
cd RoSpin
docker compose up --build
```
### 2️⃣ Apply migrations and create admin user
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser   # (create your login)
```
### 3️⃣ Authenticate Google Earth Engine
```bash
docker compose exec web bash
earthengine authenticate      # follow the link → log in → copy verification code
exit
```
### 4️⃣ Generate region zones
```bash
python main.py    # ✅ region_zones.geojson generated successfully.
```
### 5️⃣ Create first region in Django shell
```bash
docker compose exec web python manage.py shell
from analysis.models import Point, Region
center = Point.objects.create(lat=46.77 , lon=23.62)
region = Region.objects.create(center=center)
print(region.id)   # (should show a number, e.g. 1)
exit()
```
### 6️⃣ Generate zones and fetch GEE data
```bash
docker compose exec web python manage.py generates_zones
docker compose exec web python manage.py fetch_gee_data
```
### 7️⃣ Register models in the admin panel
```python
# (open RoSpin/analysis/admin.py and add:)
 from django.contrib import admin
 from .models import Region, Zone, Point, Infrastructure, EnergyStorage
 admin.site.register(Region)
 admin.site.register(Zone)
 admin.site.register(Point)
 admin.site.register(Infrastructure)
 admin.site.register(EnergyStorage)
```

### 8️⃣ Restart the containers
```bash
docker compose down
docker compose up
```
### 9️⃣ Open the app in your browser
Go to http://localhost:8000/admin
 Log in with the user you created earlier (e.g., sefu / rospin2025)

---

 ## 🔁 RELOAD / UPDATE (EACH TIME YOU WORK) 

### Option 1 — Update your local code
```bash
git pull origin main https://github.com/bbeatricecretu/RoSpin.git
```

### Option 2 — If you want a clean restart (delete and re-clone)
```bash
rm -rf RoSpin
git clone git https://github.com/bbeatricecretu/RoSpin.git
cd RoSpin
docker compose up --build
```

### Restart the containers (to reload the latest version)
```bash
docker compose down
docker compose up
```

### Open the admin panel again
👉 http://localhost:8000/admin

---

## 🌿 --- GIT WORKFLOW (ALL COMMANDS) ---
---
### 1️⃣ Clone the repository (first time)
```bash
git clone https://github.com/bbeatricecretu/RoSpin.git
cd RoSpin
```

### 2️⃣ Check current branch
```bash
git branch
```

### 3️⃣ Switch to an existing branch
```bash
git checkout branch-name
```

### 4️⃣ Create and switch to a new branch
```bash
git checkout -b new-branch-name
```
### 5️⃣ Pull latest updates from the main branch
```bash
git pull origin main
```
### 6️⃣ Stage all your changes
```bash
git add .
```
### 7️⃣ Commit your changes with a message
```bash
git commit -m "Describe what you changed"
```
### 8️⃣ Push your changes to a specific branch
```bash
git push origin branch-name
```
### 9️⃣ If it's a new branch (first push)
```bash
git push -u origin new-branch-name
```
### 🔁 Update local project with latest code (daily use)
```bash
git pull origin main
```
