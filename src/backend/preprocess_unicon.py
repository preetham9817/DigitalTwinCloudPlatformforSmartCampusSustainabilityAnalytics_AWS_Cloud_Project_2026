import os
import pandas as pd
import numpy as np


# ============================================================
# PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

UNICON_PATH = os.path.join(
    PROJECT_ROOT,
    "public_dataset",
    "UNICON"
)

OUTPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "public_dataset",
    "public_training_dataset.csv"
)


# ============================================================
# FILE PATHS
# ============================================================

BUILDING_CONSUMPTION_FILE = os.path.join(
    UNICON_PATH,
    "building_consumption.csv"
)

BUILDING_META_FILE = os.path.join(
    UNICON_PATH,
    "building_meta.csv"
)

WEATHER_FILE = os.path.join(
    UNICON_PATH,
    "weather_data.csv"
)

CALENDAR_FILE = os.path.join(
    UNICON_PATH,
    "calender.csv"
)


# ============================================================
# STEP 1: LOAD BUILDING METADATA
# ============================================================

print("\nLoading building metadata...")

building_meta = pd.read_csv(
    BUILDING_META_FILE
)

building_meta = building_meta.rename(
    columns={
        "id": "building_id"
    }
)

building_meta = building_meta[
    [
        "campus_id",
        "building_id",
        "built_year",
        "category",
        "gross_floor_area",
        "room_area",
        "capacity"
    ]
]

print(
    "Building metadata records:",
    len(building_meta)
)


# ============================================================
# STEP 2: LOAD WEATHER DATA
# ============================================================

print("\nLoading weather data...")

weather = pd.read_csv(
    WEATHER_FILE
)

weather["timestamp"] = pd.to_datetime(
    weather["timestamp"],
    errors="coerce"
)

weather["date"] = weather["timestamp"].dt.date

weather_daily = (
    weather
    .groupby(
        ["campus_id", "date"],
        as_index=False
    )
    .agg(
        {
            "air_temperature": "mean",
            "relative_humidity": "mean",
            "apparent_temperature": "mean",
            "dew_point_temperature": "mean",
            "wind_speed": "mean",
            "wind_direction": "mean"
        }
    )
)

print(
    "Daily weather records:",
    len(weather_daily)
)


# ============================================================
# STEP 3: LOAD UNIVERSITY CALENDAR
# ============================================================

print("\nLoading calendar...")

calendar = pd.read_csv(
    CALENDAR_FILE
)

calendar["date"] = pd.to_datetime(
    calendar["date"],
    errors="coerce"
).dt.date

calendar = calendar[
    [
        "date",
        "is_holiday",
        "is_semester",
        "is_exam"
    ]
]

print(
    "Calendar records:",
    len(calendar)
)


# ============================================================
# STEP 4: PROCESS BUILDING ELECTRICITY
# ============================================================

print("\nProcessing building electricity...")
print("This may take some time because the file is large.")


daily_chunks = []

chunk_number = 0

for chunk in pd.read_csv(
    BUILDING_CONSUMPTION_FILE,
    chunksize=500_000
):

    chunk_number += 1

    print(
        f"Processing chunk {chunk_number}..."
    )

    chunk["timestamp"] = pd.to_datetime(
        chunk["timestamp"],
        errors="coerce"
    )

    chunk = chunk.dropna(
        subset=[
            "campus_id",
            "meter_id",
            "timestamp",
            "consumption"
        ]
    )

    chunk["date"] = chunk["timestamp"].dt.date

    # --------------------------------------------------------
    # Aggregate 15-minute electricity readings to daily
    # building-level consumption.
    # --------------------------------------------------------

    daily = (
        chunk
        .groupby(
            [
                "campus_id",
                "meter_id",
                "date"
            ],
            as_index=False
        )["consumption"]
        .sum()
    )

    daily_chunks.append(
        daily
    )


# Combine chunk-level aggregations

print("\nCombining electricity chunks...")

building_daily = pd.concat(
    daily_chunks,
    ignore_index=True
)

# Re-aggregate because the same building/date may
# appear in multiple chunks.

building_daily = (
    building_daily
    .groupby(
        [
            "campus_id",
            "meter_id",
            "date"
        ],
        as_index=False
    )["consumption"]
    .sum()
)

