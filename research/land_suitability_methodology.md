# Enhanced Land Suitability Methodology for Wind Farm Site Assessment

## Overview

This document describes the mathematical framework for incorporating land cover composition into wind farm potential scoring, replacing the previous binary exclusion approach with a nuanced, area-weighted suitability assessment.

---

## 1. Current Implementation Summary

The potential scoring system evaluates three independent dimensions:

1. **Wind Resource** (70% weight)
2. **Terrain Characteristics** (30% weight)  
3. **Land Cover Suitability** (multiplicative factor)

### Formula

```
potential = 100 × S_base × F_land
```

Where:
- **S_base** = 0.7 × S_wind + 0.3 × S_terrain  
  Base score combining wind and terrain factors

- **F_land** = M_land × S_land  
  Combined land factor (hard mask × suitability)

---

## 2. Wind Resource Component (S_wind)

**Source**: ERA5 Reanalysis, 100m wind data  
**Metric**: Wind Power Density (WPD)

```
S_wind = min(1.25, power_avg / 800)
```

**Normalization**:
- Reference: 800 W/m² (threshold for "Good" wind resource)
- Values > 1000 W/m² capped at 1.25 (exceptional sites)
- Range: [0, 1.25]

**Wind Class Guidelines** (IEC 61400-1):
| WPD (W/m²) | Class | S_wind |
|------------|-------|---------|
| < 300 | Poor | < 0.38 |
| 300-500 | Marginal | 0.38-0.63 |
| 500-800 | Fair | 0.63-1.00 |
| 800-1200 | Good | 1.00-1.25 |
| > 1200 | Excellent | 1.25 (capped) |

---

## 3. Terrain Component (S_terrain)

**Source**: Copernicus GLO-30 DEM  
**Metric**: Terrain Ruggedness Index (TRI)

```
S_terrain = 1 - min(1.0, roughness / 50)
```

**Interpretation**:
- roughness = Standard deviation of elevation in 11×11 window (30m resolution)
- S_terrain = 1.0 → Perfectly flat terrain (TRI = 0)
- S_terrain = 0.0 → Very rough terrain (TRI ≥ 50m)
- Range: [0, 1]

**Terrain Classification**:
| TRI (m) | Description | S_terrain | Impact |
|---------|-------------|-----------|---------|
| 0-5 | Flat | 0.90-1.00 | Minimal construction cost increase |
| 5-15 | Gentle | 0.70-0.90 | Moderate access challenges |
| 15-30 | Moderate | 0.40-0.70 | Significant engineering requirements |
| 30-50 | Rough | 0.00-0.40 | Major cost/feasibility concerns |
| > 50 | Very Rough | 0.00 | Generally prohibitive |

---

## 4. Land Cover Suitability Framework

### 4.1 Mathematical Model

For a zone covered by land classes *c ∈ C* with fractional areas *f_c*:

**Area-Weighted Suitability Index**:
```
S_land = Σ(f_c × s_c) / F_buildable
```

Where:
- **f_c** = fractional coverage of class *c* (percentage / 100)
- **s_c** = suitability score for class *c* ∈ [0, 1]
- **F_buildable** = total buildable fraction (area not in hard exclusions)

**Buildable Fraction**:
```
F_buildable = Σ f_c  for c ∉ {hard exclusion classes}
```

**Hard Exclusion Mask**:
```
M_land = 1  if F_buildable ≥ τ
         0  otherwise
```

Where **τ** = 0.7 (buildable threshold: 70% minimum)

---

### 4.2 Land Cover Suitability Scores

Based on ESA WorldCover v200 classification (11 classes):

