import pandas as pd
import os

datasets = {
    "Academic": "../../dataset/academic_building_sensor_data.csv",
    "Hostel": "../../dataset/hostel_building_sensor_data.csv",
    "Main": "../../dataset/main_building_sensor_data.csv",
    "Placement": "../../dataset/placement_building_sensor_data.csv"
}

dataframes = []

for name, path in datasets.items():
    df = pd.read_csv(path)

    # Add building type so we know which dataset the record came from
    df["Building_Type"] = name

    dataframes.append(df)

# Combine all four datasets
combined_df = pd.concat(dataframes, ignore_index=True)

print("Total records:", len(combined_df))
print("Total columns:", len(combined_df.columns))

print("\nBuilding Type Distribution:")
print(combined_df["Building_Type"].value_counts())

print("\nCombined Dataset:")
print(combined_df.head())

# Save combined dataset
output_path = "../../dataset/combined_sensor_data.csv"
combined_df.to_csv(output_path, index=False)

print("\nCombined dataset saved successfully.")
print(output_path)