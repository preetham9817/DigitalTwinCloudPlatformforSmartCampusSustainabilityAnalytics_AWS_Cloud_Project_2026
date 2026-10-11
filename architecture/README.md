# Architecture

Contains architecture diagrams for the Digital Twin Cloud Platform for Smart Campus Sustainability Analytics.

- `AWS Cloud Architecture.png` — planned AWS service architecture.
- `Complete System Architecture.png` — broader sensor-to-analytics workflow.

The verified cloud demonstration routes AWS IoT Core messages to `DigitalTwinDataProcessor`, then stores processed output in S3 and logs execution in CloudWatch Logs. The local Flask dashboard reads local CSV data; the diagrams do not prove a live cloud-to-dashboard connection.
