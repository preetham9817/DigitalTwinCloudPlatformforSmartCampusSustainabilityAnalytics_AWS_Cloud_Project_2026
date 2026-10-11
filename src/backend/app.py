import os
import json
import joblib
import warnings
from datetime import datetime, timezone
from json import JSONDecodeError

import boto3
import numpy as np
import pandas as pd

from flask import Flask, jsonify, request
from flask_cors import CORS
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

warnings.filterwarnings("ignore")


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DATASET_DIR = os.path.join(ROOT, "dataset")

MODEL_DIR = os.path.join(ROOT, "src", "ml_model")

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "public_bsei_model.pkl"
)

CONFIG_PATH = os.path.join(
    MODEL_DIR,
    "model_config.json"
)

PUBLIC_DATASET_PATH = os.path.join(
    ROOT,
    "public_dataset",
    "public_bsei_dataset.csv"
)

AWS_DATA_BUCKET = "digital-twin-campus-2026-preetham"
AWS_DATA_REGION = "us-east-1"
AWS_DATA_PREFIX = "processed-data/"
AWS_DATA_MAX_RECORDS = 50
AWS_HISTORY_MAX_RECORDS = 1000
AWS_HISTORY_DEFAULT_RECORDS = 500
AWS_EXPIRED_CREDENTIAL_CODES = {
    "ExpiredToken",
    "ExpiredTokenException",
    "SecurityTokenExpired",
    "TokenRefreshRequired"
}
AWS_INVALID_CREDENTIAL_CODES = {
    "InvalidClientTokenId",
    "InvalidToken",
    "UnrecognizedClientException"
}
AWS_ACCESS_DENIED_CODES = {
    "AccessDenied",
    "AccessDeniedException",
    "AllAccessDisabled"
}


# ============================================================
# BSEI WEIGHTS
# ============================================================

ENERGY_WEIGHT = 0.45
WATER_WEIGHT = 0.35
ENVIRONMENT_WEIGHT = 0.20


# ============================================================
# BSEI NORMALIZATION CONSTANTS
# ============================================================

# Retained by the existing BSEI calculation; these constants are not used as
# standalone dashboard alert or recommendation thresholds.
ENERGY_REFERENCE = 772.8378
WATER_REFERENCE = 335464.242

TEMPERATURE_REFERENCE = 17.5706
HUMIDITY_REFERENCE = 71.0625

TEMPERATURE_STD = 4.9704
HUMIDITY_STD = 12.2897


# ============================================================
# BUILDING ORDER
# ============================================================

BUILDING_ORDER = [
    "Academic",
    "Main",
    "Hostel",
    "Placement"
]


# ============================================================
# GLOBAL MODEL / PUBLIC DATA
# ============================================================

PUBLIC_MODEL = None
MODEL_CONFIG = {}
PUBLIC_BSEI_DATA = pd.DataFrame()


def rounded_metric(value, decimals=2):

    if pd.isna(value) or not np.isfinite(value):
        return None

    return round(float(value), decimals)


def numeric_series(data, column):

    if column not in data.columns:
        return pd.Series(dtype="float64")

    values = pd.to_numeric(data[column], errors="coerce")
    return values[np.isfinite(values)]


def parse_timestamps(values):

    text_values = values.astype("string").str.strip()
    iso_dates = text_values.str.match(
        r"^\d{4}-\d{1,2}-\d{1,2}(?:$|[T\s])",
        na=False
    )
    iso_parsed = pd.to_datetime(
        values.where(iso_dates),
        errors="coerce"
    )
    day_first_parsed = pd.to_datetime(
        values.where(~iso_dates),
        errors="coerce",
        dayfirst=True
    )

    return iso_parsed.fillna(day_first_parsed)


# ============================================================
# LOAD RANDOM FOREST MODEL
# ============================================================

def load_public_model():

    global PUBLIC_MODEL
    global MODEL_CONFIG

    try:

        if not os.path.exists(MODEL_PATH):

            print("WARNING: Public BSEI model not found:")
            print(MODEL_PATH)

            return

        with open(MODEL_PATH, "rb") as file:

            artifact = joblib.load(MODEL_PATH)

        # The new training script saves the estimator directly.
        if hasattr(artifact, "predict"):

            PUBLIC_MODEL = artifact

        # Backward compatibility for dictionary artifacts.
        elif isinstance(artifact, dict):

            possible_keys = [
                "model",
                "estimator",
                "rf_model",
                "regressor"
            ]

            for key in possible_keys:

                if key in artifact:

                    candidate = artifact[key]

                    if hasattr(candidate, "predict"):

                        PUBLIC_MODEL = candidate
                        break

        if os.path.exists(CONFIG_PATH):

            try:

                with open(CONFIG_PATH, "r") as file:

                    MODEL_CONFIG = json.load(file)

            except Exception as config_error:

                print(
                    "Could not load model configuration:",
                    config_error
                )

        if PUBLIC_MODEL is not None:

            print()
            print("=" * 70)
            print("PUBLIC UNICON BSEI MODEL LOADED")
            print("=" * 70)
            print("Model:", MODEL_PATH)
            print(
                "Weights: Energy 45% | Water 35% | Environment 20%"
            )

        else:

            print(
                "WARNING: public_bsei_model.pkl "
                "does not contain a usable estimator."
            )

    except Exception as error:

        print(
            "ERROR loading public BSEI model:",
            error
        )


# ============================================================
# LOAD PUBLIC BSEI DATASET
# ============================================================

