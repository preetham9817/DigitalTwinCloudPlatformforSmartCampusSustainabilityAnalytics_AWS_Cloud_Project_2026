import os
import json
import hashlib

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

# Generate August + September 2026
#
# August:
# 01-08-2026 to 30-08-2026
#
# September:
# 01-09-2026 to 30-09-2026

START_DATE = "2026-08-01"
END_DATE = "2026-09-30"


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset"
)

CONFIG_FILE = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "building_config.json"
)

os.makedirs(
    DATASET_DIR,
    exist_ok=True
)


# ============================================================
# LOAD BUILDING CONFIGURATION
# ============================================================

with open(
    CONFIG_FILE,
    "r"
) as file:

    BUILDINGS = json.load(file)


# ============================================================
# MONTHLY CONDITIONS
# ============================================================

# These values are synthetic project assumptions.
# They are used to create realistic variation between months.

MONTHLY_CONDITIONS = {

    1: {
        "occupancy_factor": 0.98,
        "temperature_offset": -1.0,
        "humidity_offset": -3,
        "energy_factor": 0.96,
        "water_factor": 0.95
    },

    2: {
        "occupancy_factor": 1.00,
        "temperature_offset": 0.0,
        "humidity_offset": -1,
        "energy_factor": 0.98,
        "water_factor": 0.98
    },

    3: {
        "occupancy_factor": 1.00,
        "temperature_offset": 1.0,
        "humidity_offset": 0,
        "energy_factor": 1.02,
        "water_factor": 1.02
    },

    4: {
        "occupancy_factor": 0.96,
        "temperature_offset": 2.0,
        "humidity_offset": 2,
        "energy_factor": 1.08,
        "water_factor": 1.04
    },

    5: {
        "occupancy_factor": 0.90,
        "temperature_offset": 3.0,
        "humidity_offset": 4,
        "energy_factor": 1.12,
        "water_factor": 1.08
    },

    6: {
        "occupancy_factor": 0.92,
        "temperature_offset": 1.0,
        "humidity_offset": 6,
        "energy_factor": 1.04,
        "water_factor": 1.06
    },

    7: {
        "occupancy_factor": 0.95,
        "temperature_offset": 0.0,
        "humidity_offset": 7,
        "energy_factor": 1.00,
        "water_factor": 1.08
    },

    # AUGUST
    8: {
        "occupancy_factor": 0.98,
        "temperature_offset": 0.0,
        "humidity_offset": 6,
        "energy_factor": 1.00,
        "water_factor": 1.06
    },

    # SEPTEMBER
    9: {
        "occupancy_factor": 1.00,
        "temperature_offset": -0.5,
        "humidity_offset": 4,
        "energy_factor": 0.99,
        "water_factor": 1.03
    },

    10: {
        "occupancy_factor": 0.97,
        "temperature_offset": -0.5,
        "humidity_offset": 2,
        "energy_factor": 0.98,
        "water_factor": 1.00
    },

    11: {
        "occupancy_factor": 0.94,
        "temperature_offset": -1.0,
        "humidity_offset": 0,
        "energy_factor": 0.96,
        "water_factor": 0.97
    },

    12: {
        "occupancy_factor": 0.88,
        "temperature_offset": -1.5,
        "humidity_offset": -2,
        "energy_factor": 0.94,
        "water_factor": 0.94
    }
}


# ============================================================
# WEEKEND OCCUPANCY FACTORS
# ============================================================

WEEKEND_OCCUPANCY_FACTOR = {

    "Academic": 0.55,

    "Hostel": 0.95,

    "Main": 0.60,

    "Placement": 0.45
}


# ============================================================
# DETERMINISTIC RANDOM GENERATOR
# ============================================================

def get_random_generator(
    building_name,
    date
):

    seed_text = (
        f"{building_name}_"
        f"{date.strftime('%Y-%m-%d')}"
    )

    seed = int(
        hashlib.sha256(
            seed_text.encode()
        ).hexdigest()[:8],
        16
    )

    return np.random.default_rng(
        seed
    )


# ============================================================
# SUSTAINABILITY SCORE
# ============================================================

