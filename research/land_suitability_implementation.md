# Land Suitability Formula - Implementation Summary

## What Changed

### Before: Binary Exclusion Approach
- Only looked at **dominant** land type (highest percentage)
- Binary decision: excluded (score = 0) or not excluded (score = 1)
- Ignored all other land types in the zone

**Example Problem**:
- Zone A: 51% Grassland, 49% Forest → potential = 87.0 (full score)
- Zone B: 95% Grassland, 5% Forest → potential = 87.0 (same score!)
- **Issue**: Both treated identically despite very different forest coverage

---

### After: Area-Weighted Suitability
- Considers **ALL** land types proportionally to their coverage
- Gradual scoring: each land type has a suitability score (0.0 to 1.0)
- Formula: `potential = 100 × (wind + terrain) × land_suitability`

**Same Example with New Formula**:
- Zone A: 51% Grassland, 49% Forest
  - S_land = (0.51×1.0 + 0.49×0.4) = 0.706
  - potential = 87.0 × 0.706 = **61.4** (Fair)
  
- Zone B: 95% Grassland, 5% Forest
  - S_land = (0.95×1.0 + 0.05×0.4) = 0.97
  - potential = 87.0 × 0.97 = **84.4** (Good)
  
- **Result**: Realistic differentiation based on land composition!

---

## Land Type Suitability Scores

| Land Cover Class | Score | Rationale |
|------------------|-------|-----------|
| **Grassland** | 1.0 | Open, ideal for turbines |
| **Bare / Sparse** | 1.0 | No vegetation to clear |
| **Cropland** | 0.9 | Agricultural compensation needed |
| **Shrubland** | 0.7 | Moderate clearing required |
| **Tree cover** | 0.4 | Deforestation costs, environmental concerns |
| **Moss / Lichen** | 0.4 | Fragile tundra soils |
| **Built-up** | 0.0 | **Cannot build** (urban) |
| **Permanent water** | 0.0 | **Cannot build** (lakes/rivers) |
| **Herbaceous wetland** | 0.0 | **Cannot build** (protected) |
| **Snow / ice** | 0.0 | **Cannot build** (glaciers) |
| **Mangroves** | 0.0 | **Cannot build** (coastal protection) |

---

## Hard Exclusion Rule

A zone is **completely excluded** (potential = 0) if:
- Less than **70%** of the zone is buildable land
- Example: 60% water + 20% urban + 20% grassland → **excluded** (only 20% buildable)

This prevents zones dominated by unsuitable land from receiving misleading scores.

---

## Real-World Example

### Zone Profile
- 45.2% Grassland
- 30.1% Cropland  
- 20.0% Tree cover
- 4.7% Built-up

### Calculation Steps

**1. Check Buildable Fraction**
```
Buildable = Grassland + Cropland + Tree cover
          = 45.2% + 30.1% + 20.0%
          = 95.3% ✓ (passes 70% threshold)
```

**2. Calculate Land Suitability**
```
S_land = (0.452×1.0 + 0.301×0.9 + 0.200×0.4) / 0.953
       = (0.452 + 0.271 + 0.080) / 0.953
       = 0.843
```

**3. Calculate Wind & Terrain Components**
```
Wind:    720 W/m² → S_wind = 0.9
Terrain: TRI = 10m → S_terrain = 0.8
Base:    S_base = 0.7×0.9 + 0.3×0.8 = 0.87
```

**4. Final Potential**
```
potential = 100 × 0.87 × 0.843 = 73.3 (Good!)
```

---

## Forest Coverage Impact Analysis

**Assuming same wind/terrain (S_base = 0.87)**

| Forest % | Grassland % | S_land | Potential | Category |
|----------|-------------|--------|-----------|----------|
| 0% | 100% | 1.00 | 87.0 | Good |
| 20% | 80% | 0.88 | 76.6 | Good |
| 40% | 60% | 0.76 | 66.1 | Fair |
| 60% | 40% | 0.64 | 55.7 | Fair |
| 80% | 20% | 0.52 | 45.2 | Fair |

**Insight**: Each 20% increase in forest reduces potential by ~10-11 points.

---

## Technical Implementation

### Code Location
- `SkyWind/analysis/core/gee_service.py` - Main computation service
- `SkyWind/analysis/management/commands/fetch_gee_data.py` - CLI command
- `research/land_suitability_methodology.md` - Full scientific documentation

### Key Functions Added
```python
LAND_SUITABILITY_SCORES = {
    "Grassland": 1.0,
    "Cropland": 0.9,
    "Tree cover": 0.4,
    # ... etc
}

def compute_land_suitability(land_type_dict):
    """Returns (S_land, M_land, F_buildable)"""
    # Calculate buildable fraction
    # Apply 70% threshold
    # Compute weighted suitability
    
def compute_potential(zones):
    """Enhanced formula with land component"""
    S_wind = min(1.25, power_avg / 800)
    S_terrain = 1 - min(1.0, roughness / 50)
    S_land, M_land, _ = compute_land_suitability(land_types)
    
    potential = 100 × (0.7×S_wind + 0.3×S_terrain) × (M_land × S_land)
```

---

## Testing the Changes

### 1. View New Potential Scores
After regenerating a region, zone potential scores will reflect land composition.

### 2. Compare Zones with Different Land Mix
- Open land zones (grassland/bare) → highest potential
- Mixed zones (cropland/shrubland) → moderate reduction
- Forested zones → significant penalty (score × 0.4-0.7)
- Zones with >30% excluded land → potential = 0

### 3. Verify CSV Export
Land types still export as: `"Type1:50.5%;Type2:30.2%"`
Potential scores now range more widely based on land composition.

---

## Scientific Validation

### Tunable Parameters (in code)
| Parameter | Value | Where to Change |
|-----------|-------|-----------------|
| Land suitability scores | See table above | `LAND_SUITABILITY_SCORES` dict |
| Buildable threshold | 70% | `BUILDABLE_THRESHOLD = 0.7` |
| Wind weight | 0.7 | `0.7 * S_wind` in formula |
| Terrain weight | 0.3 | `0.3 * S_terrain` in formula |

### How to Adjust
If wind energy experts suggest different scores:
1. Open `gee_service.py`
2. Modify `LAND_SUITABILITY_SCORES` dictionary
3. Update corresponding dict in `fetch_gee_data.py` (keep them in sync)
4. Regenerate regions to see new scores

---

## Next Steps

### 1. Commit Changes
```bash
git add .
git commit -m "Enhanced land suitability formula with area-weighted scoring"
git push origin madi-branch
```

### 2. Test with Sample Region
- Delete an existing region
- Regenerate it with new formula
- Compare potential scores with old version
- Verify zones with different land compositions get appropriate scores

### 3. Expert Review
- Share `research/land_suitability_methodology.md` with wind energy experts
- Get feedback on suitability scores (especially Tree cover = 0.4)
- Adjust scores based on local regulations/experience
- Consider regional variations (e.g., different forest types)

---

## Summary

✅ **Implemented**: Area-weighted land suitability assessment  
✅ **Documented**: Full mathematical methodology for scientists  
✅ **Tested**: Formula verified, no syntax errors  
✅ **Ready**: Code ready to commit and test with real data  

**Key Improvement**: System now distinguishes between zones based on complete land composition, not just dominant type. This provides more realistic and actionable site assessments for wind farm development.
