from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

datasets = {
    "Academic": PROJECT_ROOT / "dataset" / "academic_building_sensor_data.csv",
    "Hostel": PROJECT_ROOT / "dataset" / "hostel_building_sensor_data.csv",
    "Main": PROJECT_ROOT / "dataset" / "main_building_sensor_data.csv",
    "Placement": PROJECT_ROOT / "dataset" / "placement_building_sensor_data.csv"
}

for name, path in datasets.items():
    df = pd.read_csv(path)

    print("\n" + "=" * 50)
    print(name + " Building Dataset")
    print("=" * 50)

    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Column Names:")
    print(list(df.columns))
    print("\nFirst 5 records:")
    print(df.head())