def calculate_sustainability_score(
    energy,
    water,
    co2,
    temperature,
    humidity,
    occupancy
):

    occupancy = max(
        occupancy,
        1
    )

    # --------------------------------------------------------
    # ENERGY SCORE
    # --------------------------------------------------------

    energy_per_person = (
        energy /
        occupancy
    )

    energy_score = 100 - (
        (energy_per_person - 1.0)
        * 25
    )

    energy_score = np.clip(
        energy_score,
        40,
        100
    )

    # --------------------------------------------------------
    # WATER SCORE
    # --------------------------------------------------------

    water_per_person = (
        water /
        occupancy
    )

    water_score = 100 - (
        (water_per_person - 5.0)
        * 2.2
    )

    water_score = np.clip(
        water_score,
        40,
        100
    )

    # --------------------------------------------------------
    # CO2 SCORE
    # --------------------------------------------------------

    co2_score = 100 - (
        max(
            co2 - 450,
            0
        ) / 12
    )

    co2_score = np.clip(
        co2_score,
        40,
        100
    )

    # --------------------------------------------------------
    # TEMPERATURE SCORE
    # --------------------------------------------------------

    temperature_score = 100 - (
        abs(
            temperature - 24
        ) * 8
    )

    temperature_score = np.clip(
        temperature_score,
        40,
        100
    )

    # --------------------------------------------------------
    # HUMIDITY SCORE
    # --------------------------------------------------------

    humidity_score = 100 - (
        abs(
            humidity - 50
        ) * 1.5
    )

    humidity_score = np.clip(
        humidity_score,
        40,
        100
    )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    score = (

        energy_score * 0.30 +

        water_score * 0.20 +

        co2_score * 0.20 +

        temperature_score * 0.15 +

        humidity_score * 0.15
    )

    # Small natural variation

    score += np.random.normal(
        0,
        1.0
    )

    score = np.clip(
        score,
        45,
        98
    )

    return round(
        float(score),
        2
    )


# ============================================================
# GENERATE DATA FOR ONE BUILDING
# ============================================================

def generate_building_data(
    building_name,
    config
):

    data = []

    dates = pd.date_range(
        start=START_DATE,
        end=END_DATE,
        freq="D"
    )

    print(
        f"\nGenerating {building_name} dataset..."
    )

    for date in dates:

        # ----------------------------------------------------
        # DATE INFORMATION
        # ----------------------------------------------------

        month = date.month

        day_of_week = date.weekday()

        is_weekend = (
            day_of_week >= 5
        )

        conditions = (
            MONTHLY_CONDITIONS[
                month
            ]
        )

        rng = get_random_generator(
            building_name,
            date
        )

        # ----------------------------------------------------
        # OCCUPANCY
        # ----------------------------------------------------

        base_occupancy = rng.uniform(
            config["occupancy_min"],
            config["occupancy_max"]
        )

        occupancy = (
            base_occupancy
            * conditions[
                "occupancy_factor"
            ]
        )

        # Weekend effect

        if is_weekend:

            weekend_factor = (
                WEEKEND_OCCUPANCY_FACTOR.get(
                    building_name,
                    0.60
                )
            )

            occupancy *= (
                weekend_factor
            )

        # Daily variation

        occupancy += rng.normal(
            0,
            max(
                occupancy * 0.04,
                10
            )
        )

        # ----------------------------------------------------
        # OCCUPANCY LIMITS
        # ----------------------------------------------------

        if building_name == "Hostel":

            minimum_occupancy = (
                config["occupancy_min"]
                * 0.85
            )

        else:

            minimum_occupancy = (
                config["occupancy_min"]
                * 0.35
            )

        maximum_occupancy = (
            config["occupancy_max"]
            * 1.05
        )

        occupancy = int(
            np.clip(
                occupancy,
                minimum_occupancy,
                maximum_occupancy
            )
        )

        # ----------------------------------------------------
        # OCCUPANCY PER FLOOR
        # ----------------------------------------------------

        occupancy_per_floor = (
            occupancy /
            config["floor_count"]
        )

        # ----------------------------------------------------
        # TEMPERATURE
        # ----------------------------------------------------

        temperature = (

            config[
                "temperature_mean"
            ]

            +

            conditions[
                "temperature_offset"
            ]
        )

        temperature += rng.normal(
            0,
            0.7
        )

        temperature = np.clip(
            temperature,
            20,
            34
        )

        # ----------------------------------------------------
        # HUMIDITY
        # ----------------------------------------------------

        humidity = (

            config[
                "humidity_mean"
            ]

            +

            conditions[
                "humidity_offset"
            ]
        )

        humidity += rng.normal(
            0,
            2.5
        )

        humidity = np.clip(
            humidity,
            35,
            85
        )

        # ----------------------------------------------------
        # ENERGY CONSUMPTION
        # ----------------------------------------------------

        energy = (

            occupancy

            *

            config[
                "energy_per_person"
            ]

            *

            conditions[
                "energy_factor"
            ]
        )

        # Higher temperature means
        # slightly higher cooling demand.

        temperature_effect = max(
            temperature - 25,
            0
        )

        energy *= (
            1
            +
            temperature_effect
            * 0.025
        )

        # Daily variation

        energy += rng.normal(
            0,
            energy * 0.05
        )

        energy = max(
            energy,
            0
        )

        # ----------------------------------------------------
        # WATER CONSUMPTION
        # ----------------------------------------------------

        water = (

            occupancy

            *

            config[
                "water_per_person"
            ]

            *

            conditions[
                "water_factor"
            ]
        )

        water += rng.normal(
            0,
            water * 0.07
        )

        water = max(
            water,
            0
        )

        # ----------------------------------------------------
        # CO2 LEVEL
        # ----------------------------------------------------

        co2 = (

            config[
                "co2_base"
            ]

            +

            occupancy

            *

            config[
                "co2_per_person"
            ]
        )

        # Slightly lower CO2 on weekends

        if is_weekend:

            co2 -= 15

        co2 += rng.normal(
            0,
            25
        )

        co2 = np.clip(
            co2,
            400,
            1200
        )

        # ----------------------------------------------------
        # SUSTAINABILITY SCORE
        # ----------------------------------------------------

        sustainability_score = (
            calculate_sustainability_score(
                energy,
                water,
                co2,
                temperature,
                humidity,
                occupancy
            )
        )

        # ----------------------------------------------------
        # STORE RECORD
        # ----------------------------------------------------

        data.append({

            # Date format:
            # 01-08-2026
            # 02-08-2026
            # ...
            # 30-09-2026

            "Timestamp": date.strftime(
                "%d-%m-%Y"
            ),

            "Building_ID": building_name,

            "Building_Type": config[
                "building_type"
            ],

            "Floor_Count": config[
                "floor_count"
            ],

            "Occupancy": occupancy,

            "Occupancy_Per_Floor": round(
                occupancy_per_floor,
                2
            ),

            "Energy_Consumption_kWh": round(
                energy,
                2
            ),

            "Water_Consumption_L": round(
                water,
                2
            ),

            "Temperature_C": round(
                temperature,
                2
            ),

            "Humidity_Percent": round(
                humidity,
                2
            ),

            "CO2_Level_ppm": round(
                co2,
                2
            ),

            "Sustainability_Score": (
                sustainability_score
            )
        })

    return pd.DataFrame(
        data
    )


