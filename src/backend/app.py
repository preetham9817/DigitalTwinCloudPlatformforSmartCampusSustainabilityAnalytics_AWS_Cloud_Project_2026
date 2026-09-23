import os
import json
import joblib
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

from flask import Flask, jsonify, request
from flask_cors import CORS

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

    combined["Timestamp"] = pd.to_datetime(
        combined["Timestamp"],
        errors="coerce"
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

    try:

        return calculate_bsei(
            row.get(
                "Energy_Consumption_kWh",
                0
            ),
            row.get(
                "Water_Consumption_L",
                0
            ),
            row.get(
                "Temperature_C",
                TEMPERATURE_REFERENCE
            ),
            row.get(
                "Humidity_Percent",
                HUMIDITY_REFERENCE
            )
        )

    except Exception:

        return 0.0


# ============================================================
# BUILDING RECOMMENDATION
# ============================================================

def generate_building_recommendation(
    building
):

    try:

        bsei = float(
            building.get("BSEI", 0)
        )

        energy = float(
            building.get(
                "Energy_Consumption_kWh",
                0
            )
        )

        water = float(
            building.get(
                "Water_Consumption_L",
                0
            )
        )

        co2 = float(
            building.get(
                "CO2_Level_ppm",
                0
            )
        )

        # ----------------------------------------------------
        # Identify the most relevant issue.
        # ----------------------------------------------------

        energy_ratio = (
            energy / ENERGY_REFERENCE
        )

        water_ratio = (
            water / WATER_REFERENCE
        )

        environmental_ratio = (
            co2 / 800.0
        )

        # ----------------------------------------------------
        # Low BSEI
        # ----------------------------------------------------

        if bsei < 40:

            if water_ratio >= energy_ratio:

                return (
                    "Prioritize water conservation using "
                    "low-flow fixtures and monitor high-use areas."
                )

            return (
                "Prioritize energy efficiency by optimizing "
                "high-load equipment and reducing unnecessary usage."
            )

        # ----------------------------------------------------
        # Medium BSEI
        # ----------------------------------------------------

        if bsei < 60:

            if environmental_ratio > 1:

                return (
                    "Improve ventilation and occupancy management "
                    "to reduce elevated environmental loads."
                )

            if water_ratio > energy_ratio:

                return (
                    "Reduce water consumption through efficient "
                    "fixtures and improved usage monitoring."
                )

            return (
                "Optimize energy usage through equipment scheduling "
                "and improved load management."
            )

        # ----------------------------------------------------
        # Good BSEI
        # ----------------------------------------------------

        if co2 > 700:

            return (
                "Maintain resource efficiency while improving "
                "ventilation to control CO2 levels."
            )

        return (
            "Maintain current sustainability performance and "
            "continue monitoring energy, water and environmental trends."
        )

    except Exception:

        return (
            "Continue monitoring energy, water and environmental "
            "conditions for further sustainability improvements."
        )


# ============================================================
# BUILDING SUMMARY
# ============================================================

def get_building_summary(data):

    buildings = []

    if data.empty:

        return buildings

    for building_name in BUILDING_ORDER:

        building_data = data[
            data["Building_ID"].str.lower()
            ==
            building_name.lower()
        ]

        if building_data.empty:

            continue

        summary = {

            "Building_ID":
                building_name,

            "Energy_Consumption_kWh":
                float(
                    building_data[
                        "Energy_Consumption_kWh"
                    ].mean()
                ),

            "Water_Consumption_L":
                float(
                    building_data[
                        "Water_Consumption_L"
                    ].mean()
                ),

            "Occupancy":
                float(
                    building_data[
                        "Occupancy"
                    ].mean()
                ),

            "Temperature_C":
                float(
                    building_data[
                        "Temperature_C"
                    ].mean()
                ),

            "Humidity_Percent":
                float(
                    building_data[
                        "Humidity_Percent"
                    ].mean()
                ),

            "CO2_Level_ppm":
                float(
                    building_data[
                        "CO2_Level_ppm"
                    ].mean()
                ),

            "BSEI":
                float(
                    building_data[
                        "BSEI"
                    ].mean()
                ),

            "Records":
                int(
                    len(building_data)
                )
        }

        summary["Recommendation"] = (
            generate_building_recommendation(
                summary
            )
        )

        buildings.append(summary)

    return buildings


# ============================================================
# CAMPUS DAILY SUMMARY
# ============================================================

def daily_campus_summary(data):

    if data.empty:

        return pd.DataFrame()

    daily = (
        data
        .groupby(
            data["Timestamp"].dt.date
        )
        .agg({

            "Energy_Consumption_kWh":
                "sum",

            "Water_Consumption_L":
                "sum",

            "Occupancy":
                "sum",

            "Temperature_C":
                "mean",

            "Humidity_Percent":
                "mean",

            "CO2_Level_ppm":
                "mean",

            "BSEI":
                "mean"
        })
        .reset_index()
    )

    daily.rename(
        columns={
            "Timestamp": "Date"
        },
        inplace=True
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

                "energyConsumption": 0,
                "waterConsumption": 0,
                "occupancy": 0,
                "bsei": 0,
                "temperature": 0,
                "humidity": 0,
                "co2": 0,
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
                round(energy, 2),

            "waterConsumption":
                round(water, 2),

            "occupancy":
                round(occupancy, 2),

            "bsei":
                round(bsei, 2),

            "temperature":
                round(temperature, 2),

            "humidity":
                round(humidity, 2),

            "co2":
                round(co2, 2),

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

        daily = (
            data
            .groupby(
                data["Timestamp"].dt.date
            )
            .agg({

                "Energy_Consumption_kWh":
                    "sum",

                "Water_Consumption_L":
                    "sum",

                "Occupancy":
                    "sum",

                "CO2_Level_ppm":
                    "mean",

                "Temperature_C":
                    "mean",

                "Humidity_Percent":
                    "mean",

                "BSEI":
                    "mean"
            })
            .reset_index()
        )

        result = []

        for _, row in daily.iterrows():

            result.append({

                "date":
                    str(row["Timestamp"]),

                "energy":
                    round(
                        float(
                            row[
                                "Energy_Consumption_kWh"
                            ]
                        ),
                        2
                    ),

                "water":
                    round(
                        float(
                            row[
                                "Water_Consumption_L"
                            ]
                        ),
                        2
                    ),

                "occupancy":
                    round(
                        float(
                            row[
                                "Occupancy"
                            ]
                        ),
                        2
                    ),

                "co2":
                    round(
                        float(
                            row[
                                "CO2_Level_ppm"
                            ]
                        ),
                        2
                    ),

                "temperature":
                    round(
                        float(
                            row[
                                "Temperature_C"
                            ]
                        ),
                        2
                    ),

                "humidity":
                    round(
                        float(
                            row[
                                "Humidity_Percent"
                            ]
                        ),
                        2
                    ),

                "bsei":
                    round(
                        float(
                            row[
                                "BSEI"
                            ]
                        ),
                        2
                    )
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

        campus_energy = float(
            data[
                "Energy_Consumption_kWh"
            ].mean()
        )

        campus_water = float(
            data[
                "Water_Consumption_L"
            ].mean()
        )

        campus_co2 = float(
            data[
                "CO2_Level_ppm"
            ].mean()
        )

        if campus_energy > ENERGY_REFERENCE:

            attention.append({

                "area": "Energy",

                "value":
                    round(
                        campus_energy,
                        2
                    ),

                "message":
                    "Energy consumption is above the reference level."
            })

        if campus_water > WATER_REFERENCE:

            attention.append({

                "area": "Water",

                "value":
                    round(
                        campus_water,
                        2
                    ),

                "message":
                    "Water consumption is above the reference level."
            })

        if campus_co2 > 700:

            attention.append({

                "area": "Environment",

                "value":
                    round(
                        campus_co2,
                        2
                    ),

                "message":
                    "Elevated CO2 levels require ventilation attention."
            })

        # Always provide useful information.
        if not attention:

            attention.append({

                "area": "Monitoring",

                "value":
                    round(
                        float(
                            data["BSEI"].mean()
                        ),
                        2
                    ),

                "message":
                    "Continue monitoring energy, water and environmental trends."
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
                    str(row["Timestamp"]),

                "energy":
                    round(
                        float(
                            row[
                                "Energy_Consumption_kWh"
                            ]
                        ),
                        2
                    ),

                "water":
                    round(
                        float(
                            row[
                                "Water_Consumption_L"
                            ]
                        ),
                        2
                    ),

                "bsei":
                    round(
                        float(
                            row["BSEI"]
                        ),
                        2
                    )
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