import os
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

UNICON_DIR = os.path.join(
    BASE_DIR,
    "public_dataset",
    "UNICON"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "public_dataset"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "public_bsei_dataset.csv"
)


# ============================================================
# BSEI WEIGHTS
# ============================================================

ENERGY_WEIGHT = 0.45
WATER_WEIGHT = 0.35
ENVIRONMENT_WEIGHT = 0.20


# ============================================================
# UNICON REFERENCE VALUES
# ============================================================

ENERGY_REFERENCE = 772.8378
WATER_REFERENCE = 335464.242

TEMPERATURE_REFERENCE = 17.5706
HUMIDITY_REFERENCE = 71.0625

TEMPERATURE_STD = 4.9704
HUMIDITY_STD = 12.2897


# ============================================================
# REQUIRED OUTPUT FEATURES
# ============================================================

OUTPUT_COLUMNS = [
    "timestamp",
    "campus",
    "building_id",

    "energy_consumption_kWh",
    "avg_power_kW",
    "electricity_coverage",

    "water_consumption_L",
    "water_coverage",

    "air_temperature",
    "relative_humidity",

    "relative_energy",
    "relative_water",

    "energy_efficiency",
    "water_efficiency",

    "environmental_deviation",
    "environmental_efficiency",

    "day_of_week",
    "month",
    "is_weekend",

    "energy_reference_kWh",
    "water_reference_L",

    "BSEI"
]


# ============================================================
# COLUMN FINDER
# ============================================================

def find_column(df, candidates):

    for column in candidates:

        if column in df.columns:
            return column

    return None


# ============================================================
# NUMERIC CLEANING
# ============================================================

def clean_numeric(series):

    return pd.to_numeric(
        series,
        errors="coerce"
    )


# ============================================================
# LOAD PREPARED UNICON PUBLIC DATASET
# ============================================================

def load_public_unicon_dataset():

    print()
    print("=" * 70)
    print("LOADING UNICON PUBLIC DATASET")
    print("=" * 70)

    source_file = os.path.join(
        UNICON_DIR,
        "public_bsei_dataset.csv"
    )

    if not os.path.exists(source_file):

        raise FileNotFoundError(
            f"\nPrepared UNICON dataset not found:\n{source_file}"
        )

    print()
    print("Source:")
    print(source_file)

    df = pd.read_csv(source_file)

    print()
    print("Records loaded:", len(df))

    print()
    print("Columns:")
    for column in df.columns:
        print(" -", column)

    if len(df) == 0:

        raise ValueError(
            "The UNICON public dataset is empty."
        )

    return df


# ============================================================
# PREPARE DATASET
# ============================================================

