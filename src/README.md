# Source Code

- `backend/` — Flask API, BSEI logic, dataset configuration/generation, and tests.
- `frontend/` — HTML, CSS, and JavaScript dashboard.
- `ml_model/` — local machine-learning model artifact and related resources.

The local application reads CSV datasets. The AWS IoT Core → Lambda → S3/CloudWatch pipeline is a separate demonstration unless a direct dashboard integration is implemented and tested.
