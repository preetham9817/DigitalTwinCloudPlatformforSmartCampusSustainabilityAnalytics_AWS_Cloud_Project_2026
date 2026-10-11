## Results and Validation

### 1. Backend Testing
The backend test suite successfully passed **20 tests** during the last recorded run. To verify the current status, execute the following command from the repository root:

```powershell
python -m unittest discover -s .\src\backend -p "test_app.py" -v
```

### 2. Dataset Generation
The system is configured to generate sensor datasets for four campus buildings: Academic, Hostel, Main, and Placement. The generated dataset contains 61 daily records per building for the period from August 1 to September 30, 2026, resulting in **244 records** across all four buildings when regenerated.

### 3. Machine Learning Model Evaluation
The previously recorded evaluation metrics for the public BSEI prediction model are:

| Metric | Recorded Value |
|---|---:|
| Mean Absolute Error (MAE) | 1.0979 |
| Mean Squared Error (MSE) | 2.2184 |
| Root Mean Squared Error (RMSE) | 1.4894 |
| R² Score | 0.8956 |
| Cross-validation R² | 0.8838 ± 0.0509 |

These values represent previously recorded results and should be revalidated before being reported as the current model performance.

### 4. AWS Pipeline Validation
The AWS IoT Core → AWS Lambda → Amazon S3 and CloudWatch pipeline was tested separately. This validates the cloud-based sensor-data processing workflow; it does not establish a direct connection between the AWS pipeline and the local Flask dashboard.
