import os
import json
import hashlib

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

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

# Public UNICON-derived BSEI dataset
PUBLIC_BSEI_DATASET = os.path.join(
    BASE_DIR,
    "public_dataset",
    "public_bsei_dataset.csv"
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
# LOAD EXACT UNICON BSEI REFERENCES
# ============================================================

print(
    "\n=============================================="
)

print(
    "LOADING UNICON BSEI REFERENCES"
)

print(
    "=============================================="
)

if not os.path.exists(
    PUBLIC_BSEI_DATASET
):

    raise FileNotFoundError(
        "Public UNICON BSEI dataset not found:\n"
        +
        PUBLIC_BSEI_DATASET
    )


public_bsei_df = pd.read_csv(
    PUBLIC_BSEI_DATASET
)


# ------------------------------------------------------------
# Required columns
# ------------------------------------------------------------

required_bsei_columns = [
    "energy_reference_kWh",
    "water_reference_L",
    "air_temperature",
    "relative_humidity"
]


missing_columns = [
    column
    for column in required_bsei_columns
    if column not in public_bsei_df.columns
]


if missing_columns:

    raise ValueError(
        "Missing required columns in public BSEI dataset: "
        +
        ", ".join(missing_columns)
    )


# ============================================================
# EXACT REFERENCE VALUES USED BY PUBLIC BSEI
# ============================================================

ENERGY_REFERENCE = float(
    public_bsei_df[
        "energy_reference_kWh"
    ].median()
)


WATER_REFERENCE = float(
    public_bsei_df[
        "water_reference_L"
    ].median()
)


TEMPERATURE_REFERENCE = float(
    public_bsei_df[
        "air_temperature"
    ].median()
)


HUMIDITY_REFERENCE = float(
    public_bsei_df[
        "relative_humidity"
    ].median()
)


# ------------------------------------------------------------
# Environmental normalization
#
# EXACTLY the same approach used in the public BSEI backend:
# standard deviation of the public BSEI reference dataset.
# ------------------------------------------------------------

TEMPERATURE_STD = float(
    public_bsei_df[
        "air_temperature"
    ].std()
)


HUMIDITY_STD = float(
    public_bsei_df[
        "relative_humidity"
    ].std()
)


# Prevent division by zero
TEMPERATURE_STD = max(
    TEMPERATURE_STD,
    1e-6
)


HUMIDITY_STD = max(
    HUMIDITY_STD,
    1e-6
)


print(
    "BSEI energy reference:",
    round(
        ENERGY_REFERENCE,
        4
    )
)


print(
    "BSEI water reference:",
    round(
        WATER_REFERENCE,
        4
    )
)


print(
    "BSEI temperature reference:",
    round(
        TEMPERATURE_REFERENCE,
        4
    )
)


print(
    "BSEI humidity reference:",
    round(
        HUMIDITY_REFERENCE,
        4
    )
)


print(
    "BSEI temperature std:",
    round(
        TEMPERATURE_STD,
        4
    )
)


print(
    "BSEI humidity std:",
    round(
        HUMIDITY_STD,
        4
    )
)


print(
    "Public BSEI records:",
    len(public_bsei_df)
)


# ============================================================
# MONTHLY CONDITIONS
# ============================================================

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

    # August
    8: {
        "occupancy_factor": 0.98,
        "temperature_offset": 0.0,
        "humidity_offset": 6,
        "energy_factor": 1.00,
        "water_factor": 1.06
    },

    # September
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
# EXISTING SYNTHETIC SUSTAINABILITY SCORE
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
    # FINAL SYNTHETIC SUSTAINABILITY SCORE
    # --------------------------------------------------------

    score = (

        energy_score * 0.30

        +

        water_score * 0.20

        +

        co2_score * 0.20

        +

        temperature_score * 0.15

        +

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
# BSEI CALCULATION
#
# SAME METHODOLOGY AS PUBLIC UNICON BSEI
# ============================================================

def calculate_bsei(
    energy,
    water,
    temperature,
    humidity
):

    # --------------------------------------------------------
    # RELATIVE ENERGY
    # --------------------------------------------------------

    relative_energy = (
        energy
        /
        max(
            ENERGY_REFERENCE,
            1e-6
        )
    )

    # --------------------------------------------------------
    # RELATIVE WATER
    # --------------------------------------------------------

    relative_water = (
        water
        /
        max(
            WATER_REFERENCE,
            1e-6
        )
    )

    # --------------------------------------------------------
    # ENERGY EFFICIENCY
    # --------------------------------------------------------

    energy_efficiency = np.exp(
        -relative_energy
    )

    # --------------------------------------------------------
    # WATER EFFICIENCY
    # --------------------------------------------------------

    water_efficiency = np.exp(
        -relative_water
    )

    # --------------------------------------------------------
    # ENVIRONMENTAL DEVIATION
    # --------------------------------------------------------

    environmental_deviation = np.sqrt(

        (

            (
                temperature
                -
                TEMPERATURE_REFERENCE
            )
            /
            TEMPERATURE_STD

        ) ** 2

        +

        (

            (
                humidity
                -
                HUMIDITY_REFERENCE
            )
            /
            HUMIDITY_STD

        ) ** 2

    )

    # --------------------------------------------------------
    # ENVIRONMENTAL EFFICIENCY
    # --------------------------------------------------------

    environmental_efficiency = np.exp(
        -environmental_deviation
    )

    # --------------------------------------------------------
    # FINAL BSEI
    #
    # Energy       = 40%
    # Water        = 30%
    # Environment  = 30%
    # --------------------------------------------------------

    bsei = 100 * (

        energy_efficiency ** 0.40

        *

        water_efficiency ** 0.30

        *

        environmental_efficiency ** 0.30
    )

    return round(
        float(
            np.clip(
                bsei,
                0,
                100
            )
        ),
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
        # DATE
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
            *
            conditions[
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

        # Temperature effect
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
        # CO2
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
        # EXISTING SYNTHETIC SUSTAINABILITY SCORE
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

            "Timestamp":
                date.strftime(
                    "%d-%m-%Y"
                ),

            "Building_ID":
                building_name,

            "Building_Type":
                config[
                    "building_type"
                ],

            "Floor_Count":
                config[
                    "floor_count"
                ],

            "Occupancy":
                occupancy,

            "Occupancy_Per_Floor":
                round(
                    occupancy_per_floor,
                    2
                ),

            "Energy_Consumption_kWh":
                round(
                    energy,
                    2
                ),

            "Water_Consumption_L":
                round(
                    water,
                    2
                ),

            "Temperature_C":
                round(
                    temperature,
                    2
                ),

            "Humidity_Percent":
                round(
                    humidity,
                    2
                ),

            "CO2_Level_ppm":
                round(
                    co2,
                    2
                ),

            "Sustainability_Score":
                sustainability_score
        })

    return pd.DataFrame(
        data
    )


# ============================================================
# GENERATE ALL BUILDINGS
# ============================================================

all_data = []

print(
    "\n=============================================="
)

print(
    "GENERATING SYNTHETIC CAMPUS DATA"
)

print(
    "=============================================="
)

print(
    f"Period: {START_DATE} to {END_DATE}"
)

print(
    f"Buildings: {len(BUILDINGS)}"
)


for building_name, config in BUILDINGS.items():

    new_df = generate_building_data(
        building_name,
        config
    )

    all_data.append(
        new_df
    )


# ============================================================
# COMBINE ALL BUILDINGS
# ============================================================

combined_df = pd.concat(
    all_data,
    ignore_index=True
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

combined_df = combined_df.drop_duplicates(
    subset=[
        "Timestamp",
        "Building_ID"
    ],
    keep="first"
)


# ============================================================
# SORT DATA
# ============================================================

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
# CALCULATE BSEI
#
# SAME PUBLIC UNICON METHODOLOGY
# ============================================================

print(
    "\n=============================================="
)

print(
    "CALCULATING BSEI USING UNICON METHODOLOGY"
)

print(
    "=============================================="
)


combined_df["BSEI"] = combined_df.apply(

    lambda row: calculate_bsei(

        row[
            "Energy_Consumption_kWh"
        ],

        row[
            "Water_Consumption_L"
        ],

        row[
            "Temperature_C"
        ],

        row[
            "Humidity_Percent"
        ]

    ),

    axis=1
)


# ============================================================
# SAVE INDIVIDUAL BUILDING DATASETS
# ============================================================

print(
    "\n=============================================="
)

print(
    "SAVING BUILDING DATASETS"
)

print(
    "=============================================="
)


for building_name in BUILDINGS.keys():

    filename = (
        building_name.lower()
        +
        "_building_sensor_data.csv"
    )

    filepath = os.path.join(
        DATASET_DIR,
        filename
    )

    building_df = combined_df[
        combined_df[
            "Building_ID"
        ]
        ==
        building_name
    ].copy()

    building_df.to_csv(
        filepath,
        index=False
    )

    print(
        f"Saved: {filename}"
    )

    print(
        f"Records: {len(building_df)}"
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
# FINAL DATASET SUMMARY
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
# AVERAGE BUILDING METRICS
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
        "Sustainability_Score",
        "BSEI"
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
    ].dt.strftime(
        "%B"
    )
)

monthly_summary = (
    monthly_df.groupby(
        "Month"
    )[
        [
            "Energy_Consumption_kWh",
            "Water_Consumption_L",
            "CO2_Level_ppm",
            "Sustainability_Score",
            "BSEI"
        ]
    ]
    .mean()
)

print(
    monthly_summary.round(2)
)


# ============================================================
# BSEI SUMMARY
# ============================================================

print(
    "\n=============================================="
)

print(
    "BSEI SUMMARY"
)

print(
    "=============================================="
)

print(
    f"Mean BSEI: "
    f"{combined_df['BSEI'].mean():.2f}"
)

print(
    f"Minimum BSEI: "
    f"{combined_df['BSEI'].min():.2f}"
)

print(
    f"Maximum BSEI: "
    f"{combined_df['BSEI'].max():.2f}"
)

print(
    f"Median BSEI: "
    f"{combined_df['BSEI'].median():.2f}"
)


# ============================================================
# BSEI BY BUILDING
# ============================================================

print(
    "\n=============================================="
)

print(
    "BSEI BY BUILDING"
)

print(
    "=============================================="
)

bsei_building_summary = (
    combined_df.groupby(
        "Building_ID"
    )[
        "BSEI"
    ]
    .agg(
        [
            "mean",
            "min",
            "max"
        ]
    )
    .round(2)
)

print(
    bsei_building_summary
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
    combined_df.head(
        10
    ).to_string(
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
    combined_df.tail(
        10
    ).to_string(
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
# FILE LOCATIONS
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
    "Dataset folder:"
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
    "\n=============================================="
)

print(
    "BSEI METHODOLOGY"
)

print(
    "=============================================="
)

print(
    "Energy efficiency: 40%"
)

print(
    "Water efficiency: 30%"
)

print(
    "Environmental efficiency: 30%"
)

print(
    "BSEI = 100 × "
    "(Energy Efficiency^0.40) × "
    "(Water Efficiency^0.30) × "
    "(Environmental Efficiency^0.30)"
)


print(
    "\nDataset generation finished successfully."
)