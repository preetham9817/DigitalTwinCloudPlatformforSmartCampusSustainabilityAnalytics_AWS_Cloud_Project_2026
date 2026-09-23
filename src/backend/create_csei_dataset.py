import os
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

UNICON_DIR = os.path.join(
    BASE_DIR,
    "public_dataset",
    "UNICON"
)

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "public_dataset",
    "public_csei_dataset.csv"
)


# ============================================================
# FILES
# ============================================================

BUILDING_SUBMETER = os.path.join(
    UNICON_DIR,
    "building_submeter_consumption.csv"
)

WATER_FILE = os.path.join(
    UNICON_DIR,
    "water_consumption.csv"
)

BUILDING_META = os.path.join(
    UNICON_DIR,
    "building_meta.csv"
)

WEATHER_FILE = os.path.join(
    UNICON_DIR,
    "weather_data.csv"
)

CALENDAR_FILE = os.path.join(
    UNICON_DIR,
    "calender.csv"
)


# ============================================================
# LOAD BUILDING METADATA
# ============================================================

print("Loading building metadata...")

meta = pd.read_csv(BUILDING_META)

meta = meta.rename(
    columns={
        "id": "building_id"
    }
)

meta["building_id"] = pd.to_numeric(
    meta["building_id"],
    errors="coerce"
)

meta["campus_id"] = pd.to_numeric(
    meta["campus_id"],
    errors="coerce"
)

meta["gross_floor_area"] = pd.to_numeric(
    meta["gross_floor_area"],
    errors="coerce"
)

meta["capacity"] = pd.to_numeric(
    meta["capacity"],
    errors="coerce"
)

