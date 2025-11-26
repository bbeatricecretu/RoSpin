# Test Files

This directory contains diagnostic and test scripts for the SkyWind project.

## Files

### Zone & Data Testing
- **`check_zones.py`** - Check zone statistics and land cover data in database
- **`diagnose_landcover.py`** - Detailed diagnostic for land cover fetching issues
- **`verify_fix.py`** - Verify that previously empty zones now have complete data
- **`test_comparison.py`** - Test floating-point comparison issues
- **`test_region_grid.py`** - Test region grid generation

### Infrastructure Testing
- **`test_infrastructure.py`** - Test infrastructure detection for zones

## Usage

Run tests from the project root using Docker:

```bash
# Pre-flight check before fetching data
docker compose exec web python tests/preflight_check.py

# Check zone statistics
docker compose exec web python tests/check_zones.py

# Verify data completeness
docker compose exec web python tests/verify_fix.py
```

## Notes

These are **diagnostic scripts**, not automated test suites. They were created during development to debug specific issues and can be safely deleted if no longer needed.
