# AWS Deployment Guide

## Project Name

Digital Twin Cloud Platform for Smart Campus Sustainability Analytics

---

## AWS Services Used

- AWS IoT Core
- AWS Lambda
- Amazon RDS (MySQL)
- Amazon S3
- AWS IoT TwinMaker
- Amazon SageMaker
- Amazon QuickSight
- Amazon Cognito
- AWS IAM
- Amazon SNS
- Amazon CloudWatch

---

## Deployment Workflow

1. IoT sensors generate real-time campus data.
2. AWS IoT Core receives sensor data.
3. AWS Lambda validates and processes incoming data.
4. Amazon RDS stores structured sensor information.
5. Amazon S3 stores historical datasets.
6. AWS IoT TwinMaker creates the Digital Twin.
7. Amazon SageMaker performs predictive analytics.
8. Amazon QuickSight generates dashboards.
9. Amazon SNS sends notifications.
10. Amazon CloudWatch monitors system health.

---

## Expected Outcome

The deployed platform provides real-time sustainability monitoring, Digital Twin visualization, predictive analytics, and resource optimization for smart campus management.