meta = meta[
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

# Only buildings with valid floor area
meta = meta[
    meta["gross_floor_area"].notna()
    & (meta["gross_floor_area"] > 0)
]

print(
    "Valid buildings:",
    len(meta)
)


# ============================================================
# PROCESS BUILDING ELECTRICITY
# ============================================================

print("\nProcessing building electricity...")

electricity_chunks = []

chunk_size = 1_000_000
chunk_number = 0

for chunk in pd.read_csv(
    BUILDING_SUBMETER,
    chunksize=chunk_size
):

    chunk_number += 1

    print(
        f"Processing electricity chunk {chunk_number}..."
    )

    chunk["timestamp"] = pd.to_datetime(
        chunk["timestamp"],
        errors="coerce",
        utc=True
    )

    chunk["building_id"] = pd.to_numeric(
        chunk["building_id"],
        errors="coerce"
    )

    chunk["campus_id"] = pd.to_numeric(
        chunk["campus_id"],
        errors="coerce"
    )

    chunk["consumption"] = pd.to_numeric(
        chunk["consumption"],
        errors="coerce"
    )

    chunk = chunk.dropna(
        subset=[
            "building_id",
            "campus_id",
            "timestamp",
            "consumption"
        ]
    )

    chunk["date"] = (
        chunk["timestamp"]
        .dt.date
    )

    daily = (
        chunk
        .groupby(
            [
                "campus_id",
                "building_id",
                "date"
            ],
            as_index=False
        )["consumption"]
        .sum()
    )

    daily = daily.rename(
        columns={
            "consumption":
                "energy_consumption_kWh"
        }
    )

    electricity_chunks.append(daily)


print("\nCombining electricity chunks...")

electricity = pd.concat(
    electricity_chunks,
    ignore_index=True
)

# In case the same building/day occurs across chunks
electricity = (
    electricity
    .groupby(
        [
            "campus_id",
            "building_id",
            "date"
        ],
        as_index=False
    )["energy_consumption_kWh"]
    .sum()
)

print(
    "Daily electricity records:",
    len(electricity)
)


# ============================================================
# PROCESS WATER
# ============================================================

print("\nProcessing water consumption...")

water_chunks = []

for chunk in pd.read_csv(
    WATER_FILE,
    chunksize=1_000_000
):

    chunk["timestamp"] = pd.to_datetime(
        chunk["timestamp"],
        errors="coerce"
    )

    chunk["campus_id"] = pd.to_numeric(
        chunk["campus_id"],
        errors="coerce"
    )

    chunk["meter_id"] = pd.to_numeric(
        chunk["meter_id"],
        errors="coerce"
    )

    chunk["consumption"] = pd.to_numeric(
        chunk["consumption"],
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

    chunk["date"] = (
        chunk["timestamp"]
        .dt.date
    )

    # Water appears to be meter readings.
    # Daily usage = maximum reading - minimum reading.
    daily_meter = (
        chunk
        .groupby(
            [
                "campus_id",
                "meter_id",
                "date"
            ]
        )["consumption"]
        .agg(
            ["min", "max"]
        )
        .reset_index()
    )

    daily_meter["water_consumption_L"] = (
        daily_meter["max"]
        - daily_meter["min"]
    )

    daily = (
        daily_meter
        .groupby(
            [
                "campus_id",
                "date"
            ],
            as_index=False
        )["water_consumption_L"]
        .sum()
    )

    water_chunks.append(daily)


water = pd.concat(
    water_chunks,
    ignore_index=True
)

water = (
    water
    .groupby(
        [
            "campus_id",
            "date"
        ],
        as_index=False
    )["water_consumption_L"]
    .sum()
)

print(
    "Daily campus water records:",
    len(water)
)


# ============================================================
# PROCESS WEATHER
# ============================================================

print("\nProcessing weather...")

weather_chunks = []

for chunk in pd.read_csv(
    WEATHER_FILE,
    chunksize=1_000_000
):

    chunk["timestamp"] = pd.to_datetime(
        chunk["timestamp"],
        errors="coerce"
    )

    chunk["campus_id"] = pd.to_numeric(
        chunk["campus_id"],
        errors="coerce"
    )

    chunk["air_temperature"] = pd.to_numeric(
        chunk["air_temperature"],
        errors="coerce"
    )

    chunk["relative_humidity"] = pd.to_numeric(
        chunk["relative_humidity"],
        errors="coerce"
    )

    chunk = chunk.dropna(
        subset=[
            "campus_id",
            "timestamp",
            "air_temperature",
            "relative_humidity"
        ]
    )

    chunk["date"] = (
        chunk["timestamp"]
        .dt.date
    )

    daily = (
        chunk
        .groupby(
            [
                "campus_id",
                "date"
            ],
            as_index=False
        )
        .agg(
            {
                "air_temperature": "mean",
                "relative_humidity": "mean"
            }
        )
    )

    weather_chunks.append(daily)


weather = pd.concat(
    weather_chunks,
    ignore_index=True
)

weather = (
    weather
    .groupby(
        [
            "campus_id",
            "date"
        ],
        as_index=False
    )
    .agg(
        {
            "air_temperature": "mean",
            "relative_humidity": "mean"
        }
    )
)

print(
    "Daily weather records:",
    len(weather)
)


# ============================================================
# CALENDAR
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


# ============================================================
# COMBINE DATA
# ============================================================

print("\nCombining public UNICON data...")

df = electricity.merge(
    meta,
    on=[
        "campus_id",
        "building_id"
    ],
    how="inner"
)

df = df.merge(
    weather,
    on=[
        "campus_id",
        "date"
    ],
    how="left"
)

df = df.merge(
    water,
    on=[
        "campus_id",
        "date"
    ],
    how="left"
)

df = df.merge(
    calendar,
    on="date",
    how="left"
)


# ============================================================
# CLEAN
# ============================================================

df["date"] = pd.to_datetime(
    df["date"]
)

df = df.dropna(
    subset=[
        "energy_consumption_kWh",
        "gross_floor_area",
        "air_temperature",
        "relative_humidity"
    ]
)

df = df[
    (df["energy_consumption_kWh"] >= 0)
    & (df["gross_floor_area"] > 0)
]


# ============================================================
# ENERGY INTENSITY
# ============================================================

df["energy_intensity"] = (
    df["energy_consumption_kWh"]
    / df["gross_floor_area"]
)


# ============================================================
# BUILDING WATER CONTEXT
#
# Water is campus-level in UNICON.
# We therefore normalize campus water by total
# campus floor area rather than falsely assigning
# measured water to individual buildings.
# ============================================================

campus_area = (
    meta
    .groupby("campus_id")[
        "gross_floor_area"
    ]
    .sum()
    .reset_index()
)

campus_area = campus_area.rename(
    columns={
        "gross_floor_area":
            "campus_total_floor_area"
    }
)

df = df.merge(
    campus_area,
    on="campus_id",
    how="left"
)

df["water_intensity"] = (
    df["water_consumption_L"]
    / df["campus_total_floor_area"]
)


# ============================================================
# REFERENCE VALUES
#
# Calculated entirely from the public dataset.
# ============================================================

energy_reference = (
    df["energy_intensity"]
    .median()
)

water_reference = (
    df["water_intensity"]
    .median()
)

temperature_reference = (
    df["air_temperature"]
    .median()
)

humidity_reference = (
    df["relative_humidity"]
    .median()
)

temperature_std = (
    df["air_temperature"]
    .std()
)

humidity_std = (
    df["relative_humidity"]
    .std()
)


print("\nPublic-data reference values:")

print(
    "Energy reference:",
    energy_reference
)

print(
    "Water reference:",
    water_reference
)

print(
    "Temperature reference:",
    temperature_reference
)

print(
    "Humidity reference:",
    humidity_reference
)


# ============================================================
# ENERGY EFFICIENCY
# ============================================================

df["energy_efficiency"] = np.exp(
    -(
        df["energy_intensity"]
        / energy_reference
    )
)


# ============================================================
# WATER EFFICIENCY
# ============================================================

df["water_efficiency"] = np.exp(
    -(
        df["water_intensity"]
        / water_reference
    )
)


# ============================================================
# ENVIRONMENTAL DEVIATION
# ============================================================

temperature_component = (
    (
        df["air_temperature"]
        - temperature_reference
    )
    / temperature_std
)

humidity_component = (
    (
        df["relative_humidity"]
        - humidity_reference
    )
    / humidity_std
)

df["environmental_deviation"] = np.sqrt(
    temperature_component ** 2
    + humidity_component ** 2
)


# ============================================================
# ENVIRONMENTAL EFFICIENCY
# ============================================================

df["environmental_efficiency"] = np.exp(
    -df["environmental_deviation"]
)


# ============================================================
# DATA-DRIVEN WEIGHTS
#
# Higher variability gets a larger contribution.
# We use inverse coefficient-of-variation so that
# unstable/noisy indicators do not dominate the score.
# ============================================================

energy_cv = (
    df["energy_intensity"].std()
    / df["energy_intensity"].mean()
)

water_cv = (
    df["water_intensity"].std()
    / df["water_intensity"].mean()
)

environment_cv = (
    df["environmental_deviation"].std()
    / (
        df["environmental_deviation"].mean()
        + 1e-9
    )
)

inverse_cv = np.array(
    [
        1 / (energy_cv + 1e-9),
        1 / (water_cv + 1e-9),
        1 / (environment_cv + 1e-9)
    ]
)

weights = (
    inverse_cv
    / inverse_cv.sum()
)

w_energy = weights[0]
w_water = weights[1]
w_environment = weights[2]


print("\nCSEI weights:")

print(
    "Energy:",
    round(w_energy, 4)
)

print(
    "Water:",
    round(w_water, 4)
)

print(
    "Environment:",
    round(w_environment, 4)
)


# ============================================================
# CAMPUS SUSTAINABILITY EFFICIENCY INDEX
# ============================================================

df["CSEI"] = (
    100
    * (
        df["energy_efficiency"]
        ** w_energy
    )
    * (
        df["water_efficiency"]
        ** w_water
    )
    * (
        df["environmental_efficiency"]
        ** w_environment
    )
)


# ============================================================
# LIMIT TO 0-100
# ============================================================

df["CSEI"] = df["CSEI"].clip(
    lower=0,
    upper=100
)


# ============================================================
# FINAL COLUMNS
# ============================================================

final_columns = [
    "campus_id",
    "building_id",
    "date",
    "category",
    "gross_floor_area",
    "room_area",
    "capacity",

    "energy_consumption_kWh",
    "water_consumption_L",

    "energy_intensity",
    "water_intensity",

    "air_temperature",
    "relative_humidity",

    "environmental_deviation",

    "energy_efficiency",
    "water_efficiency",
    "environmental_efficiency",

    "is_holiday",
    "is_semester",
    "is_exam",

    "CSEI"
]

df = df[
    [
        column
        for column in final_columns
        if column in df.columns
    ]
]


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

print("\n==============================================")
print("CSEI DATASET CREATED")
print("==============================================")

print(
    "Output:",
    OUTPUT_PATH
)

print(
    "Records:",
    len(df)
)

print(
    "Buildings:",
    df["building_id"].nunique()
)

print(
    "Campuses:",
    df["campus_id"].nunique()
)

print("\nCSEI statistics:")

print(
    df["CSEI"].describe()
)

print("\nFirst 10 records:")

print(
    df.head(10).to_string(
        index=False
    )
)

print("\n==============================================")
print("DONE")
print("==============================================")