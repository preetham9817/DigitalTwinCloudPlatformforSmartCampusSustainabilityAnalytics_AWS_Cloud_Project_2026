import pandas as pd

datasets = {
    "Academic": "../../dataset/academic_building_sensor_data.csv",
    "Hostel": "../../dataset/hostel_building_sensor_data.csv",
    "Main": "../../dataset/main_building_sensor_data.csv",
    "Placement": "../../dataset/placement_building_sensor_data.csv"
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