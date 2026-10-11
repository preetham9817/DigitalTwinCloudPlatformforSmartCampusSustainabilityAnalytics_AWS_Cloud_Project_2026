# Results and Validation

The backend test suite was last recorded as passing 20 tests. Re-run from the repository root to confirm current status:

```powershell
python -m unittest discover -s .\src\backend -p "test_app.py" -v
```

The configured generated dataset has four buildings with 61 daily records each from 2026-08-01 through 2026-09-30 (244 records total when regenerated). Previously recorded public-BSEI model metrics were MAE 1.0979, MSE 2.2184, RMSE 1.4894, R² 0.8956, and cross-validation R² 0.8838 ± 0.0509; rerun evaluation before citing as current. The AWS IoT Core → Lambda → S3/CloudWatch flow was tested separately and does not establish that the local dashboard consumes live AWS data.
