# Digital Twin Cloud Platform for Smart Campus Sustainability Analytics

A Flask-backed sustainability analytics dashboard for four campus buildings, using simulated CSV data, formula-based BSEI, a Random Forest model artifact, and a separately tested AWS sensor-processing pipeline.

## Project
- **Team member:** Preetham H (24BIT0294)
- **Buildings:** Academic, Hostel, Main, Placement
- **Backend/frontend:** Python Flask; HTML, CSS, JavaScript
- **AWS demo:** AWS IoT Core → Lambda (`DigitalTwinDataProcessor`) → Amazon S3 and CloudWatch Logs

## Implemented functionality
- Flask API-backed dashboard: campus analytics use local CSV files; the live sensor section reads processed IoT records from S3 through Flask.
- Four simulated building datasets with 61 daily records each, covering 2026-08-01 through 2026-09-30 (244 records total when regenerated from the current configuration).
- BSEI calculation, component-efficiency comparisons, alerts/recommendations, and a prediction endpoint.
- Prediction endpoint blends model prediction (60%) and formula-based BSEI (40%).
- Separately tested AWS IoT Core rule routes `campus/sensors/#` messages to `DigitalTwinDataProcessor`; processed results are written to S3 and execution logs to CloudWatch Logs.

**Scope note:** CSV analytics remain local. The Live AWS Sensor Data section uses the separately configured IoT Core → Lambda → S3 pipeline via the read-only Flask S3 endpoint documented below.

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

To validate Python, AWS identity, S3 access to the processed-data prefix, and port 5000 before starting Flask, run this from PowerShell:
```powershell
.\start-dashboard.ps1
```
If AWS Academy Learner Lab credentials are missing or expired, refresh them in the Learner Lab and configure the AWS CLI credential chain before rerunning the script. It will not start another Flask instance when port 5000 is already occupied.

Run tests:
```powershell
python -m unittest discover -s .\src\backend -p "test_app.py" -v
```
The current backend suite includes the Flask API contract, CSV dataset checks, and mocked S3 endpoint tests.

## Live AWS sensor data

The dashboard's **Live AWS Sensor Data** section calls Flask's `GET /api/aws-data` endpoint. The endpoint reads the newest JSON objects (up to 50) under `processed-data/` in bucket `digital-twin-campus-2026-preetham`, region `us-east-1`, then displays the latest reading per building. It uses boto3's standard credential provider chain; no access keys are stored in the application.

Configure local AWS access with an AWS profile (or use an attached IAM role in the deployment environment):
```powershell
aws configure --profile campus-dashboard
$env:AWS_PROFILE = "campus-dashboard"
aws sts get-caller-identity
```
The selected identity needs `s3:ListBucket` on the bucket, constrained to the `processed-data/` prefix, and `s3:GetObject` on `arn:aws:s3:::digital-twin-campus-2026-preetham/processed-data/*`. Start Flask in the same PowerShell session so it inherits `AWS_PROFILE`. If the profile uses temporary credentials, refresh the access key, secret key, and session token together when the session expires; boto3 does not refresh credentials copied directly into the shared credentials file. The API returns HTTP 503 for missing or expired credentials and HTTP 403 for S3 access denial, with the AWS error code and request ID in the response and backend log. Refresh in the dashboard or call:
```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/aws-data
```
An empty prefix produces an empty record list. Malformed JSON objects are skipped and counted in the response; missing AWS credentials and S3/API errors are returned as explicit endpoint errors.

The **AWS Sensor Trends** section uses `GET /api/aws-data/history?limit=500`, which returns the newest processed JSON records (maximum 1,000 per request), sorted by sensor timestamp chronologically, and indicates whether more records exist. The browser filters to Academic, Hostel, Main, and Placement and charts only available measurements. Records without a valid sensor timestamp are omitted from plots; optional temperature and CO₂ charts appear only when those measurements are present. Chart.js is already loaded by the dashboard, so no new frontend dependency is required. Trend coverage is limited to the records currently retained in S3 and the per-request limit; no historical values are generated.

## Technology and limitations
- Flask/Python, HTML/CSS/JavaScript, scikit-learn model artifact.
- AWS demo pipeline: IoT Core, Lambda, S3, and CloudWatch Logs. The live dashboard S3 endpoint requires valid local AWS credentials or an IAM role with the permissions above.
- Architecture documents may discuss RDS, IoT TwinMaker, SageMaker, QuickSight, Cognito, and SNS, but these are not claimed as deployed/integrated features unless separately verified.

## Repository map
`architecture/` diagrams; `aws/` cloud resources; `database/` database documentation; `dataset/` CSVs; `docs/` reports; `images/` visuals; `literature_survey/` research documents; `presentation/` slides; `references/` citations; `results/` evidence; `src/backend/` Flask/data logic/tests; `src/frontend/` dashboard; `src/ml_model/` model artifact.
