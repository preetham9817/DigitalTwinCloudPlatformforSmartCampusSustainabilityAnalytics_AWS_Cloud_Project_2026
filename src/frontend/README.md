# Frontend

Contains the browser dashboard built with HTML, CSS, and JavaScript.

## Responsibilities
- Display campus sustainability KPIs and historical trends.
- Compare Academic, Hostel, Main, and Placement buildings.
- Present energy, water, occupancy, and environmental metrics.
- Display BSEI and component-efficiency-based alerts/recommendations.

The dashboard obtains data through the local Flask backend, which reads CSV files. It is not documented as directly connected to live AWS IoT/S3 data. Building consumption and occupancy are per-record means; campus KPI and historical-trend energy, water, and occupancy use daily totals. Temperature, humidity, CO₂, and BSEI are means. Priorities use BSEI and component efficiencies relative to campus-building means, not internal normalization constants as external thresholds.
