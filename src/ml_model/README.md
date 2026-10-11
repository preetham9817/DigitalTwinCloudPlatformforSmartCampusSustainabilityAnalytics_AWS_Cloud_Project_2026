# Machine Learning Model

Contains the local model artifact used by the backend for sustainability prediction.

The prediction endpoint blends model output (60%) with formula-based BSEI (40%). Previously recorded evaluation on the public BSEI dataset:

| Metric | Recorded value |
|---|---:|
| MAE | 1.0979 |
| MSE | 2.2184 |
| RMSE | 1.4894 |
| R² | 0.8956 |
| Cross-validation R² | 0.8838 ± 0.0509 |

These are historical results; rerun evaluation against the current artifact and dataset before presenting them as current. The documented feature set includes energy/water consumption and coverage, environmental readings, relative resource values, component efficiencies, and calendar features. Confirm the actual training script before changing features. SageMaker hosting/training is not claimed as implemented; the current application uses a local model artifact.
