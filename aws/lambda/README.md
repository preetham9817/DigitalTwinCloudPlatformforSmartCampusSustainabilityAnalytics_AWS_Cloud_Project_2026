# AWS Lambda

Contains Lambda code and artifacts for the campus sensor-processing demonstration.

## Verified function
`DigitalTwinDataProcessor` is a Python 3.10 Lambda function with handler `lambda_function.lambda_handler`. IoT rule `CampusSensorToLambda` routes messages from `campus/sensors/#` to this function. It processes sensor JSON, calculates sustainability metrics, writes processed output to S3, and logs execution details to CloudWatch Logs.

- Region: `us-east-1`
- S3 bucket: `digital-twin-campus-2026-preetham`
- Log group: `/aws/lambda/DigitalTwinDataProcessor`

Treat `sensor_processor.py`, `sustainability_score.py`, and `anomaly_detector.py` as planned names unless those files are present and implemented.
