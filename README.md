# Digital Twin Cloud Platform for Smart Campus Sustainability Analytics

A cloud-based Digital Twin platform for monitoring, analyzing, and improving sustainability across smart campus infrastructure using AWS cloud services.

---

# Project Title

**Digital Twin Cloud Platform for Smart Campus Sustainability Analytics**

---

# Team Members

| Name | Register Number |
|------|-----------------|
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

The proposed system collects real-time IoT sensor data from different campus buildings using AWS IoT Core. AWS Lambda processes incoming data before storing it in Amazon RDS and Amazon S3.

AWS IoT TwinMaker creates a virtual Digital Twin of campus infrastructure, while Amazon SageMaker performs predictive analytics. Amazon QuickSight visualizes sustainability metrics through interactive dashboards.

Amazon Cognito manages user authentication, AWS IAM provides secure access control, Amazon SNS delivers notifications, and Amazon CloudWatch monitors cloud resources and application performance.

---

# Architecture Diagrams

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

The project uses four simulated IoT sensor datasets representing different campus buildings.

| Dataset | Description |
|----------|-------------|
| Academic Building IoT Sensor Dataset | Simulated IoT sensor readings collected from classrooms, laboratories, libraries, and administrative offices. |
| Hostel Building IoT Sensor Dataset | Simulated IoT sensor readings representing residential energy consumption, occupancy patterns, and environmental conditions. |
| Main Building IoT Sensor Dataset | Simulated IoT sensor readings collected from the campus main building and administrative offices. |
| Placement Building IoT Sensor Dataset | Simulated IoT sensor readings representing placement drives, training sessions, workshops, and student activities. |

## Common Dataset Features

- Timestamp
- Building ID
- Energy Consumption (kWh)
- Water Consumption (L)
- Temperature (°C)
- Humidity (%)
- CO₂ Level (ppm)
- Occupancy
- Sustainability Score

## Dataset Specifications

- **File Format:** CSV
- **Number of Datasets:** 4
- **Records per Dataset:** 100
- **Total Records:** 400
- **Number of Features:** 9

Dataset files are available in the **dataset/** folder.

---

# Repository Structure

```text
DigitalTwinCloudPlatformforSmartCampusSustainabilityAnalytics_AWS_Cloud_Project_2026/
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
├── database/
│   └── README.md
│
├── dataset/
│   ├── academic_building_sensor_data.csv
│   ├── hostel_building_sensor_data.csv
│   ├── main_building_sensor_data.csv
│   ├── placement_building_sensor_data.csv
│   ├── dataset_description.md
│   └── README.md
│
├── docs/
│   ├── Work_Distribution.md
│   └── README.md
│
├── images/
│   └── README.md
│
├── literature_survey/
│   ├── Survey_Table.pdf
│   ├── Individual_Research_Gap_Analysis.pdf
│   ├── Novelty_Summary.pdf
│   └── README.md
│
├── presentation/
│   └── README.md
│
├── references/
│   ├── References.pdf
│   └── README.md
│
├── results/
│   └── README.md
│
├── src/
│   ├── backend/
│   │   └── README.md
│   ├── frontend/
│   │   └── README.md
│   ├── ml_model/
│   │   └── README.md
│   └── README.md
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
| **database** | Contains Amazon RDS database planning and documentation. |
| **dataset** | Contains simulated IoT sensor datasets and dataset documentation. |
| **docs** | Contains supporting project documentation such as work distribution and future technical documents. |
| **images** | Contains project images, screenshots, and visual assets. |
| **literature_survey** | Contains the survey table, individual research gap analysis, and novelty summary documents. |
| **presentation** | Contains project presentations and demonstration slides. |
| **references** | Contains the IEEE reference list and supporting reference materials. |
| **results** | Contains implementation outputs, dashboard screenshots, and project results. |
| **src** | Contains the project source code, including backend, frontend, and machine learning modules. |

---

# Project Documentation

The repository includes the following documentation:

- Survey Table
- Individual Research Gap Analysis
- Novelty Summary
- Work Distribution
- IEEE Reference List
- AWS Cloud Architecture
- Complete System Architecture
- Dataset Documentation

Documentation is organized across the **literature_survey**, **references**, **architecture**, **dataset**, and **docs** directories.

---

# Project Status

## 🟢 Phase-I (Planning & Documentation Completed)

The repository currently contains:

- Survey Table
- Individual Research Gap Analysis
- Novelty Summary
- IEEE Reference List
- AWS Cloud Architecture
- Complete System Architecture
- Four simulated IoT sensor datasets
- Dataset documentation
- Work Distribution
- Organized project repository structure

The project is prepared for the implementation phase, where AWS services, backend development, frontend development, Digital Twin integration, predictive analytics, machine learning models, and dashboard visualization will be developed.

---

# Future Scope

- Implement AWS IoT Core for real-time IoT data ingestion.
- Develop AWS Lambda functions for data processing.
- Integrate Amazon RDS and Amazon S3 for cloud storage.
- Build the Digital Twin using AWS IoT TwinMaker.
- Train predictive models using Amazon SageMaker.
- Create interactive dashboards using Amazon QuickSight.
- Deploy the complete application on AWS Cloud.

---