building_daily = building_daily.rename(
    columns={
        "meter_id": "building_id",
        "consumption": "energy_consumption"
    }
)

print(
    "Daily building records:",
    len(building_daily)
)


# ============================================================
# STEP 5: JOIN BUILDING METADATA
# ============================================================

print("\nJoining building metadata...")

building_daily = building_daily.merge(
    building_meta,
    on=[
        "campus_id",
        "building_id"
    ],
    how="left"
)


# ============================================================
# STEP 6: JOIN WEATHER
# ============================================================

print("Joining weather data...")

building_daily = building_daily.merge(
    weather_daily,
    on=[
        "campus_id",
        "date"
    ],
    how="left"
)


# ============================================================
# STEP 7: JOIN CALENDAR
# ============================================================

print("Joining university calendar...")

building_daily = building_daily.merge(
    calendar,
    on="date",
    how="left"
)


# ============================================================
# STEP 8: DATE FEATURES
# ============================================================

print("Creating date features...")

building_daily["date"] = pd.to_datetime(
    building_daily["date"]
)

building_daily["year"] = (
    building_daily["date"].dt.year
)

building_daily["month"] = (
    building_daily["date"].dt.month
)

building_daily["day"] = (
    building_daily["date"].dt.day
)

building_daily["day_of_week"] = (
    building_daily["date"].dt.dayofweek
)

building_daily["is_weekend"] = (
    building_daily["day_of_week"] >= 5
).astype(int)


# ============================================================
# STEP 9: ENERGY INTENSITY
# ============================================================

print("Calculating energy intensity...")

building_daily["energy_intensity"] = np.where(
    building_daily["gross_floor_area"] > 0,
    building_daily["energy_consumption"]
    / building_daily["gross_floor_area"],
    np.nan
)


# ============================================================
# STEP 10: CLEAN NUMERIC VALUES
# ============================================================

numeric_columns = [
    "energy_consumption",
    "built_year",
    "gross_floor_area",
    "room_area",
    "capacity",
    "air_temperature",
    "relative_humidity",
    "apparent_temperature",
    "dew_point_temperature",
    "wind_speed",
    "wind_direction",
    "is_holiday",
    "is_semester",
    "is_exam",
    "energy_intensity"
]

for column in numeric_columns:

    if column in building_daily.columns:

        building_daily[column] = pd.to_numeric(
            building_daily[column],
            errors="coerce"
        )


# ============================================================
# STEP 11: REMOVE INVALID TARGET VALUES
# ============================================================

building_daily = building_daily[
    building_daily["energy_consumption"] > 0
]


# ============================================================
# STEP 12: HANDLE MISSING VALUES
# ============================================================

print("Handling missing values...")

numeric_features = [
    "built_year",
    "gross_floor_area",
    "room_area",
    "capacity",
    "air_temperature",
    "relative_humidity",
    "apparent_temperature",
    "dew_point_temperature",
    "wind_speed",
    "wind_direction",
    "is_holiday",
    "is_semester",
    "is_exam"
]

for column in numeric_features:

    if column in building_daily.columns:

        building_daily[column] = (
            building_daily[column]
            .fillna(
                building_daily[column].median()
            )
        )


# Missing category

building_daily["category"] = (
    building_daily["category"]
    .fillna("unknown")
)


# ============================================================
# STEP 13: SAVE DATASET
# ============================================================

print("\nSaving public training dataset...")

building_daily.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# STEP 14: SUMMARY
# ============================================================

print("\n==============================================")
print("UNICON PREPROCESSING COMPLETE")
print("==============================================")

print(
    "Output:",
    OUTPUT_PATH
)

print(
    "Records:",
    len(building_daily)
)

print(
    "Columns:",
    len(building_daily.columns)
)

print("\nColumns:")

for column in building_daily.columns:
    print(
        " -",
        column
    )


print("\nSample records:")

print(
    building_daily.head().to_string(
        index=False
    )
)

print("\nTarget statistics:")

print(
    building_daily[
        "energy_consumption"
    ].describe()
)

print("\nBuilding count:")

print(
    building_daily[
        "building_id"
    ].nunique()
)

print("\nCampus count:")

print(
    building_daily[
        "campus_id"
    ].nunique()
)

print("\n==============================================")