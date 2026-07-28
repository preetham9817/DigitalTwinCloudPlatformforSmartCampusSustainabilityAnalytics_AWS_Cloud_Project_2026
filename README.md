# Digital Twin Cloud Platform for Smart Campus Sustainability Analytics

## Project Title

Digital Twin Cloud Platform for Smart Campus Sustainability Analytics

---

## Team Members

| Name | Registration Number |
|------|---------------------|
| Preetham H | 24BIT0294 |

---

## Problem Statement

University campuses generate large volumes of operational data related to energy consumption, water usage, environmental conditions, and occupancy. Existing campus management systems often monitor these resources independently, making it difficult to obtain a unified view of sustainability performance. This project proposes a cloud-based Digital Twin platform that integrates multiple campus resources into a single virtual environment, enabling centralized monitoring, predictive analytics, sustainability assessment, and informed decision-making.

---

## Objectives

- Develop a cloud-based Digital Twin platform for smart campus sustainability.
- Integrate energy, water, occupancy, and environmental sensor data.
- Generate a dynamic Campus Sustainability Score.
- Forecast resource consumption using predictive analytics.
- Detect abnormal resource usage and generate alerts.
- Provide interactive dashboards for sustainability monitoring and decision support.

---

## Proposed Architecture / Framework

The proposed system collects real-time IoT sensor data from campus buildings using AWS IoT Core. AWS Lambda processes incoming data before storing it in Amazon RDS and Amazon S3. AWS IoT TwinMaker creates a virtual Digital Twin of campus infrastructure, while Amazon SageMaker performs predictive analytics. Amazon QuickSight visualizes sustainability metrics through dashboards. Amazon Cognito manages user authentication, AWS IAM controls secure access, Amazon SNS delivers notifications, and Amazon CloudWatch continuously monitors cloud resources.

Architecture diagrams are available in the **architecture/** folder.

---

## Technology Stack

### Frontend
- React.js
- HTML
- CSS
- JavaScript

### Backend
- AWS Lambda
- Python

### Cloud Platform
- AWS IoT Core
- AWS IoT TwinMaker
- Amazon RDS
- Amazon S3
- Amazon SageMaker
- Amazon QuickSight
- Amazon SNS
- Amazon Cognito
- AWS IAM
- Amazon CloudWatch

### Database
- Amazon RDS (MySQL)

### Tools
- Git
- GitHub
- Eraser.io

---

## Dataset Details

### Historical Dataset

**Name:** ASHRAE Great Energy Predictor III

**Source:** Kaggle

**Purpose:** Historical building energy consumption analysis.

### Simulated Dataset

**Name:** Smart Campus IoT Sensor Dataset

**Source:** Simulated sensor readings generated for the project.

**Features**

- Timestamp
- Building ID
- Energy Consumption
- Water Consumption
- Temperature
- Humidity
- CO₂ Level
- Occupancy
- Sustainability Score

Dataset files are available in the **dataset/** folder.

---

## Repository Structure

```
├── architecture/
├── aws/
├── dataset/
├── docs/
├── images/
├── presentation/
├── README.md
```

---

## Project Documentation

- Literature Survey
- Research Gap Analysis
- Novelty Summary
- Work Distribution
- Architecture Diagrams

Available in the **docs/** folder.

---

## Project Status

🟢 Phase-I (Planning & Documentation Completed)

Current repository includes project planning, documentation, architecture design, dataset information, and folder organization. Code implementation will be added in future development phases.

