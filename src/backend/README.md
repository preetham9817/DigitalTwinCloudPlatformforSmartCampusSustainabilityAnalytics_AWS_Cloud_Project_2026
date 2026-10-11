# Backend

Flask backend for the Digital Twin Cloud Platform for Smart Campus Sustainability Analytics.

## Responsibilities
- Serve dashboard data and analytics through Flask routes.
- Load and process local simulated building datasets.
- Calculate BSEI and component-efficiency metrics.
- Provide prediction functionality using the model artifact and formula-based BSEI.
- Generate datasets from configured buildings and run backend tests.

## BSEI and prediction
Formula-based BSEI weights: 45% energy efficiency, 35% water efficiency, 20% environmental efficiency. The prediction endpoint blends model prediction (60%) with formula-based BSEI (40%).

## Run
From repository root:
```powershell
python .\src\backend\app.py
```
Open `http://127.0.0.1:5000`.

Tests:
```powershell
python -m unittest discover -s .\src\backend -p "test_app.py" -v
```
The local backend uses CSV data; do not describe it as reading live S3/IoT data unless a tested integration has been added.