def load_public_bsei_dataset():

    global PUBLIC_BSEI_DATA

    try:

        if not os.path.exists(PUBLIC_DATASET_PATH):

            print(
                "WARNING: Public BSEI dataset not found:",
                PUBLIC_DATASET_PATH
            )

            PUBLIC_BSEI_DATA = pd.DataFrame()

            return

        data = pd.read_csv(PUBLIC_DATASET_PATH)

        data.columns = [
            str(column).strip()
            for column in data.columns
        ]

        PUBLIC_BSEI_DATA = data.copy()

        print(
            "Public BSEI records:",
            len(PUBLIC_BSEI_DATA)
        )

    except Exception as error:

        print(
            "ERROR loading public BSEI dataset:",
            error
        )

        PUBLIC_BSEI_DATA = pd.DataFrame()


# ============================================================
# LOAD CAMPUS SENSOR DATA
# ============================================================

def load_sensor_data():

    frames = []

    if not os.path.exists(DATASET_DIR):

        print(
            "Dataset directory not found:",
            DATASET_DIR
        )

        return pd.DataFrame()

    csv_files = [
        file_name
        for file_name in os.listdir(DATASET_DIR)
        if file_name.lower().endswith(".csv")
    ]

    for file_name in csv_files:

        # Never use the public UNICON dataset as campus sensor data.
        if file_name.lower() in [
            "combined_sensor_data.csv",
            "public_bsei_dataset.csv"
        ]:

            continue

        file_path = os.path.join(
            DATASET_DIR,
            file_name
        )

        try:

            data = pd.read_csv(file_path)

            if (
                "Timestamp" not in data.columns
                or "Building_ID" not in data.columns
            ):

                continue

            frames.append(data)

        except Exception as error:

            print(
                "Could not load:",
                file_name,
                error
            )

    if not frames:

        return pd.DataFrame()

    combined = pd.concat(
        frames,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Clean column names
    # --------------------------------------------------------

    combined.columns = [
        str(column).strip()
        for column in combined.columns
    ]

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    combined["Timestamp"] = parse_timestamps(
        combined["Timestamp"]
    )

    combined = combined.dropna(
        subset=["Timestamp"]
    )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "Occupancy",
        "Occupancy_Per_Floor",
        "Energy_Consumption_kWh",
        "Water_Consumption_L",
        "Temperature_C",
        "Humidity_Percent",
        "CO2_Level_ppm"
    ]

    for column in numeric_columns:

        if column in combined.columns:

            combined[column] = pd.to_numeric(
                combined[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Building ID
    # --------------------------------------------------------

    combined["Building_ID"] = (
        combined["Building_ID"]
        .where(combined["Building_ID"].notna(), "")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Calculate BSEI dynamically
    # --------------------------------------------------------

    combined["BSEI"] = combined.apply(
        calculate_bsei_from_row,
        axis=1
    )

    return combined


# ============================================================
# BSEI CALCULATION
# ============================================================

def calculate_bsei(
    energy,
    water,
    temperature,
    humidity
):

    try:

        energy = float(energy)
        water = float(water)
        temperature = float(temperature)
        humidity = float(humidity)

        # ----------------------------------------------------
        # Relative consumption
        # ----------------------------------------------------

        relative_energy = (
            energy / ENERGY_REFERENCE
        )

        relative_water = (
            water / WATER_REFERENCE
        )

        # ----------------------------------------------------
        # Efficiency scores
        #
        # Arithmetic formulation avoids the severe compression
        # caused by the earlier multiplicative formula.
        # ----------------------------------------------------

        energy_efficiency = (
            100.0 / (1.0 + relative_energy)
        )

        water_efficiency = (
            100.0 / (1.0 + relative_water)
        )

        # ----------------------------------------------------
        # Environmental deviation
        # ----------------------------------------------------

        temperature_deviation = (
            (temperature - TEMPERATURE_REFERENCE)
            / TEMPERATURE_STD
        )

        humidity_deviation = (
            (humidity - HUMIDITY_REFERENCE)
            / HUMIDITY_STD
        )

        environmental_deviation = np.sqrt(
            temperature_deviation ** 2
            +
            humidity_deviation ** 2
        )

        environmental_efficiency = (
            100.0
            /
            (1.0 + environmental_deviation)
        )

        # ----------------------------------------------------
        # Weighted BSEI
        # ----------------------------------------------------

        bsei = (
            energy_efficiency * ENERGY_WEIGHT
            +
            water_efficiency * WATER_WEIGHT
            +
            environmental_efficiency
            * ENVIRONMENT_WEIGHT
        )

        return float(
            np.clip(bsei, 0, 100)
        )

    except Exception:

        return 0.0


# ============================================================
# CALCULATE BSEI FOR DATAFRAME ROW
# ============================================================

def calculate_bsei_from_row(row):

    metric_values = pd.to_numeric(
        pd.Series([
            row.get("Energy_Consumption_kWh"),
            row.get("Water_Consumption_L"),
            row.get("Temperature_C"),
            row.get("Humidity_Percent")
        ]),
        errors="coerce"
    )

    if metric_values.isna().any() or not np.isfinite(metric_values).all():
        return np.nan

    return calculate_bsei(*metric_values.tolist())


def calculate_component_efficiencies(data):
    required_columns = [
        "Energy_Consumption_kWh",
        "Water_Consumption_L",
        "Temperature_C",
        "Humidity_Percent"
    ]
    if any(column not in data.columns for column in required_columns):
        return None

    metrics = data[required_columns].apply(
        pd.to_numeric,
        errors="coerce"
    ).replace([np.inf, -np.inf], np.nan).dropna()

    if metrics.empty:
        return None

    energy_efficiency = 100.0 / (
        1.0 + metrics["Energy_Consumption_kWh"] / ENERGY_REFERENCE
    )
    water_efficiency = 100.0 / (
        1.0 + metrics["Water_Consumption_L"] / WATER_REFERENCE
    )
    temperature_deviation = (
        (metrics["Temperature_C"] - TEMPERATURE_REFERENCE)
        / TEMPERATURE_STD
    )
    humidity_deviation = (
        (metrics["Humidity_Percent"] - HUMIDITY_REFERENCE)
        / HUMIDITY_STD
    )
    environmental_efficiency = 100.0 / (
        1.0 + np.sqrt(
            temperature_deviation ** 2
            + humidity_deviation ** 2
        )
    )

    return {
        "energy": float(energy_efficiency.mean()),
        "water": float(water_efficiency.mean()),
        "environment": float(environmental_efficiency.mean())
    }


def calculate_weighted_bsei_gaps(data):

    efficiencies = calculate_component_efficiencies(data)
    if efficiencies is None:
        return None

    return {
        "energy": float(
            (100.0 - efficiencies["energy"]) * ENERGY_WEIGHT
        ),
        "water": float(
            (100.0 - efficiencies["water"]) * WATER_WEIGHT
        ),
        "environment": float(
            (100.0 - efficiencies["environment"])
            * ENVIRONMENT_WEIGHT
        )
    }


def select_weighted_bsei_gap(weighted_gaps):

    if not weighted_gaps:
        return None

    valid_gaps = {}
    for component, gap in weighted_gaps.items():
        if component not in {"energy", "water", "environment"}:
            continue
        numeric_gap = pd.to_numeric(
            pd.Series([gap]),
            errors="coerce"
        ).iloc[0]
        if pd.notna(numeric_gap) and np.isfinite(numeric_gap):
            valid_gaps[component] = float(numeric_gap)

    if not valid_gaps:
        return None

    component = max(valid_gaps, key=valid_gaps.get)
    gap = valid_gaps[component]

    if gap <= 0:
        return None

    return component, gap


# ============================================================
# BUILDING RECOMMENDATION
# ============================================================

def generate_building_recommendation(
    building,
    weighted_gaps=None,
    component_efficiencies=None
):

    def numeric_value(key):
        value = pd.to_numeric(
            pd.Series([building.get(key)]),
            errors="coerce"
        ).iloc[0]

        if pd.isna(value) or not np.isfinite(value):
            return None

        return float(value)

    name = str(
        building.get("Building_ID") or "This building"
    ).strip()
    bsei = numeric_value("BSEI")
    co2 = numeric_value("CO2_Level_ppm")

    if bsei is None:
        return (
            f"Collect complete sensor readings for {name} before "
            "prioritizing sustainability actions."
        )

    energy = numeric_value("Energy_Consumption_kWh")
    water = numeric_value("Water_Consumption_L")
    temperature = numeric_value("Temperature_C")
    humidity = numeric_value("Humidity_Percent")

    if any(
        value is None
        for value in (energy, water, temperature, humidity)
    ):
        return (
            f"Collect complete energy, water, temperature and humidity "
            f"readings for {name} before prioritizing a resource-specific action."
        )

    weighted_gaps = (
        weighted_gaps
        if weighted_gaps is not None
        else calculate_weighted_bsei_gaps(pd.DataFrame([{
            "Energy_Consumption_kWh": energy,
            "Water_Consumption_L": water,
            "Temperature_C": temperature,
            "Humidity_Percent": humidity
        }]))
    )
    selected_gap = select_weighted_bsei_gap(weighted_gaps)

    if selected_gap is None:
        return (
            f"Collect complete energy, water, temperature and humidity "
            f"readings for {name} before prioritizing a resource-specific action."
        )

    principal_issue, selected_weighted_gap = selected_gap
    if component_efficiencies is None:
        component_efficiencies = calculate_component_efficiencies(
            pd.DataFrame([{
                "Energy_Consumption_kWh": energy,
                "Water_Consumption_L": water,
                "Temperature_C": temperature,
                "Humidity_Percent": humidity
            }])
        )

    if not component_efficiencies:
        return (
            f"Collect complete energy, water, temperature and humidity "
            f"readings for {name} before prioritizing a resource-specific action."
        )

    if principal_issue == "water":
        efficiency_key = "water"
        efficiency_label = "Water"
        measurement_detail = (
            f"Mean water consumption in {name} is {water:.2f} L "
            "per sensor record."
        )
        action = (
            "Review water-use patterns and investigate conservation "
            "opportunities."
        )
    elif principal_issue == "environment":
        efficiency_key = "environment"
        efficiency_label = "environmental"
        measurement_detail = (
            f"Mean conditions in {name} are {temperature:.2f} °C and "
            f"{humidity:.2f}% humidity; "
            + (
                f"mean CO2 is {co2:.2f} ppm."
                if co2 is not None
                else "CO2 measurement is unavailable."
            )
        )
        action = (
            "Review temperature, humidity, and CO2 conditions."
        )
    else:
        efficiency_key = "energy"
        efficiency_label = "Energy"
        measurement_detail = (
            f"Mean energy consumption in {name} is {energy:.2f} kWh "
            "per sensor record."
        )
        action = (
            "Review high-load consumption and operating schedules."
        )

    efficiency = component_efficiencies[efficiency_key]
    primary = (
        f"BSEI is {bsei:.2f}. The primary {efficiency_label} component "
        f"has {efficiency:.2f}% efficiency and a "
        f"{selected_weighted_gap:.2f}-point weighted BSEI gap. "
    )

    secondary_key = max(
        (
            key for key in weighted_gaps
            if key != principal_issue
        ),
        key=weighted_gaps.get,
        default=None
    )
    secondary = ""
    if (
        secondary_key is not None
        and weighted_gaps[secondary_key] > 0
        and component_efficiencies.get(secondary_key) is not None
        and component_efficiencies[secondary_key] < 100
    ):
        secondary_names = {
            "energy": "energy",
            "water": "water",
            "environment": "environmental"
        }
        secondary = (
            f"Also monitor {secondary_names[secondary_key]} efficiency "
            f"({component_efficiencies[secondary_key]:.2f}%; "
            f"{weighted_gaps[secondary_key]:.2f}-point weighted gap). "
        )

    return f"{measurement_detail} {primary}{action} {secondary}".strip()


# ============================================================
# BUILDING SUMMARY
# ============================================================

def get_building_summary(data):

    buildings = []

    if data.empty or "Building_ID" not in data.columns:

        return buildings

    identifiers = data["Building_ID"]
    normalized_ids = identifiers.astype(str).str.strip().str.casefold()
    valid_ids = (
        identifiers.notna()
        & normalized_ids.ne("")
        & ~normalized_ids.isin({"nan", "none", "<na>"})
    )
    valid_data = data.loc[valid_ids].copy()

    if valid_data.empty:
        return buildings

    valid_data["_Building_Key"] = (
        valid_data["Building_ID"].astype(str).str.strip().str.casefold()
    )

    display_names = {}
    for building_id in valid_data["Building_ID"]:
        display_name = str(building_id).strip()
        if not display_name:
            continue
        key = display_name.casefold()
        if key not in display_names:
            display_names[key] = display_name

    preferred_names = {
        building_name.casefold(): building_name
        for building_name in BUILDING_ORDER
    }
    ordered_keys = [
        name.casefold()
        for name in BUILDING_ORDER
        if name.casefold() in display_names
    ]
    additional_keys = sorted(
        (
            key for key in display_names
            if key not in preferred_names
        ),
        key=lambda key: (key, display_names[key])
    )

    metric_columns = [
        "Energy_Consumption_kWh",
        "Water_Consumption_L",
        "Occupancy",
        "Temperature_C",
        "Humidity_Percent",
        "CO2_Level_ppm",
        "BSEI"
    ]

    for column in metric_columns:
        if column not in valid_data.columns:
            valid_data[column] = np.nan
        else:
            valid_data[column] = pd.to_numeric(
                valid_data[column],
                errors="coerce"
            ).replace([np.inf, -np.inf], np.nan)

    for building_key in ordered_keys + additional_keys:
        building_data = valid_data[
            valid_data["_Building_Key"] == building_key
        ]

        summary = {
            "Building_ID": preferred_names.get(
                building_key,
                display_names[building_key]
            ),
            **{
                column: (
                    float(building_data[column].mean())
                    if building_data[column].notna().any()
                    else None
                )
                for column in metric_columns
            },
            "Records": int(len(building_data))
        }

        weighted_gaps = calculate_weighted_bsei_gaps(building_data)
        component_efficiencies = calculate_component_efficiencies(
            building_data
        )
        selected_gap = select_weighted_bsei_gap(weighted_gaps)
        summary["Recommendation_Efficiencies"] = (
            {
                component: round(efficiency, 2)
                for component, efficiency in component_efficiencies.items()
            }
            if component_efficiencies
            else None
        )
        summary["Recommendation_Gaps"] = (
            {
                component: round(gap, 2)
                for component, gap in weighted_gaps.items()
            }
            if weighted_gaps
            else None
        )
        summary["Recommendation_Component"] = (
            selected_gap[0] if selected_gap else None
        )
        summary["Recommendation_Gap"] = (
            round(selected_gap[1], 2) if selected_gap else None
        )
        summary["Recommendation"] = generate_building_recommendation(
            summary,
            weighted_gaps,
            component_efficiencies
        )
        buildings.append(summary)

    return buildings


# ============================================================
# CAMPUS DAILY SUMMARY
# ============================================================


def daily_campus_summary(data):

    if data.empty:
        return pd.DataFrame()

    data = data.copy()

    # Ensure Timestamp is available and converted to datetime
    if "Timestamp" not in data.columns:
        return pd.DataFrame()

    data["Timestamp"] = parse_timestamps(
        data["Timestamp"]
    )

    data = data.dropna(subset=["Timestamp"])

    if data.empty:
        return pd.DataFrame()

    # Building summaries are per-record means; campus daily summaries use
    # daily totals for energy, water, and occupancy, and daily means otherwise.
    data["Date"] = data["Timestamp"].dt.date

    aggregations = {
        "Energy_Consumption_kWh": "sum",
        "Water_Consumption_L": "sum",
        "Occupancy": "sum",
        "Temperature_C": "mean",
        "Humidity_Percent": "mean",
        "CO2_Level_ppm": "mean",
        "BSEI": "mean"
    }

    for column in aggregations:
        if column not in data.columns:
            data[column] = np.nan
        else:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

    daily = (
        data.groupby("Date", sort=True)
        .agg({
            column: (
                (lambda values: values.sum(min_count=1))
                if aggregation == "sum"
                else "mean"
            )
            for column, aggregation in aggregations.items()
        })
        .reset_index()
        .sort_values("Date", kind="stable")
        .reset_index(drop=True)
    )

    return daily


# ============================================================
# API: HEALTH
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status": "online",

        "model_loaded":
            PUBLIC_MODEL is not None,

        "public_records":
            int(
                len(PUBLIC_BSEI_DATA)
            ),

        "bsei_weights": {

            "energy": 45,

            "water": 35,

            "environment": 20
        }
    })


# ============================================================
# API: LATEST PROCESSED AWS SENSOR DATA
# ============================================================

def fetch_processed_aws_records(limit):

    s3 = boto3.client(
        "s3",
        region_name=AWS_DATA_REGION
    )
    paginator = s3.get_paginator("list_objects_v2")
    objects = []
    for page in paginator.paginate(
        Bucket=AWS_DATA_BUCKET,
        Prefix=AWS_DATA_PREFIX
    ):
        objects.extend(
            item
            for item in page.get("Contents", [])
            if item.get("Key", "").lower().endswith(".json")
        )

    objects.sort(
        key=lambda item: (
            (
                item["LastModified"].isoformat()
                if item.get("LastModified")
                else ""
            ),
            item.get("Key", "")
        ),
        reverse=True
    )

    records = []
    malformed_records = 0
    for item in objects[:limit]:
        response = s3.get_object(
            Bucket=AWS_DATA_BUCKET,
            Key=item["Key"]
        )
        try:
            record = json.loads(response["Body"].read())
        except (JSONDecodeError, UnicodeDecodeError, TypeError):
            malformed_records += 1
            continue

        if not isinstance(record, dict):
            malformed_records += 1
            continue

        record["s3Key"] = item["Key"]
        record["s3LastModified"] = (
            item["LastModified"].isoformat()
            if item.get("LastModified")
            else None
        )
        records.append(record)

    return records, malformed_records, len(objects) > limit


def aws_data_error_response(error):

    if isinstance(error, NoCredentialsError):
        app.logger.error(
            "AWS sensor data retrieval failed: no AWS credentials were found."
        )
        return jsonify({
            "error": (
                "AWS credentials are unavailable. Configure the standard "
                "AWS credential chain to access live sensor data."
            )
        }), 503

    if isinstance(error, ClientError):
        aws_error = error.response.get("Error", {})
        error_code = aws_error.get("Code", "Unknown")
        error_message = aws_error.get(
            "Message",
            "AWS returned an error without a message."
        )
        request_id = error.response.get(
            "ResponseMetadata",
            {}
        ).get("RequestId")

        app.logger.error(
            "AWS sensor data retrieval failed "
            "(code=%s, request_id=%s): %s",
            error_code,
            request_id,
            error_message
        )

        if error_code in AWS_EXPIRED_CREDENTIAL_CODES:
            return jsonify({
                "error": (
                    "AWS temporary credentials have expired. Refresh the credentials "
                    "for the active AWS profile and restart Flask."
                ),
                "awsErrorCode": error_code,
                "requestId": request_id
            }), 503

        if error_code in AWS_INVALID_CREDENTIAL_CODES:
            return jsonify({
                "error": (
                    "AWS rejected the configured credentials. Verify the "
                    "active AWS profile, refresh its credentials, and restart "
                    "Flask."
                ),
                "awsErrorCode": error_code,
                "requestId": request_id
            }), 503

        if error_code == "RequestExpired":
            return jsonify({
                "error": (
                    "AWS rejected the request as expired. Verify the system "
                    "clock and refresh the active AWS credentials."
                ),
                "awsErrorCode": error_code,
                "requestId": request_id
            }), 503

        if error_code in AWS_ACCESS_DENIED_CODES:
            return jsonify({
                "error": (
                    "AWS denied access to the processed sensor data. Check "
                    "s3:ListBucket and s3:GetObject permissions for the "
                    "configured bucket and prefix."
                ),
                "awsErrorCode": error_code,
                "requestId": request_id
            }), 403

        return jsonify({
            "error": (
                f"AWS S3 request failed ({error_code}): {error_message}"
            ),
            "awsErrorCode": error_code,
            "requestId": request_id
        }), 502

    app.logger.error(
        "AWS sensor data retrieval failed (%s): %s",
        type(error).__name__,
        error
    )
    return jsonify({
        "error": (
            f"Unable to retrieve live sensor data from S3: {error}"
        ),
        "awsErrorType": type(error).__name__
    }), 502


def aws_record_timestamp(record):

    for field in (
        "timestamp",
        "Timestamp",
        "timestamp_utc",
        "timestampUtc"
    ):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            continue

        parsed = pd.to_datetime(
            value,
            errors="coerce",
            utc=True
        )
        if not pd.isna(parsed):
            return parsed.to_pydatetime()

    return None


def aws_record_sort_key(record):

    timestamp = aws_record_timestamp(record)
    return (
        timestamp is None,
        timestamp or datetime.max.replace(tzinfo=timezone.utc)
    )


def aws_records_response(records, malformed_records, has_more, limit):

    return jsonify({
        "records": records,
        "count": len(records),
        "malformedRecords": malformed_records,
        "hasMore": has_more,
        "limit": limit,
        "bucket": AWS_DATA_BUCKET,
        "region": AWS_DATA_REGION,
        "prefix": AWS_DATA_PREFIX,
        "retrievedAt": datetime.now(timezone.utc).isoformat()
    })


@app.route(
    "/api/aws-data",
    methods=["GET"]
)
def aws_data():

    try:
        records, malformed_records, has_more = fetch_processed_aws_records(
            AWS_DATA_MAX_RECORDS
        )
        return aws_records_response(
            records,
            malformed_records,
            has_more,
            AWS_DATA_MAX_RECORDS
        )

    except (NoCredentialsError, ClientError, BotoCoreError) as error:
        return aws_data_error_response(error)


@app.route(
    "/api/aws-data/history",
    methods=["GET"]
)
def aws_data_history():

    limit_value = request.args.get("limit")
    try:
        limit = (
            int(limit_value)
            if limit_value is not None
            else AWS_HISTORY_DEFAULT_RECORDS
        )
    except ValueError:
        return jsonify({
            "error": (
                f"limit must be an integer between 1 and "
                f"{AWS_HISTORY_MAX_RECORDS}."
            )
        }), 400

    if not 1 <= limit <= AWS_HISTORY_MAX_RECORDS:
        return jsonify({
            "error": (
                f"limit must be between 1 and "
                f"{AWS_HISTORY_MAX_RECORDS}."
            )
        }), 400

    try:
        records, malformed_records, has_more = fetch_processed_aws_records(
            limit
        )
        records.sort(key=aws_record_sort_key)
        return aws_records_response(
            records,
            malformed_records,
            has_more,
            limit
        )

    except (NoCredentialsError, ClientError, BotoCoreError) as error:
        return aws_data_error_response(error)


# ============================================================
# API: ANALYTICS
# ============================================================

@app.route(
    "/api/analytics",
    methods=["GET"]
)
def analytics():

    try:

        data = load_sensor_data()

        if data.empty:

            return jsonify({

                "energyConsumption": 0,

                "waterConsumption": 0,

                "occupancy": 0,

                "bsei": 0,

                "temperature": 0,

                "humidity": 0,

                "co2": 0,

                "records": 0
            })

        daily = daily_campus_summary(
            data
        )

        if daily.empty:

            return jsonify({

                "energyConsumption": None,
                "waterConsumption": None,
                "occupancy": None,
                "bsei": None,
                "temperature": None,
                "humidity": None,
                "co2": None,
                "records": int(len(data))
            })

        # Campus daily average.
        energy = float(
            daily[
                "Energy_Consumption_kWh"
            ].mean()
        )

        water = float(
            daily[
                "Water_Consumption_L"
            ].mean()
        )

        occupancy = float(
            daily[
                "Occupancy"
            ].mean()
        )

        bsei = float(
            daily[
                "BSEI"
            ].mean()
        )

        temperature = float(
            daily[
                "Temperature_C"
            ].mean()
        )

        humidity = float(
            daily[
                "Humidity_Percent"
            ].mean()
        )

        co2 = float(
            daily[
                "CO2_Level_ppm"
            ].mean()
        )

        return jsonify({

            "energyConsumption":
                rounded_metric(energy),

            "waterConsumption":
                rounded_metric(water),

            "occupancy":
                rounded_metric(occupancy),

            "bsei":
                rounded_metric(bsei),

            "temperature":
                rounded_metric(temperature),

            "humidity":
                rounded_metric(humidity),

            "co2":
                rounded_metric(co2),

            "records":
                int(len(data)),

            "bseiWeights": {

                "energy": 45,

                "water": 35,

                "environment": 20
            }
        })

    except Exception as error:

        print(
            "Analytics error:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# API: SUSTAINABILITY / DIGITAL TWIN
# ============================================================

@app.route(
    "/api/sustainability",
    methods=["GET"]
)
def sustainability():

    try:

        data = load_sensor_data()

        buildings = get_building_summary(
            data
        )

        return jsonify({

            "buildings":
                buildings,

            "weights": {

                "energy": 45,

                "water": 35,

                "environment": 20
            }
        })

    except Exception as error:

        print(
            "Sustainability error:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# API: ENERGY TREND
# ============================================================

@app.route(
    "/api/energy-trend",
    methods=["GET"]
)
def energy_trend():

    try:

        data = load_sensor_data()

        if data.empty:

            return jsonify([])

        daily = daily_campus_summary(data)

        result = []

        for _, row in daily.iterrows():

            result.append({

                "date":
                    str(row["Date"]),

                "energy":
                    rounded_metric(
                        row["Energy_Consumption_kWh"]
                    ),

                "water":
                    rounded_metric(
                        row["Water_Consumption_L"]
                    ),

                "occupancy":
                    rounded_metric(row["Occupancy"]),

                "co2":
                    rounded_metric(row["CO2_Level_ppm"]),

                "temperature":
                    rounded_metric(row["Temperature_C"]),

                "humidity":
                    rounded_metric(row["Humidity_Percent"]),

                "bsei":
                    rounded_metric(row["BSEI"])
            })

        return jsonify(result)

    except Exception as error:

        print(
            "Energy trend error:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# API: PREDICTIVE ANALYSIS
# ============================================================

@app.route(
    "/api/predictive-analysis",
    methods=["GET"]
)
def predictive_analysis():

    try:

        data = load_sensor_data()

        if data.empty:

            return jsonify({

                "attentionAreas": [],

                "buildingPerformance": [],

                "historicalTrends": [],

                "improvementAreas": {

                    "energy": 45,

                    "water": 35,

                    "environment": 20
                },

                "buildingRecommendations": []
            })

        buildings = get_building_summary(
            data
        )

        # ----------------------------------------------------
        # Attention areas
        # ----------------------------------------------------

        attention = []
        valid_bsei = [
            building["BSEI"]
            for building in buildings
            if building.get("BSEI") is not None
            and np.isfinite(building["BSEI"])
        ]
        campus_mean_bsei = (
            float(np.mean(valid_bsei))
            if valid_bsei
            else None
        )
        components = ("energy", "water", "environment")
        campus_efficiency_values = {
            component: [
                building["Recommendation_Efficiencies"][component]
                for building in buildings
                if building.get("Recommendation_Efficiencies")
                and building["Recommendation_Efficiencies"].get(component)
                is not None
            ]
            for component in components
        }
        campus_efficiency_means = {
            component: (
                float(np.mean(values))
                if values
                else None
            )
            for component, values in campus_efficiency_values.items()
        }
        component_labels = {
            "energy": ("Energy", "⚡", "Review high-load consumption and operating schedules."),
            "water": ("Water", "💧", "Review water-use patterns and investigate conservation opportunities."),
            "environment": ("Environment", "🌿", "Review measured temperature and humidity conditions; check CO₂ readings where available.")
        }

        for building in sorted(
            buildings,
            key=lambda item: (
                item.get("BSEI") is None,
                item.get("BSEI") if item.get("BSEI") is not None else float("inf")
            )
        ):
            bsei = building.get("BSEI")
            efficiencies = building.get("Recommendation_Efficiencies")
            weighted_gaps = building.get("Recommendation_Gaps")
            if (
                bsei is None
                or efficiencies is None
                or weighted_gaps is None
            ):
                continue

            weaker_components = [
                component for component in components
                if efficiencies.get(component) is not None
                and campus_efficiency_means[component] is not None
                and efficiencies[component] < campus_efficiency_means[component]
            ]
            below_campus_bsei = (
                campus_mean_bsei is not None
                and bsei < campus_mean_bsei
            )
            if not below_campus_bsei and not weaker_components:
                continue

            component = max(
                weaker_components or list(components),
                key=lambda key: weighted_gaps.get(key, -1)
            )
            label, icon, recommendation = component_labels[component]
            efficiency = efficiencies[component]
            reasons = []
            if below_campus_bsei:
                reasons.append(
                    f"BSEI {bsei:.2f} is below the campus building mean "
                    f"of {campus_mean_bsei:.2f}"
                )
            if component in weaker_components:
                reasons.append(
                    f"{label.lower()} efficiency ({efficiency:.2f}%) is "
                    f"below the campus building mean of "
                    f"{campus_efficiency_means[component]:.2f}%"
                )
            reasons.append(
                f"its {label.lower()} component contributes a "
                f"{weighted_gaps[component]:.2f}-point weighted BSEI gap"
            )

            alert = {
                "area": f"{label} monitoring priority",
                "title": (
                    "Water Efficiency Monitoring Priority"
                    if component == "water"
                    else f"{label} Monitoring Priority"
                ),
                "status": "Monitor",
                "severity": "monitor",
                "icon": icon,
                "affected": building["Building_ID"],
                "metric": f"{label} component efficiency",
                "component": component,
                "value": rounded_metric(efficiency),
                "unit": "% efficiency",
                "bsei": rounded_metric(bsei),
                "weightedGap": rounded_metric(weighted_gaps[component]),
                "message": "; ".join(reasons) + ".",
                "recommendation": recommendation
            }
            if component == "water":
                water_consumption = building.get("Water_Consumption_L")
                if water_consumption is not None and np.isfinite(water_consumption):
                    alert["observedConsumption"] = rounded_metric(
                        water_consumption
                    )
                    alert["consumptionUnit"] = "L per sensor record"
                    alert["recommendation"] = (
                        "Review water-use patterns and investigate "
                        "conservation opportunities."
                    )
            attention.append(alert)

            water_efficiency = efficiencies.get("water")
            water_gap = weighted_gaps.get("water")
            water_consumption = building.get("Water_Consumption_L")
            if (
                component != "water"
                and "water" in weaker_components
                and water_efficiency is not None
                and water_gap is not None
                and water_gap > 0
                and water_consumption is not None
                and np.isfinite(water_consumption)
            ):
                attention.append({
                    "area": "Water monitoring priority",
                    "title": "Water Efficiency Monitoring Priority",
                    "status": "Monitor",
                    "severity": "monitor",
                    "icon": "💧",
                    "affected": building["Building_ID"],
                    "metric": "Water component efficiency",
                    "component": "water",
                    "value": rounded_metric(water_efficiency),
                    "unit": "% efficiency",
                    "bsei": rounded_metric(bsei),
                    "weightedGap": rounded_metric(water_gap),
                    "observedConsumption": rounded_metric(water_consumption),
                    "consumptionUnit": "L per sensor record",
                    "message": (
                        f"Water efficiency ({water_efficiency:.2f}%) is "
                        f"below the campus building mean of "
                        f"{campus_efficiency_means['water']:.2f}%; the water "
                        f"component contributes a {water_gap:.2f}-point "
                        "weighted BSEI gap."
                    ),
                    "recommendation": (
                        "Review water-use patterns and investigate "
                        "conservation opportunities."
                    )
                })

        # ----------------------------------------------------
        # Historical trends
        # ----------------------------------------------------

        daily = daily_campus_summary(
            data
        )

        historical = []

        for _, row in daily.iterrows():

            historical.append({

                "date":
                    str(row["Date"]),

                "energy":
                    rounded_metric(row["Energy_Consumption_kWh"]),

                "water":
                    rounded_metric(row["Water_Consumption_L"]),

                "bsei":
                    rounded_metric(row["BSEI"])
            })

        return jsonify({

            "attentionAreas":
                attention,

            "buildingPerformance":
                buildings,

            "historicalTrends":
                historical,

            "improvementAreas": {

                "energy": 45,

                "water": 35,

                "environment": 20
            },

            "buildingRecommendations":
                buildings,

            "weights": {

                "energy": 45,

                "water": 35,

                "environment": 20
            }
        })

    except Exception as error:

        print(
            "Predictive analysis error:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# MODEL FEATURE PREPARATION
# ============================================================

MODEL_FEATURES = [

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

    "is_weekend"
]


# ============================================================
# CREATE MODEL INPUT
# ============================================================

def create_model_input(values):

    energy = float(
        values.get(
            "energy_consumption_kWh",
            values.get(
                "energy",
                0
            )
        )
    )

    water = float(
        values.get(
            "water_consumption_L",
            values.get(
                "water",
                0
            )
        )
    )

    avg_power = float(
        values.get(
            "avg_power_kW",
            values.get(
                "avgPower",
                energy / 24
            )
        )
    )

    electricity_coverage = float(
        values.get(
            "electricity_coverage",
            values.get(
                "electricityCoverage",
                100
            )
        )
    )

    water_coverage = float(
        values.get(
            "water_coverage",
            values.get(
                "waterCoverage",
                100
            )
        )
    )

    temperature = float(
        values.get(
            "air_temperature",
            values.get(
                "temperature",
                25
            )
        )
    )

    humidity = float(
        values.get(
            "relative_humidity",
            values.get(
                "humidity",
                60
            )
        )
    )

    day_of_week = int(
        values.get(
            "day_of_week",
            values.get(
                "dayOfWeek",
                0
            )
        )
    )

    month = int(
        values.get(
            "month",
            1
        )
    )

    is_weekend = int(
        values.get(
            "is_weekend",
            values.get(
                "weekend",
                0
            )
        )
    )

    # --------------------------------------------------------
    # Relative values
    # --------------------------------------------------------

    relative_energy = (
        energy / ENERGY_REFERENCE
    )

    relative_water = (
        water / WATER_REFERENCE
    )

    # --------------------------------------------------------
    # Efficiency values
    # --------------------------------------------------------

    energy_efficiency = (
        100 /
        (1 + relative_energy)
    )

    water_efficiency = (
        100 /
        (1 + relative_water)
    )

    # --------------------------------------------------------
    # Environmental deviation
    # --------------------------------------------------------

    temperature_deviation = (
        (temperature - TEMPERATURE_REFERENCE)
        / TEMPERATURE_STD
    )

    humidity_deviation = (
        (humidity - HUMIDITY_REFERENCE)
        / HUMIDITY_STD
    )

    environmental_deviation = np.sqrt(
        temperature_deviation ** 2
        +
        humidity_deviation ** 2
    )

    environmental_efficiency = (
        100 /
        (1 + environmental_deviation)
    )

    values_for_model = {

        "energy_consumption_kWh":
            energy,

        "avg_power_kW":
            avg_power,

        "electricity_coverage":
            electricity_coverage,

        "water_consumption_L":
            water,

        "water_coverage":
            water_coverage,

        "air_temperature":
            temperature,

        "relative_humidity":
            humidity,

        "relative_energy":
            relative_energy,

        "relative_water":
            relative_water,

        "energy_efficiency":
            energy_efficiency,

        "water_efficiency":
            water_efficiency,

        "environmental_deviation":
            environmental_deviation,

        "environmental_efficiency":
            environmental_efficiency,

        "day_of_week":
            day_of_week,

        "month":
            month,

        "is_weekend":
            is_weekend
    }

    return pd.DataFrame(
        [
            [
                values_for_model[
                    feature
                ]
                for feature in MODEL_FEATURES
            ]
        ],
        columns=MODEL_FEATURES
    )

# ============================================================
# API: ML PREDICTION
# ============================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict():

    try:

        if PUBLIC_MODEL is None:

            return jsonify({

                "error":
                    "Public BSEI Random Forest model is not loaded."

            }), 500

        values = request.get_json(
            silent=True
        )

        if not values:

            return jsonify({

                "error":
                    "No prediction input received."

            }), 400

        # ----------------------------------------------------
        # Create model input
        # ----------------------------------------------------

        model_input = create_model_input(
            values
        )

        # ----------------------------------------------------
        # Random Forest prediction
        # ----------------------------------------------------

        prediction = PUBLIC_MODEL.predict(
            model_input
        )

        model_bsei = float(
            prediction[0]
        )

        # ----------------------------------------------------
        # Component efficiencies
        # ----------------------------------------------------

        energy_efficiency = float(
            model_input[
                "energy_efficiency"
            ].iloc[0]
        )

        water_efficiency = float(
            model_input[
                "water_efficiency"
            ].iloc[0]
        )

        environmental_efficiency = float(
            model_input[
                "environmental_efficiency"
            ].iloc[0]
        )

        # ----------------------------------------------------
        # Input-driven BSEI
        # ----------------------------------------------------

        formula_bsei = (

            energy_efficiency
            * ENERGY_WEIGHT

            +

            water_efficiency
            * WATER_WEIGHT

            +

            environmental_efficiency
            * ENVIRONMENT_WEIGHT

        )

        formula_bsei = float(
            np.clip(
                formula_bsei,
                0,
                100
            )
        )

        # ----------------------------------------------------
        # Final prediction
        #
        # 60% Random Forest
        # 40% input-driven BSEI
        # ----------------------------------------------------

        predicted_bsei = (

            (model_bsei * 0.60)

            +

            (formula_bsei * 0.40)

        )

        predicted_bsei = float(
            np.clip(
                predicted_bsei,
                0,
                100
            )
        )

        # ----------------------------------------------------
        # Return prediction
        # ----------------------------------------------------

        return jsonify({

            "predictedBSEI":
                round(
                    predicted_bsei,
                    2
                ),

            "modelBSEI":
                round(
                    float(
                        np.clip(
                            model_bsei,
                            0,
                            100
                        )
                    ),
                    2
                ),

            "formulaBSEI":
                round(
                    formula_bsei,
                    2
                ),

            "energyEfficiency":
                round(
                    energy_efficiency,
                    2
                ),

            "waterEfficiency":
                round(
                    water_efficiency,
                    2
                ),

            "environmentalEfficiency":
                round(
                    environmental_efficiency,
                    2
                ),

            "model":
                "Random Forest Regressor",

            "dataset":
                "UNICON Public Dataset",

            "weights": {

                "energy": 45,

                "water": 35,

                "environment": 20

            }

        })

    except Exception as error:

        print(
            "Prediction error:",
            error
        )

        return jsonify({

            "error":
                str(error)

        }), 500

        
# ============================================================
# API: MODEL INFORMATION
# ============================================================

@app.route(
    "/api/model-info",
    methods=["GET"]
)
def model_info():

    return jsonify({

        "model":
            "Random Forest Regressor",

        "dataset":
            "UNICON Public Dataset",

        "trainingRecords":
            int(
                len(PUBLIC_BSEI_DATA)
            ),

        "features":
            MODEL_FEATURES,

        "weights": {

            "energy": 45,

            "water": 35,

            "environment": 20
        },

        "modelLoaded":
            PUBLIC_MODEL is not None
    })


# ============================================================
# INITIALIZE MODEL AND DATA
# ============================================================

load_public_model()

load_public_bsei_dataset()


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "SMART CAMPUS SUSTAINABILITY ANALYTICS"
    )
    print("=" * 70)

    print("BSEI weights:")

    print(
        "Energy      : 45%"
    )

    print(
        "Water       : 35%"
    )

    print(
        "Environment : 20%"
    )

    print()

    print(
        "Server: http://127.0.0.1:5000"
    )

    print("=" * 70)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )