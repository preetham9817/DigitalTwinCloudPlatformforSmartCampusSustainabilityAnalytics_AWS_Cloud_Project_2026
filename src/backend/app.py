from flask import Flask, request
from flask_cors import CORS
import pandas as pd
import os
import joblib

app = Flask(__name__)
CORS(app)


# =========================
# PATHS
# =========================

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


# =========================
# LOAD ML MODEL
# =========================

model = joblib.load(MODEL_PATH)


# =========================
# LOAD ALL DATASETS
# =========================

def load_data():

    dataframes = []

    print("\n======================================")
    print("SCANNING DATASET FOLDER")
    print("======================================")

    print("Dataset folder:")
    print(DATASET_DIR)

    # Get every file inside dataset folder
    files = os.listdir(DATASET_DIR)

    # Only accept CSV and Excel files
    dataset_files = [
        file
        for file in files
        if file.lower().endswith(
            (".csv", ".xlsx", ".xls")
        )
    ]

    print("\nFiles detected:")

    for file in dataset_files:
        print("-", file)

    # Read every dataset
    for file in dataset_files:

        path = os.path.join(
            DATASET_DIR,
            file
        )

        try:

            # CSV
            if file.lower().endswith(".csv"):

                df = pd.read_csv(path)

            # Excel
            else:

                df = pd.read_excel(path)

            # Store filename as source
            df["Dataset_Source"] = file

            dataframes.append(df)

            print(
                f"Loaded {file}: {len(df)} records"
            )

        except Exception as error:

            print(
                f"Could not load {file}: {error}"
            )

    # No datasets found
    if not dataframes:

        raise Exception(
            "No CSV or Excel datasets found."
        )

    # Combine everything
    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    print("\n======================================")
    print("DATASET SUMMARY")
    print("======================================")

    print(
        "Total files:",
        len(dataframes)
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


# =========================
# HOME
# =========================

@app.route("/")
def home():

    return {
        "project":
        "Digital Twin Cloud Platform for Smart Campus Sustainability Analytics",

        "status":
        "Backend running"
    }


# =========================
# HEALTH
# =========================

@app.route("/api/health")
def health():

    return {
        "status": "healthy"
    }


# =========================
# SENSOR DATA
# =========================

@app.route("/api/sensor-data")
def sensor_data():

    df = load_data()

    return df.to_dict(
        orient="records"
    )


# =========================
# BUILDINGS
# =========================

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


# =========================
# ANALYTICS
# =========================

@app.route("/api/analytics")
def analytics():

    df = load_data()

    return {

        "total_records":
        len(df),

        "total_datasets":
        df["Dataset_Source"]
        .nunique(),

        "average_energy":
        round(
            df[
                "Energy_Consumption_kWh"
            ].mean(),
            2
        ),

        "average_water":
        round(
            df[
                "Water_Consumption_L"
            ].mean(),
            2
        ),

        "average_occupancy":
        round(
            df[
                "Occupancy"
            ].mean(),
            2
        ),

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

        "average_sustainability_score":
        round(
            df[
                "Sustainability_Score"
            ].mean(),
            2
        )
    }


# =========================
# SUSTAINABILITY BY BUILDING
# =========================

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


# =========================
# DATASET INFORMATION
# =========================

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


# =========================
# ML PREDICTION
# =========================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict():

    data = request.get_json()

    energy = float(
        data["Energy_Consumption_kWh"]
    )

    water = float(
        data["Water_Consumption_L"]
    )

    temperature = float(
        data["Temperature_C"]
    )

    humidity = float(
        data["Humidity_Percent"]
    )

    co2 = float(
        data["CO2_Level_ppm"]
    )

    occupancy = int(
        data["Occupancy"]
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

    return {

        "predicted_sustainability_score":
        round(
            float(prediction),
            2
        )
    }


# =========================
# START SERVER
# =========================

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
        "\nBackend automatically reads:"
    )

    print(
        "CSV files"
    )

    print(
        "Excel files"
    )

    print("======================================\n")

    app.run(
        debug=True
    )