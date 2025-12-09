# Enhanced Potential Formula - Quick Reference

## Formula

```
potential = 100 × S_base × F_land
```

Where:
- **S_base** = Wind + Terrain components (weighted average)
- **F_land** = Land suitability factor (hard mask × soft score)

---

## Components Breakdown

### 1. Wind Component (70% weight)
```
S_wind = min(1.25, power_avg / 800)
```
- Normalized to reference of 800 W/m² (good wind resource)
- Capped at 1.25 for exceptional sites (>1000 W/m²)

### 2. Terrain Component (30% weight)
```
S_terrain = 1 - min(1.0, roughness / 50)
```
- Based on Terrain Ruggedness Index (TRI)
- 1.0 = flat, 0.0 = very rough (TRI ≥ 50m)

### 3. Base Score
```
S_base = 0.7 × S_wind + 0.3 × S_terrain
```

### 4. Land Suitability Factor
```
F_land = M_land × S_land

where:
    F_buildable = Σ(percentage/100) for non-excluded land types
    
    M_land = 1  if F_buildable ≥ 0.7
             0  otherwise
    
    S_land = Σ(f_c × s_c) / F_buildable  for buildable classes
```

**Variables**:
- `f_c` = fractional coverage of land class c
- `s_c` = suitability score for class c (from table below)
- `F_buildable` = total buildable fraction (non-excluded area)
- `M_land` = hard exclusion mask (binary 0/1)

---

## Land Suitability Scores (s_c)

```python
SCORES = {
    "Grassland": 1.0,
    "Bare / sparse": 1.0,
    "Cropland": 0.9,
    "Shrubland": 0.7,
    "Tree cover": 0.4,
    "Moss / lichen": 0.4,
    "Built-up": 0.0,
    "Permanent water": 0.0,
    "Herbaceous wetland": 0.0,
    "Snow / ice": 0.0,
    "Mangroves": 0.0,
}
```

---

## Example Calculation

**Zone Data**:
- Land: 45% Grassland, 30% Cropland, 20% Forest, 5% Built-up
- Wind: 720 W/m²
- Terrain: TRI = 10m

**Step-by-step**:

1. **Wind**: S_wind = 720/800 = 0.9
2. **Terrain**: S_terrain = 1 - 10/50 = 0.8
3. **Base**: S_base = 0.7×0.9 + 0.3×0.8 = 0.87

4. **Buildable**: F_buildable = 0.45 + 0.30 + 0.20 = 0.95 ✓
5. **Hard mask**: M_land = 1 (since 0.95 ≥ 0.7)
6. **Land score**: 
   ```
   S_land = (0.45×1.0 + 0.30×0.9 + 0.20×0.4) / 0.95
          = 0.843
   ```
7. **Land factor**: F_land = 1 × 0.843 = 0.843

8. **Final**: potential = 100 × 0.87 × 0.843 = **73.3**

**Result**: Good potential (70-100 range)

---

## Comparison Table

| Scenario | S_base | F_land | Potential | Category |
|----------|--------|--------|-----------|----------|
| 100% Grassland | 0.87 | 1.00 | 87.0 | Good |
| 80% Grass, 20% Forest | 0.87 | 0.88 | 76.6 | Good |
| 50% Grass, 50% Forest | 0.87 | 0.70 | 60.9 | Fair |
| 30% Grass, 70% Urban | 0.87 | 0.00 | 0.0 | Excluded |

*(Assuming constant wind/terrain: S_base = 0.87)*

---

## Interpretation Scale

| Score | Category | Meaning |
|-------|----------|---------|
| 0 | Excluded | <70% buildable area OR no wind/terrain data |
| 1-20 | Poor | Not viable for development |
| 21-40 | Marginal | Low priority, feasibility study needed |
| 41-70 | Fair | Moderate potential, detailed assessment required |
| 71-100 | Good | High priority development candidate |

---

## Key Changes from Old Formula

### Old (Binary):
```
ok_land = 0 if dominant_land in EXCLUDED else 1
potential = 100 × S_base × ok_land
```

### New (Area-Weighted):
```
S_land = Σ(coverage × suitability) / buildable_area
F_land = M_land × S_land
potential = 100 × S_base × F_land
```

**Impact**: 
- Old: 51% forest = 49% forest (both get 0 or 1)
- New: Gradual penalty proportional to forest coverage
- More realistic for mixed land types
