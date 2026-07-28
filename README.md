# Digital Twin Cloud Platform for Smart Campus Sustainability Analytics

A cloud-based Digital Twin platform for monitoring, analyzing, and improving sustainability across smart campus infrastructure using AWS cloud services.

---

# Project Title

**Digital Twin Cloud Platform for Smart Campus Sustainability Analytics**

---

# Team Members

| Name | Registration Number |
|------|---------------------|
| Preetham H | 24BIT0294 |

---

# Problem Statement

University campuses generate large volumes of operational data related to energy consumption, water usage, environmental conditions, and occupancy. Existing campus management systems often monitor these resources independently, making it difficult to obtain a unified view of sustainability performance.

This project proposes a cloud-based Digital Twin platform that integrates multiple campus resources into a single virtual environment, enabling centralized monitoring, predictive analytics, sustainability assessment, and informed decision-making.

---

# Objectives

- Develop a cloud-based Digital Twin platform for smart campus sustainability.
- Integrate energy, water, occupancy, and environmental sensor data.
- Generate a dynamic Campus Sustainability Score.
- Forecast resource consumption using predictive analytics.
- Detect abnormal resource usage and generate alerts.
- Provide interactive dashboards for sustainability monitoring and decision support.

---

# Proposed Architecture / Framework

The proposed system collects real-time IoT sensor data from campus buildings using **AWS IoT Core**. **AWS Lambda** processes incoming data before storing it in **Amazon RDS** and **Amazon S3**.

**AWS IoT TwinMaker** creates a virtual Digital Twin of campus infrastructure, while **Amazon SageMaker** performs predictive analytics. **Amazon QuickSight** visualizes sustainability metrics through dashboards.

**Amazon Cognito** manages user authentication, **AWS IAM** provides secure access control, **Amazon SNS** delivers notifications, and **Amazon CloudWatch** monitors cloud resources.

## Architecture Diagrams

The architecture diagrams are available in the **architecture/** folder.

- AWS Cloud Architecture
- Complete System Architecture

---

# Technology Stack

## Frontend

- React.js
- HTML
- CSS
- JavaScript

## Backend

- Python
- AWS Lambda

## Cloud Platform

- AWS IoT Core
- AWS IoT TwinMaker
- Amazon RDS
- Amazon S3
- Amazon SageMaker
- Amazon QuickSight
- Amazon Cognito
- Amazon SNS
- AWS IAM
- Amazon CloudWatch

## Database

- Amazon RDS (MySQL)

## Tools

- Git
- GitHub
- Eraser.io

---

# Dataset Details

## Historical Dataset

- **Name:** ASHRAE Great Energy Predictor III
- **Source:** Kaggle
- **Type:** Historical Building Energy Dataset
- **Purpose:** Historical building energy consumption analysis.

## Simulated Dataset

- **Name:** Smart Campus IoT Sensor Dataset
- **Source:** Simulated IoT sensor readings generated for the project.
- **Type:** CSV
- **Records:** 100
- **Features:** 9

### Dataset Features

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

# Repository Structure

```text
DigitalTwinCloudPlatformforSmartCampusSustainabilityAnalytics_AWS_Cloud_Project_2026
│
├── architecture/
│   ├── AWS_Cloud_Architecture.png
│   ├── Complete_System_Architecture.png
│   └── README.md
│
├── aws/
│   ├── cloudformation/
│   ├── lambda/
│   ├── deployment_guide.md
│   └── README.md
│
├── dataset/
│   ├── campus_sensor_data.csv
│   ├── dataset_description.md
│   └── README.md
│
├── docs/
│   ├── Survey Table.pdf
│   ├── Individual Research gap Analysis.pdf
│   ├── Novelty Summary.pdf
│   ├── Work_Distribution.md
│   └── README.md
│
├── images/
│   └── README.md
│
├── presentation/
│
├── .gitignore
└── README.md
```

---

# Folder Overview

| Folder | Description |
|---------|-------------|
| **architecture** | Contains the AWS Cloud Architecture and Complete System Architecture diagrams. |
| **aws** | Contains AWS deployment planning, CloudFormation templates, Lambda functions, and cloud documentation. |
| **dataset** | Contains the project datasets and dataset documentation. |
| **docs** | Contains the literature survey, research gap analysis, novelty summary, and work distribution documents. |
| **images** | Contains project images and screenshots. |
| **presentation** | Contains presentation files prepared for project reviews. |

---

# Project Documentation

The repository includes the following documentation:

- Literature Survey
- Individual Research Gap Analysis
- Novelty Summary
- Work Distribution
- AWS Cloud Architecture
- Complete System Architecture

Documentation is available in the **docs/** folder.

---

# Project Status

🟢 **Phase-I (Planning & Documentation Completed)**

The repository currently contains the project planning, literature survey, research gap analysis, novelty summary, proposed architectures, dataset information, work distribution, and organized project structure.

The project is prepared for the implementation phase, where AWS services, backend development, frontend development, Digital Twin integration, predictive analytics, and dashboard visualization will be developed.

---

# Future Scope

- Implement AWS IoT Core for real-time data ingestion.
- Develop AWS Lambda functions for data processing.
- Integrate Amazon RDS and Amazon S3 for storage.
- Build the Digital Twin using AWS IoT TwinMaker.
- Train predictive models using Amazon SageMaker.
- Create interactive dashboards using Amazon QuickSight.
- Deploy the complete application on AWS Cloud.