# ============================================================
# GENERATE / APPEND ALL BUILDINGS
# ============================================================

all_data = []

for building_name, config in BUILDINGS.items():

    # Generate new data for requested period

    new_df = generate_building_data(
        building_name,
        config
    )

    filename = (
        building_name.lower()
        + "_building_sensor_data.csv"
    )

    filepath = os.path.join(
        DATASET_DIR,
        filename
    )

    # --------------------------------------------------------
    # CHECK FOR EXISTING DATA
    # --------------------------------------------------------

    if os.path.exists(filepath):

        try:

            existing_df = pd.read_csv(
                filepath
            )

            print(
                f"Existing data found for "
                f"{building_name}: "
                f"{len(existing_df)} records"
            )

            # ------------------------------------------------
            # Combine existing + new
            # ------------------------------------------------

            df = pd.concat(
                [
                    existing_df,
                    new_df
                ],
                ignore_index=True
            )

            # ------------------------------------------------
            # Remove duplicate date/building records
            # ------------------------------------------------

            df = df.drop_duplicates(
                subset=[
                    "Timestamp",
                    "Building_ID"
                ],
                keep="first"
            )

            # ------------------------------------------------
            # Sort by date
            # ------------------------------------------------

            df["_sort_date"] = (
                pd.to_datetime(
                    df["Timestamp"],
                    format="%d-%m-%Y",
                    errors="coerce"
                )
            )

            df = df.sort_values(
                "_sort_date"
            )

            df = df.drop(
                columns=[
                    "_sort_date"
                ]
            )

            df = df.reset_index(
                drop=True
            )

        except Exception as error:

            print(
                f"Could not read existing "
                f"{filename}: {error}"
            )

            df = new_df

    else:

        df = new_df

    # --------------------------------------------------------
    # Save building dataset
    # --------------------------------------------------------

    df.to_csv(
        filepath,
        index=False
    )

    print(
        f"Saved: {filename}"
    )

    print(
        f"Total records for {building_name}: "
        f"{len(df)}"
    )

    all_data.append(
        df
    )