| Land Cover Class | Symbol | s_c | Rationale |
|------------------|--------|-----|-----------|
| **Grassland** | G | 1.0 | Open terrain, ideal for development |
| **Bare / Sparse Vegetation** | B | 1.0 | Minimal clearing required |
| **Cropland** | C | 0.9 | Generally usable, agricultural compensation |
| **Shrubland** | S | 0.7 | Moderate clearing, slightly rougher |
| **Tree Cover (Forest)** | T | 0.4 | Deforestation concerns, access issues |
| **Moss & Lichen (Tundra)** | M | 0.4 | Fragile soils, permafrost challenges |
| **Built-up** | U | 0.0 | **Hard exclusion** — Urban areas |
| **Permanent Water** | W | 0.0 | **Hard exclusion** — Lakes, rivers |
| **Herbaceous Wetland** | H | 0.0 | **Hard exclusion** — Protected ecosystems |
| **Snow / Ice** | I | 0.0 | **Hard exclusion** — Glaciers, ice caps |
| **Mangroves** | Mg | 0.0 | **Hard exclusion** — Coastal protection |

**Design Principles**:
- **Hard exclusions** (s_c = 0.0): Physical or regulatory barriers
- **Soft preferences** (s_c > 0.0): Development feasibility gradients
- **Open land** (s_c = 1.0): Minimal environmental/economic constraints
- **Forested/Sensitive** (s_c = 0.4-0.7): Significant but not prohibitive challenges

---

### 4.3 Hard Exclusion Logic

A zone is **completely excluded** (potential = 0) if:

```
F_buildable < 0.7  (less than 70% buildable area)
```

This prevents zones dominated by unsuitable land from receiving misleadingly high scores.

**Example**:
- Zone with 40% water, 35% urban, 25% grassland
- F_buildable = 0.25 < 0.7
- M_land = 0 → potential = 0 (regardless of wind/terrain quality)

---

## 5. Worked Example

### Scenario: Mixed-Use Zone

**Land Composition**:
| Class | Percentage | f_c | s_c |
|-------|------------|-----|-----|
| Grassland | 45.2% | 0.452 | 1.0 |
| Cropland | 30.1% | 0.301 | 0.9 |
| Tree Cover | 20.0% | 0.200 | 0.4 |
| Built-up | 4.7% | 0.047 | 0.0 |

**Step 1: Calculate Buildable Fraction**
```
F_buildable = 0.452 + 0.301 + 0.200 = 0.953  (95.3%)
```

**Step 2: Check Hard Exclusion**
```
F_buildable = 0.953 ≥ 0.7  →  M_land = 1  ✓
```

**Step 3: Calculate Land Suitability**
```
S_land = (0.452×1.0 + 0.301×0.9 + 0.200×0.4) / 0.953
       = (0.452 + 0.271 + 0.080) / 0.953
       = 0.803 / 0.953
       = 0.843
```

**Step 4: Assume Other Components**
```
S_wind = 0.9    (720 W/m² wind power density)
S_terrain = 0.8 (moderate roughness)
```

**Step 5: Calculate Base Score**
```
S_base = 0.7 × 0.9 + 0.3 × 0.8
       = 0.63 + 0.24
       = 0.87
```

**Step 6: Apply Land Factor**
```
F_land = M_land × S_land = 1 × 0.843 = 0.843
```

**Step 7: Final Potential**
```
potential = 100 × 0.87 × 0.843 = 73.3
```

**Interpretation**: **Good** potential (70-100 range)
- Strong wind resource and favorable terrain
- Mostly open land (75% grassland/cropland)
- 20% forest coverage introduces moderate land constraints
- Small urban footprint (5%) does not trigger exclusion

---

## 6. Comparison with Previous Approach

### Old Method (Binary Dominant Class)
```python
dominant_land = "Grassland"  # Highest percentage
ok_land = 0 if dominant_land in EXCLUDED else 1
potential = 100 × (0.7×wpd + 0.3×rough) × ok_land
```

**Limitations**:
- Ignored composition of non-dominant classes
- Binary decision (1 or 0) — no gradation
- 49% forest + 51% grassland treated same as 5% forest + 95% grassland

### New Method (Area-Weighted Suitability)
```python
S_land = Σ(f_c × s_c) / F_buildable
F_land = M_land × S_land
potential = 100 × S_base × F_land
```

