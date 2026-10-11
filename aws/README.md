# AWS Resources

Contains AWS code, configuration, infrastructure resources, and deployment notes.

## Verified cloud flow
1. Sensor messages are published to `campus/sensors/#`.
2. Active IoT rule `CampusSensorToLambda` routes matching messages to Lambda `DigitalTwinDataProcessor`.
3. Lambda processes sensor JSON, calculates sustainability metrics, writes processed output to S3, and logs execution details to CloudWatch Logs.

The tested setup used region `us-east-1` and bucket `digital-twin-campus-2026-preetham`. The local Flask dashboard reads local CSV datasets; the AWS pipeline is a separate demonstration. Do not claim RDS, TwinMaker, SageMaker, QuickSight, Cognito, or SNS integration without verifying deployment and application integration.
