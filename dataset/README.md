# Dataset Repository

Contains simulated IoT time-series datasets for the four configured buildings: Academic, Hostel, Main, and Placement.

| File | Description |
|---|---|
| `academic_building_sensor_data.csv` | Academic-building readings |
| `hostel_building_sensor_data.csv` | Hostel/residential readings |
| `main_building_sensor_data.csv` | Main-building readings |
| `placement_building_sensor_data.csv` | Placement/training-building readings |
| `combined_sensor_data.csv` | Combined records, when generated/present |
| `dataset_description.md` | Dataset field documentation, when present |

The current generated building CSVs cover 2026-08-01 through 2026-09-30: 61 daily records per building, 244 records total. Regenerate/check files before relying on counts. These are simulated data, not measurements from physical campus sensors.

## Common fields
Timestamp, building identifier, energy consumption, water consumption, temperature, humidity, CO₂ level, occupancy, and sustainability score. Confirm the exact header against the current CSVs.

## BSEI weights
- Energy efficiency: 45%
- Water efficiency: 35%
- Environmental efficiency: 20%

Timestamps use `DD-MM-YYYY`. Building Performance consumption/occupancy values are per-record means; building BSEI is a mean of per-record scores. Campus KPI and historical-trend energy, water, and occupancy use daily totals; campus KPI cards average those daily totals across dates. Temperature, humidity, CO₂, and BSEI are means. Alerts compare BSEI and component efficiencies with campus-building means, not hidden normalization constants as external thresholds.