**Advantages**:
- **Proportional**: All land types contribute by coverage
- **Gradated**: Scores reflect land quality spectrum (0.0-1.0)
- **Transparent**: Explicit suitability scores (s_c) are scientifically tunable
- **Realistic**: 20% forest penalty differs from 60% forest penalty

---

## 7. Sensitivity Analysis

### Impact of Forest Coverage (holding wind/terrain constant)

| Forest % | Other Land | S_land | F_land | Potential |
|----------|------------|--------|--------|-----------|
| 0% | Grassland 100% | 1.00 | 1.00 | 87.0 |
| 20% | Grassland 80% | 0.88 | 0.88 | 76.6 |
| 40% | Grassland 60% | 0.76 | 0.76 | 66.1 |
| 60% | Grassland 40% | 0.64 | 0.64 | 55.7 |
| 80% | Grassland 20% | 0.52 | 0.52 | 45.2 |

*(Assumes S_base = 0.87 from example above)*

**Observation**: Each 20% increase in forest coverage reduces potential by ~10-11 points.

---

### Impact of Buildable Fraction on Hard Mask

| Buildable % | M_land | Effect on Potential |
|-------------|--------|---------------------|
| 90% | 1 | No exclusion (normal scoring) |
| 75% | 1 | No exclusion |
| **70%** | 1 | **Threshold** |
| 65% | 0 | **Complete exclusion** (potential = 0) |
| 50% | 0 | Complete exclusion |

**Critical Zone**: 65-75% buildable fraction
- Small changes in water/urban coverage can trigger exclusion
- Reflects reality: zones with 30%+ unsuitable land are not viable

---

## 8. Implementation Details

### Data Sources

1. **Land Cover**: ESA WorldCover v200 (2021)
   - Resolution: 10m
   - Method: Frequency histogram per zone → percentage distribution

2. **Wind**: ECMWF ERA5 Hourly
   - Resolution: ~25km
   - Variable: 100m wind components (u, v)

3. **Terrain**: Copernicus GLO-30 DEM
   - Resolution: 30m
   - Metric: TRI (standard deviation in 5-pixel radius)

### Computational Workflow

```python
def compute_potential(zone):
    # 1. Wind component
    S_wind = min(1.25, zone.power_avg / 800)
    
    # 2. Terrain component
    S_terrain = 1 - min(1.0, zone.roughness / 50)
    
    # 3. Land suitability
    S_land, M_land, F_buildable = compute_land_suitability(zone.land_type)
    
    # 4. Combined score
    S_base = 0.7 * S_wind + 0.3 * S_terrain
    F_land = M_land * S_land
    potential = 100 * S_base * F_land
    
    return round(potential, 1)
```

---

## 9. Scientific Validation & Calibration

### Tuneable Parameters

| Parameter | Symbol | Current Value | Purpose |
|-----------|--------|---------------|---------|
| Buildable threshold | τ | 0.7 (70%) | Hard exclusion cutoff |
| Wind weight | α_wind | 0.7 | Relative importance of wind resource |
| Terrain weight | α_terrain | 0.3 | Relative importance of terrain |
| WPD reference | WPD_ref | 800 W/m² | Normalization point for "Good" wind |
| TRI reference | TRI_ref | 50 m | Normalization point for roughness |
| Land scores | s_c | Table in §4.2 | Class-specific suitability |

### Recommended Validation Steps

1. **Expert Review**: Have wind energy developers review suitability scores (s_c)
2. **Case Study Comparison**: Apply to known successful/failed projects
3. **Sensitivity Testing**: Vary α weights and τ threshold
4. **Regional Calibration**: Adjust for local regulations (e.g., forest protection laws)
5. **Stakeholder Feedback**: Incorporate agricultural, environmental perspectives

---

## 10. Advantages of This Approach

### For Scientists
- **Explicit Assumptions**: All scores (s_c) and weights (α) are documented
- **Reproducible**: Deterministic calculation from satellite data
- **Extensible**: Easy to add new land classes or update scores
- **Comparable**: Normalized [0-100] scale allows cross-region comparison