def prepare_dataset(df):

    print()
    print("=" * 70)
    print("PREPARING PUBLIC BSEI DATASET")
    print("=" * 70)


    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------

    timestamp_column = find_column(
        df,
        [
            "timestamp",
            "Timestamp",
            "datetime",
            "Datetime",
            "date",
            "Date",
            "time",
            "Time"
        ]
    )


    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    energy_column = find_column(
        df,
        [
            "energy_consumption_kWh",
            "Energy_Consumption_kWh",
            "energy_consumption",
            "electricity_consumption",
            "electricity",
            "energy"
        ]
    )


    # --------------------------------------------------------
    # WATER
    # --------------------------------------------------------

    water_column = find_column(
        df,
        [
            "water_consumption_L",
            "Water_Consumption_L",
            "water_consumption",
            "water",
            "Water"
        ]
    )


    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    temperature_column = find_column(
        df,
        [
            "air_temperature",
            "Air_Temperature",
            "temperature",
            "Temperature",
            "Temperature_C"
        ]
    )


    # --------------------------------------------------------
    # HUMIDITY
    # --------------------------------------------------------

    humidity_column = find_column(
        df,
        [
            "relative_humidity",
            "Relative_Humidity",
            "humidity",
            "Humidity",
            "Humidity_Percent"
        ]
    )


    print()
    print("Detected columns:")
    print("Timestamp:", timestamp_column)
    print("Energy:", energy_column)
    print("Water:", water_column)
    print("Temperature:", temperature_column)
    print("Humidity:", humidity_column)


    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    missing = []

    if timestamp_column is None:
        missing.append("timestamp")

    if energy_column is None:
        missing.append("energy")

    if water_column is None:
        missing.append("water")

    if temperature_column is None:
        missing.append("temperature")

    if humidity_column is None:
        missing.append("humidity")


    if missing:

        raise ValueError(
            "\nRequired columns missing from UNICON dataset: "
            + ", ".join(missing)
        )


    # --------------------------------------------------------
    # CREATE STANDARD DATAFRAME
    # --------------------------------------------------------

    result = pd.DataFrame()


    result["timestamp"] = pd.to_datetime(
        df[timestamp_column],
        errors="coerce"
    )


    result["energy_consumption_kWh"] = clean_numeric(
        df[energy_column]
    )


    result["water_consumption_L"] = clean_numeric(
        df[water_column]
    )


    result["air_temperature"] = clean_numeric(
        df[temperature_column]
    )


    result["relative_humidity"] = clean_numeric(
        df[humidity_column]
    )


    # --------------------------------------------------------
    # CAMPUS
    # --------------------------------------------------------

    campus_column = find_column(
        df,
        [
            "campus",
            "Campus",
            "campus_name",
            "Campus_Name"
        ]
    )

    if campus_column is not None:

        result["campus"] = (
            df[campus_column]
            .astype(str)
        )

    else:

        result["campus"] = "UNICON Campus"


    # --------------------------------------------------------
    # BUILDING
    # --------------------------------------------------------

    building_column = find_column(
        df,
        [
            "building_id",
            "Building_ID",
            "building",
            "Building"
        ]
    )

    if building_column is not None:

        result["building_id"] = (
            df[building_column]
            .astype(str)
        )

    else:

        result["building_id"] = "Unknown"


    # --------------------------------------------------------
    # REMOVE INVALID VALUES
    # --------------------------------------------------------

    before = len(result)

    result = result.dropna(
        subset=[
            "timestamp",
            "energy_consumption_kWh",
            "water_consumption_L",
            "air_temperature",
            "relative_humidity"
        ]
    )


    result = result[
        result["energy_consumption_kWh"] >= 0
    ]


    result = result[
        result["water_consumption_L"] >= 0
    ]


    print()
    print("Valid records:", len(result))
    print("Removed records:", before - len(result))


    if len(result) == 0:

        raise ValueError(
            "All public UNICON records were removed during cleaning."
        )


    # --------------------------------------------------------
    # AVG POWER
    # --------------------------------------------------------

    result["avg_power_kW"] = (
        result["energy_consumption_kWh"] / 24.0
    )


    # --------------------------------------------------------
    # COVERAGE
    # --------------------------------------------------------

    result["electricity_coverage"] = 1.0
    result["water_coverage"] = 1.0


    # --------------------------------------------------------
    # TIME FEATURES
    # --------------------------------------------------------

    result["day_of_week"] = (
        result["timestamp"].dt.dayofweek
    )

    result["month"] = (
        result["timestamp"].dt.month
    )

    result["is_weekend"] = (
        result["day_of_week"] >= 5
    ).astype(int)


    # --------------------------------------------------------
    # REFERENCE VALUES
    # --------------------------------------------------------

    result["energy_reference_kWh"] = ENERGY_REFERENCE

    result["water_reference_L"] = WATER_REFERENCE


    # --------------------------------------------------------
    # RELATIVE CONSUMPTION
    # --------------------------------------------------------

    result["relative_energy"] = (
        result["energy_consumption_kWh"]
        / ENERGY_REFERENCE
    )


    result["relative_water"] = (
        result["water_consumption_L"]
        / WATER_REFERENCE
    )


    # ========================================================
    # ENERGY EFFICIENCY
    # ========================================================

    result["energy_efficiency"] = (
        100.0
        /
        (
            1.0
            +
            result["relative_energy"]
        )
    )


    # ========================================================
    # WATER EFFICIENCY
    # ========================================================

    result["water_efficiency"] = (
        100.0
        /
        (
            1.0
            +
            result["relative_water"]
        )
    )


    # ========================================================
    # ENVIRONMENTAL DEVIATION
    # ========================================================

    temperature_deviation = (
        (
            result["air_temperature"]
            -
            TEMPERATURE_REFERENCE
        )
        /
        TEMPERATURE_STD
    )


    humidity_deviation = (
        (
            result["relative_humidity"]
            -
            HUMIDITY_REFERENCE
        )
        /
        HUMIDITY_STD
    )


    result["environmental_deviation"] = np.sqrt(
        temperature_deviation ** 2
        +
        humidity_deviation ** 2
    )


    # ========================================================
    # ENVIRONMENTAL EFFICIENCY
    # ========================================================

    result["environmental_efficiency"] = (
        100.0
        /
        (
            1.0
            +
            result["environmental_deviation"]
        )
    )


    # ========================================================
    # FINAL BSEI
    # ========================================================

    result["BSEI"] = (

        result["energy_efficiency"]
        *
        ENERGY_WEIGHT

        +

        result["water_efficiency"]
        *
        WATER_WEIGHT

        +

        result["environmental_efficiency"]
        *
        ENVIRONMENT_WEIGHT
    )


    result["BSEI"] = result["BSEI"].clip(
        0,
        100
    )


    result["BSEI"] = result["BSEI"].round(2)


    # --------------------------------------------------------
    # FINAL COLUMNS
    # --------------------------------------------------------

    result = result[
        OUTPUT_COLUMNS
    ]


    result = result.sort_values(
        "timestamp"
    )


    result = result.reset_index(
        drop=True
    )


    return result


# ============================================================
# SAVE
# ============================================================

def save_dataset(df):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print()
    print("=" * 70)
    print("PUBLIC BSEI DATASET CREATED")
    print("=" * 70)

    print()
    print("Output:")
    print(OUTPUT_FILE)

    print()
    print("Records:", len(df))

    print()
    print("BSEI Statistics:")

    print(
        df["BSEI"].describe()
    )

    print()
    print(
        "Average BSEI:",
        round(df["BSEI"].mean(), 2)
    )

    print(
        "Minimum BSEI:",
        round(df["BSEI"].min(), 2)
    )

    print(
        "Maximum BSEI:",
        round(df["BSEI"].max(), 2)
    )

    print()
    print("BSEI Weights:")
    print("Energy:       45%")
    print("Water:        35%")
    print("Environment:  20%")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("PUBLIC UNICON BSEI DATASET GENERATOR")
    print("=" * 70)

    raw_data = load_public_unicon_dataset()

    prepared_data = prepare_dataset(
        raw_data
    )

    save_dataset(
        prepared_data
    )

    print()
    print("DONE.")