# ============================================================
# CREATE COMBINED DATASET
# ============================================================

combined_df = pd.concat(
    all_data,
    ignore_index=True
)

# ------------------------------------------------------------
# Remove any duplicate records
# ------------------------------------------------------------

combined_df = combined_df.drop_duplicates(
    subset=[
        "Timestamp",
        "Building_ID"
    ],
    keep="first"
)

# ------------------------------------------------------------
# Sort by date and building
# ------------------------------------------------------------

combined_df["_sort_date"] = (
    pd.to_datetime(
        combined_df["Timestamp"],
        format="%d-%m-%Y",
        errors="coerce"
    )
)

combined_df = combined_df.sort_values(
    [
        "_sort_date",
        "Building_ID"
    ]
)

combined_df = combined_df.drop(
    columns=[
        "_sort_date"
    ]
)

combined_df = combined_df.reset_index(
    drop=True
)


# ============================================================
# SAVE COMBINED DATASET
# ============================================================

combined_file = os.path.join(
    DATASET_DIR,
    "combined_sensor_data.csv"
)

combined_df.to_csv(
    combined_file,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

date_range = pd.date_range(
    START_DATE,
    END_DATE
)

print(
    "\n=============================================="
)

print(
    "DATASET GENERATION COMPLETED"
)

print(
    "=============================================="
)

print(
    f"Requested period: "
    f"{START_DATE} to {END_DATE}"
)

print(
    f"Days in requested period: "
    f"{len(date_range)}"
)

print(
    f"Buildings: "
    f"{len(BUILDINGS)}"
)

print(
    f"Total combined records: "
    f"{len(combined_df)}"
)


# ============================================================
# RECORDS PER BUILDING
# ============================================================

print(
    "\n=============================================="
)

print(
    "RECORDS PER BUILDING"
)

print(
    "=============================================="
)

print(
    combined_df[
        "Building_ID"
    ].value_counts()
)


# ============================================================
# BUILDING AVERAGES
# ============================================================

print(
    "\n=============================================="
)

print(
    "AVERAGE BUILDING METRICS"
)

print(
    "=============================================="
)

summary = combined_df.groupby(
    "Building_ID"
)[
    [
        "Floor_Count",
        "Occupancy",
        "Occupancy_Per_Floor",
        "Energy_Consumption_kWh",
        "Water_Consumption_L",
        "Temperature_C",
        "Humidity_Percent",
        "CO2_Level_ppm",
        "Sustainability_Score"
    ]
].mean()

print(
    summary.round(2)
)


# ============================================================
# MONTHLY SUMMARY
# ============================================================

print(
    "\n=============================================="
)

print(
    "MONTHLY SUMMARY"
)

print(
    "=============================================="
)

monthly_df = combined_df.copy()

monthly_df["Date"] = pd.to_datetime(
    monthly_df["Timestamp"],
    format="%d-%m-%Y"
)

monthly_df["Month"] = (
    monthly_df[
        "Date"
    ].dt.strftime("%B")
)

monthly_summary = (
    monthly_df.groupby(
        "Month"
    )[
        [
            "Energy_Consumption_kWh",
            "Water_Consumption_L",
            "CO2_Level_ppm",
            "Sustainability_Score"
        ]
    ]
    .mean()
)

print(
    monthly_summary.round(2)
)


# ============================================================
# FIRST 10 RECORDS
# ============================================================

print(
    "\n=============================================="
)

print(
    "FIRST 10 RECORDS"
)

print(
    "=============================================="
)

print(
    combined_df.head(10).to_string(
        index=False
    )
)


# ============================================================
# LAST 10 RECORDS
# ============================================================

print(
    "\n=============================================="
)

print(
    "LAST 10 RECORDS"
)

print(
    "=============================================="
)

print(
    combined_df.tail(10).to_string(
        index=False
    )
)


# ============================================================
# DATASET COLUMNS
# ============================================================

print(
    "\n=============================================="
)

print(
    "DATASET COLUMNS"
)

print(
    "=============================================="
)

for column in combined_df.columns:

    print(
        f"- {column}"
    )


# ============================================================
# FILE LOCATION
# ============================================================

print(
    "\n=============================================="
)

print(
    "FILES"
)

print(
    "=============================================="
)

print(
    f"Dataset folder:"
)

print(
    DATASET_DIR
)

print(
    "\nCombined dataset:"
)

print(
    combined_file
)

print(
    "\nDataset generation finished successfully."
)