### For Developers
- **Nuanced Ranking**: Distinguishes between "mostly grassland" vs "mixed forest"
- **Transparent Exclusions**: Clear why zones score 0 (below buildable threshold)
- **Risk Assessment**: Low S_land signals land acquisition challenges
- **Realistic Expectations**: Accounts for clearing costs and permitting complexity

### For Policymakers
- **Environmental Integration**: Protected areas naturally score 0.0
- **Land-Use Planning**: Identifies zones compatible with multiple uses (e.g., cropland)
- **Objective Criteria**: Reduces subjectivity in site selection
- **Scalable**: Same methodology applies nationally or globally

---

## 11. Future Enhancements

### Option B: Weighted Average (Alternative Formulation)

Instead of multiplicative land factor, treat land as third independent component:

```
S_combo = (α_wind × S_wind + α_terrain × S_terrain + α_land × S_land) / Σα
potential = 100 × S_combo × M_land
```

**Suggested weights**:
- α_wind = 0.6
- α_terrain = 0.2  
- α_land = 0.2

**Trade-offs**:
- More symmetric (all three on equal footing)
- Requires re-normalization of S_wind to [0,1] (currently [0,1.25])
- May need recalibration of interpretation thresholds

### Additional Factors

Consider incorporating:
1. **Grid Distance**: Proximity to transmission infrastructure
2. **Protected Areas**: Binary overlay (nature reserves, UNESCO sites)
3. **Population Density**: Social acceptance / noise constraints
4. **Slope Aspect**: Wind direction alignment (already captured in wind rose)
5. **Ice Loading**: Climate risk (Snow/Ice class partially addresses this)

---

## 12. References & Standards

- **IEC 61400-1**: Wind turbine design classes (wind resource classification)
- **ESA WorldCover**: [https://esa-worldcover.org/](https://esa-worldcover.org/)
- **ERA5 Documentation**: [https://cds.climate.copernicus.eu/](https://cds.climate.copernicus.eu/)
- **Wind Power Density Classes**: NREL Technical Report (Elliott et al., 1986)
- **TRI Methodology**: Riley et al. (1999), "A Terrain Ruggedness Index"

---

## Appendix A: Zone Potential Interpretation Guide

| Potential Score | Category | Color Code | Recommendation |
|-----------------|----------|------------|----------------|
| 0-20 | Poor | 🔴 Red | Not viable — exclude from planning |
| 20-40 | Marginal | 🟠 Orange | Low priority — feasibility study required |
| 40-70 | Fair | 🟡 Yellow | Moderate potential — detailed assessment needed |
| 70-100 | Good | 🟢 Green | High priority — strong development candidate |

---

## Appendix B: Example Zones

### Zone A: Ideal Grassland Site
- Land: 100% Grassland → S_land = 1.0, M_land = 1
- Wind: 950 W/m² → S_wind = 1.19
- Terrain: TRI = 3m → S_terrain = 0.94
- **Potential**: 100 × (0.7×1.19 + 0.3×0.94) × 1.0 = **111 → capped at 125** ✓

### Zone B: Mixed Forest/Cropland
- Land: 60% Forest, 40% Cropland → S_land = 0.60, M_land = 1
- Wind: 600 W/m² → S_wind = 0.75
- Terrain: TRI = 12m → S_terrain = 0.76
- **Potential**: 100 × (0.7×0.75 + 0.3×0.76) × 0.60 = **45.5** (Fair)

### Zone C: Coastal Urban (Excluded)
- Land: 50% Built-up, 30% Water, 20% Grassland → F_buildable = 0.20 < 0.7
- Wind: 1200 W/m² → S_wind = 1.25 (excellent wind!)
- Terrain: TRI = 2m → S_terrain = 0.96 (flat)
- **Potential**: 100 × ... × M_land(0) = **0** (excluded despite great wind)

---

**Document Version**: 1.0  
**Date**: December 9, 2025  
**Author**: Wind Farm Assessment System (RoSpin Project)  
**Status**: Implemented in production code
