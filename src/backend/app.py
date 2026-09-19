from flask import Flask, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import json
import joblib


app = Flask(__name__)
CORS(app)


# ============================================================
# PATHS
# ============================================================

DATASET_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../dataset"
    )
)

MODEL_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../ml_model/sustainability_model.pkl"
    )
)


# ============================================================
# LOAD ML MODEL
# ============================================================

model = joblib.load(MODEL_PATH)

FEATURES = [
    "Energy_Consumption_kWh",
    "Water_Consumption_L",
    "Temperature_C",
    "Humidity_Percent",
    "CO2_Level_ppm",
    "Occupancy"
]


# ============================================================
# DATA LOADER
# Automatically loads building CSV / Excel files
# combined_sensor_data.csv is excluded to avoid duplicates
# ============================================================

def load_data():

    dataframes = []

    print("\n======================================")
    print("SCANNING DATASET FOLDER")
    print("======================================")

    print("Dataset folder:")
    print(DATASET_DIR)

    if not os.path.exists(DATASET_DIR):
        raise Exception("Dataset directory does not exist.")

    files = os.listdir(DATASET_DIR)

    # Load individual building datasets only.
    # Do NOT load combined_sensor_data.csv because it
    # contains copies of the same records.
    dataset_files = [
        file
        for file in files
        if file.lower().endswith(
            (".csv", ".xlsx", ".xls")
        )
        and file.lower() != "combined_sensor_data.csv"
    ]

    print("\nFiles detected:")

    for file in dataset_files:
        print("-", file)

    for file in dataset_files:

        path = os.path.join(
            DATASET_DIR,
            file
        )

        try:

            if file.lower().endswith(".csv"):
                df = pd.read_csv(path)

            else:
                df = pd.read_excel(path)

            # Keep track of which dataset produced each row
            df["Dataset_Source"] = file

            dataframes.append(df)

            print(
                f"Loaded {file}: {len(df)} records"
            )

        except Exception as error:

            print(
                f"Could not load {file}: {error}"
            )

    if not dataframes:
        raise Exception(
            "No CSV or Excel datasets found."
        )

    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    # Convert numerical columns safely
    numeric_columns = [
        "Energy_Consumption_kWh",
        "Water_Consumption_L",
        "Temperature_C",
        "Humidity_Percent",
        "CO2_Level_ppm",
        "Occupancy",
        "Sustainability_Score"
    ]

    for column in numeric_columns:

        if column in combined_df.columns:

            combined_df[column] = pd.to_numeric(
                combined_df[column],
                errors="coerce"
            )

    combined_df = combined_df.dropna(
        subset=[
            column
            for column in numeric_columns
            if column in combined_df.columns
        ]
    )

    print("\n======================================")
    print("DATASET SUMMARY")
    print("======================================")

    print(
        "Total datasets:",
        combined_df["Dataset_Source"].nunique()
    )

    print(
        "Total records:",
        len(combined_df)
    )

    print(
        "Average energy:",
        round(
            combined_df[
                "Energy_Consumption_kWh"
            ].mean(),
            2
        )
    )

    print("======================================\n")

    return combined_df


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return {
        "project":
        "Digital Twin Cloud Platform for Smart Campus Sustainability Analytics",

        "status":
        "Backend running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# SENSOR DATA
# ============================================================

@app.route("/api/sensor-data")
def sensor_data():

    df = load_data()

    # Convert NaN / Infinity values to JSON-safe null values
    return json.loads(
        df.to_json(
            orient="records",
            date_format="iso"
        )
    )


# ============================================================
# BUILDINGS
# ============================================================

@app.route("/api/buildings")
def buildings():

    df = load_data()

    if "Building_Type" in df.columns:

        building_list = (
            df["Building_Type"]
            .dropna()
            .unique()
            .tolist()
        )

    elif "Building_ID" in df.columns:

        building_list = (
            df["Building_ID"]
            .dropna()
            .unique()
            .tolist()
        )

    else:

        building_list = []

    return {
        "buildings": building_list
    }


# ============================================================
# BASIC ANALYTICS
# ============================================================

@app.route("/api/analytics")
def analytics():

    df = load_data()

    # --------------------------------------------------------
    # Campus-wide daily aggregation
    # --------------------------------------------------------
    #
    # Each date contains 4 building records.
    # We first sum the four buildings for each day,
    # then calculate the average daily campus value.
    #
    # Therefore:
    #
    # Energy     = campus-wide kWh/day
    # Water      = campus-wide L/day
    # Occupancy  = total people present across buildings
    #
    # Environmental values remain averages because they
    # represent environmental conditions rather than
    # additive resource consumption.
    # --------------------------------------------------------

    daily = (
        df.groupby("Timestamp")
        .agg({
            "Energy_Consumption_kWh": "sum",
            "Water_Consumption_L": "sum",
            "Occupancy": "sum"
        })
    )

    return {

        "total_records":
        len(df),

        "total_datasets":
        df["Dataset_Source"].nunique(),

        # Campus-wide average daily energy
        "average_energy":
        round(
            daily[
                "Energy_Consumption_kWh"
            ].mean(),
            2
        ),

        # Campus-wide average daily water
        "average_water":
        round(
            daily[
                "Water_Consumption_L"
            ].mean(),
            2
        ),

        # Campus-wide average daily occupancy
        "average_occupancy":
        round(
            daily[
                "Occupancy"
            ].mean(),
            2
        ),

        # Environmental metrics
        "average_temperature":
        round(
            df[
                "Temperature_C"
            ].mean(),
            2
        ),

        "average_humidity":
        round(
            df[
                "Humidity_Percent"
            ].mean(),
            2
        ),

        "average_co2":
        round(
            df[
                "CO2_Level_ppm"
            ].mean(),
            2
        ),

        # Sustainability score
        "average_sustainability_score":
        round(
            df[
                "Sustainability_Score"
            ].mean(),
            2
        )
    }


# ============================================================
# BUILDING SUSTAINABILITY
# ============================================================

@app.route("/api/sustainability")
def sustainability():

    df = load_data()

    if "Building_Type" in df.columns:

        result = (
            df.groupby(
                "Building_Type"
            )[
                "Sustainability_Score"
            ]
            .mean()
            .round(2)
            .to_dict()
        )

    elif "Building_ID" in df.columns:

        result = (
            df.groupby(
                "Building_ID"
            )[
                "Sustainability_Score"
            ]
            .mean()
            .round(2)
            .to_dict()
        )

    else:

        result = {}

    return {
        "sustainability_scores":
        result
    }


# ============================================================
# DATASET INFORMATION
# ============================================================

@app.route("/api/datasets")
def datasets():

    df = load_data()

    dataset_info = (
        df.groupby(
            "Dataset_Source"
        )
        .size()
        .reset_index(
            name="records"
        )
        .to_dict(
            orient="records"
        )
    )

    return {
        "datasets": dataset_info
    }


# ============================================================
# PREDICTIVE ANALYSIS
# ============================================================

@app.route("/api/predictive-analysis")
def predictive_analysis():

    df = load_data()

    # --------------------------------------------------------
    # Campus summary
    # --------------------------------------------------------
    #
    # Keep these as dataset averages for predictive analysis.
    # Building-level comparisons and recommendation logic
    # depend on this same reference baseline.
    # --------------------------------------------------------

    campus = {
        "energy":
        df[
            "Energy_Consumption_kWh"
        ].mean(),

        "water":
        df[
            "Water_Consumption_L"
        ].mean(),

        "temperature":
        df[
            "Temperature_C"
        ].mean(),

        "humidity":
        df[
            "Humidity_Percent"
        ].mean(),

        "co2":
        df[
            "CO2_Level_ppm"
        ].mean(),

        "occupancy":
        df[
            "Occupancy"
        ].mean(),

        "sustainability":
        df[
            "Sustainability_Score"
        ].mean()
    }


    # --------------------------------------------------------
    # Building analysis
    # --------------------------------------------------------

    building_column = None

    if "Building_Type" in df.columns:

        building_column = "Building_Type"

    elif "Building_ID" in df.columns:

        building_column = "Building_ID"

    building_analysis = []

    if building_column:

        grouped = df.groupby(
            building_column
        )

        campus_score = campus[
            "sustainability"
        ]

        for building, group in grouped:

            score = group[
                "Sustainability_Score"
            ].mean()

            energy = group[
                "Energy_Consumption_kWh"
            ].mean()

            water = group[
                "Water_Consumption_L"
            ].mean()

            co2 = group[
                "CO2_Level_ppm"
            ].mean()

            occupancy = group[
                "Occupancy"
            ].mean()

            # Difference from campus average
            score_difference = (
                score - campus_score
            )

            building_analysis.append({

                "building":
                str(building),

                "sustainability_score":
                round(
                    score,
                    2
                ),

                "energy":
                round(
                    energy,
                    2
                ),

                "water":
                round(
                    water,
                    2
                ),

                "co2":
                round(
                    co2,
                    2
                ),

                "occupancy":
                round(
                    occupancy,
                    2
                ),

                "score_difference":
                round(
                    score_difference,
                    2
                )
            })


    # --------------------------------------------------------
    # Identify areas requiring attention
    # --------------------------------------------------------

    attention = []

    energy_threshold = (
        campus["energy"] * 1.15
    )

    water_threshold = (
        campus["water"] * 1.15
    )

    co2_threshold = (
        campus["co2"] * 1.15
    )

    sustainability_threshold = (
        campus["sustainability"] * 0.90
    )


    if campus["energy"] > 0:

        high_energy = df[
            df[
                "Energy_Consumption_kWh"
            ]
            > energy_threshold
        ]

        if len(high_energy) > 0:

            attention.append({

                "area":
                "Energy Consumption",

                "severity":
                "High",

                "description":
                "Energy consumption is elevated in a significant portion of observations compared with the campus average.",

                "recommendation":
                "Review energy-intensive equipment, operating schedules and building-level consumption patterns."
            })


    if campus["water"] > 0:

        high_water = df[
            df[
                "Water_Consumption_L"
            ]
            > water_threshold
        ]

        if len(high_water) > 0:

            attention.append({

                "area":
                "Water Consumption",

                "severity":
                "High",

                "description":
                "Water consumption is elevated in a significant portion of observations compared with the campus average.",

                "recommendation":
                "Investigate water-intensive activities and monitor possible leakage or unnecessary consumption."
            })


    if campus["co2"] > 0:

        high_co2 = df[
            df[
                "CO2_Level_ppm"
            ]
            > co2_threshold
        ]

        if len(high_co2) > 0:

            attention.append({

                "area":
                "CO₂ Levels",

                "severity":
                "Monitor",

                "description":
                "Some observations show CO₂ levels above the campus average range.",

                "recommendation":
                "Monitor ventilation and occupancy conditions in areas with elevated CO₂."
            })


    low_sustainability = df[
        df[
            "Sustainability_Score"
        ]
        < sustainability_threshold
    ]

    if len(low_sustainability) > 0:

        attention.append({

            "area":
            "Sustainability Score",

            "severity":
            "Attention",

            "description":
            "Some observations have sustainability scores substantially below the campus average.",

            "recommendation":
            "Focus improvement efforts on reducing resource consumption while maintaining suitable environmental conditions."
        })


    # --------------------------------------------------------
    # Building-specific recommendations
    # --------------------------------------------------------

    building_recommendations = []

    for item in building_analysis:

        recommendations = []

        if item["energy"] > (
            campus["energy"] * 1.15
        ):

            recommendations.append(
                "Reduce energy consumption"
            )

        if item["water"] > (
            campus["water"] * 1.15
        ):

            recommendations.append(
                "Monitor water usage"
            )

        if item["co2"] > (
            campus["co2"] * 1.15
        ):

            recommendations.append(
                "Review ventilation conditions"
            )

        if item[
            "sustainability_score"
        ] < sustainability_threshold:

            recommendations.append(
                "Prioritize sustainability improvements"
            )

        if recommendations:

            building_recommendations.append({

                "building":
                item["building"],

                "recommendations":
                recommendations
            })


    # --------------------------------------------------------
    # Historical trend analysis
    # --------------------------------------------------------

    trend = {}

    if "Timestamp" in df.columns:

        try:

            time_df = df.copy()

            time_df["Timestamp"] = pd.to_datetime(
                time_df["Timestamp"],
                errors="coerce",
                dayfirst=True
            )

            time_df = time_df.dropna(
                subset=[
                    "Timestamp"
                ]
            )

            if len(time_df) >= 4:

                time_df = time_df.sort_values(
                    "Timestamp"
                )

                midpoint = len(
                    time_df
                ) // 2

                first_half = time_df.iloc[
                    :midpoint
                ]

                second_half = time_df.iloc[
                    midpoint:
                ]

                metrics = {

                    "energy":
                    "Energy_Consumption_kWh",

                    "water":
                    "Water_Consumption_L",

                    "co2":
                    "CO2_Level_ppm",

                    "sustainability":
                    "Sustainability_Score"
                }

                for name, column in metrics.items():

                    first_value = first_half[
                        column
                    ].mean()

                    second_value = second_half[
                        column
                    ].mean()

                    if first_value != 0:

                        percentage_change = (
                            (
                                second_value
                                - first_value
                            )
                            / first_value
                        ) * 100

                    else:

                        percentage_change = 0

                    if percentage_change > 5:

                        direction = "Increasing"

                    elif percentage_change < -5:

                        direction = "Decreasing"

                    else:

                        direction = "Stable"

                    trend[name] = {

                        "direction":
                        direction,

                        "percentage_change":
                        round(
                            percentage_change,
                            2
                        )
                    }

        except Exception:

            trend = {}


    # --------------------------------------------------------
    # Model feature importance
    # --------------------------------------------------------

    feature_importance = {}

    if hasattr(
        model,
        "feature_importances_"
    ):

        importances = (
            model.feature_importances_
        )

        for feature, importance in zip(
            FEATURES,
            importances
        ):

            feature_importance[
                feature
            ] = round(
                float(importance) * 100,
                2
            )


    # --------------------------------------------------------
    # Overall improvement summary
    # --------------------------------------------------------

    improvement_areas = []

    if campus["energy"] > 0:

        improvement_areas.append({

            "area":
            "Energy Efficiency",

            "reason":
            "Energy consumption is one of the primary resource metrics tracked by the platform.",

            "action":
            "Identify high-consumption buildings and review energy-intensive operations."
        })


    if campus["water"] > 0:

        improvement_areas.append({

            "area":
            "Water Efficiency",

            "reason":
            "Water usage contributes directly to campus resource consumption.",

            "action":
            "Monitor high-use areas and investigate abnormal consumption patterns."
        })


    if campus["co2"] > 0:

        improvement_areas.append({

            "area":
            "Indoor Environmental Conditions",

            "reason":
            "CO₂ levels provide an indication of environmental conditions associated with occupancy.",

            "action":
            "Monitor elevated CO₂ observations and review ventilation conditions."
        })


    return {

        "campus_summary": {

            key:
            round(
                float(value),
                2
            )

            for key, value
            in campus.items()
        },

        "building_analysis":
        building_analysis,

        "attention_areas":
        attention,

        "building_recommendations":
        building_recommendations,

        "trend_analysis":
        trend,

        "feature_importance":
        feature_importance,

        "improvement_areas":
        improvement_areas
    }


# ============================================================
# ML PREDICTION
# ============================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict():

    data = request.get_json()

    energy = float(
        data[
            "Energy_Consumption_kWh"
        ]
    )

    water = float(
        data[
            "Water_Consumption_L"
        ]
    )

    temperature = float(
        data[
            "Temperature_C"
        ]
    )

    humidity = float(
        data[
            "Humidity_Percent"
        ]
    )

    co2 = float(
        data[
            "CO2_Level_ppm"
        ]
    )

    occupancy = int(
        data[
            "Occupancy"
        ]
    )

    input_data = [[

        energy,

        water,

        temperature,

        humidity,

        co2,

        occupancy
    ]]

    prediction = model.predict(
        input_data
    )[0]

    # Keep prediction within a sensible
    # sustainability-score range
    prediction = max(
        0,
        min(
            100,
            float(prediction)
        )
    )

    return {

        "predicted_sustainability_score":
        round(
            prediction,
            2
        )
    }


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    print("\n======================================")
    print("DIGITAL TWIN CLOUD BACKEND")
    print("======================================")

    print(
        "Dataset directory:"
    )

    print(
        DATASET_DIR
    )

    print(
        "\nPredictive analysis enabled"
    )

    print("======================================\n")

    app.run(
        debug=True
    )