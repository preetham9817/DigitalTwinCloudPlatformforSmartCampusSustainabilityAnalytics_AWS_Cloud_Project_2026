# Digital Twin Cloud Platform for Smart Campus Sustainability Analytics

A Flask-backed sustainability analytics dashboard for four campus buildings, using simulated CSV data, formula-based BSEI, a Random Forest model artifact, and a separately tested AWS sensor-processing pipeline.

## Project
- **Team member:** Preetham H (24BIT0294)
- **Buildings:** Academic, Hostel, Main, Placement
- **Backend/frontend:** Python Flask; HTML, CSS, JavaScript
- **AWS demo:** AWS IoT Core → Lambda (`DigitalTwinDataProcessor`) → Amazon S3 and CloudWatch Logs

## Implemented functionality
- Local dashboard and Flask API backed by local CSV files.
- Four simulated building datasets with 61 daily records each, covering 2026-08-01 through 2026-09-30 (244 records total when regenerated from the current configuration).
- BSEI calculation, component-efficiency comparisons, alerts/recommendations, and a prediction endpoint.
- Prediction endpoint blends model prediction (60%) and formula-based BSEI (40%).
- Separately tested AWS IoT Core rule routes `campus/sensors/#` messages to `DigitalTwinDataProcessor`; processed results are written to S3 and execution logs to CloudWatch Logs.

**Scope note:** The local Flask dashboard reads local CSV data. The AWS pipeline is a separate cloud demonstration; a live AWS-to-dashboard connection is not claimed.

## BSEI weights
| Component | Weight |
|---|---:|
| Energy efficiency | 45% |
| Water efficiency | 35% |
| Environmental efficiency | 20% |

Priorities are based on BSEI and component efficiencies relative to campus-building means. Internal normalization constants are not external alert thresholds.

## Dataset
- `dataset/academic_building_sensor_data.csv`
- `dataset/hostel_building_sensor_data.csv`
- `dataset/main_building_sensor_data.csv`
- `dataset/placement_building_sensor_data.csv`

Source timestamps use `DD-MM-YYYY`. Building Performance energy, water, and occupancy values are per-record means; building BSEI is the mean of per-record scores. Campus KPI and historical-trend energy, water, and occupancy use daily totals (averaged across dates for campus KPI cards). Temperature, humidity, CO₂, and BSEI are means.

## Run locally
From repository root:
```powershell
python .\src\backend\app.py
```
Open `http://127.0.0.1:5000`.

Run tests:
```powershell
python -m unittest discover -s .\src\backend -p "test_app.py" -v
```
The last recorded test run had 20 passing tests; rerun to confirm current status.

## Technology and limitations
- Flask/Python, HTML/CSS/JavaScript, scikit-learn model artifact.
- Verified AWS demo: IoT Core, Lambda, S3, CloudWatch Logs.
- Architecture documents may discuss RDS, IoT TwinMaker, SageMaker, QuickSight, Cognito, and SNS, but these are not claimed as deployed/integrated features unless separately verified.

## Repository map
`architecture/` diagrams; `aws/` cloud resources; `database/` database documentation; `dataset/` CSVs; `docs/` reports; `images/` visuals; `literature_survey/` research documents; `presentation/` slides; `references/` citations; `results/` evidence; `src/backend/` Flask/data logic/tests; `src/frontend/` dashboard; `src/ml_model/` model artifact.
