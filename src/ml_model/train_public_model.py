import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import (
    train_test_split,
    KFold,
    cross_val_score
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)


DATASET_PATH = os.path.join(
    BASE_DIR,
    "public_dataset",
    "public_bsei_dataset.csv"
)


MODEL_DIR = os.path.join(
    BASE_DIR,
    "src",
    "ml_model"
)


MODEL_PATH = os.path.join(
    MODEL_DIR,
    "public_bsei_model.pkl"
)


CONFIG_PATH = os.path.join(
    MODEL_DIR,
    "model_config.json"
)


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURES = [

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


TARGET = "BSEI"


# ============================================================
# MODEL CONFIGURATION
# ============================================================

CONFIG = {

    "model_type": "Random Forest Regressor",

    "dataset": "UNICON Public Dataset",

    "target": TARGET,

    "features": FEATURES,

    "bsei_weights": {

        "energy": 0.45,

        "water": 0.35,

        "environment": 0.20
    },

    "energy_weight_percent": 45,

    "water_weight_percent": 35,

    "environment_weight_percent": 20
}


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    print()
    print("=" * 70)
    print("LOADING PUBLIC BSEI DATASET")
    print("=" * 70)

    if not os.path.exists(DATASET_PATH):

        raise FileNotFoundError(
            f"\nDataset not found:\n{DATASET_PATH}"
        )


    df = pd.read_csv(
        DATASET_PATH
    )


    print()
    print("Dataset:")
    print(DATASET_PATH)

    print()
    print("Rows:", len(df))

    print(
        "Columns:",
        len(df.columns)
    )


    if len(df) == 0:

        raise ValueError(
            "Dataset contains zero records."
        )


    return df


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_data(df):

    print()
    print("=" * 70)
    print("PREPARING TRAINING DATA")
    print("=" * 70)


    missing_features = [

        column

        for column in FEATURES

        if column not in df.columns
    ]


    if missing_features:

        raise ValueError(
            "\nMissing feature columns:\n"
            +
            "\n".join(
                "- " + x
                for x in missing_features
            )
        )


    if TARGET not in df.columns:

        raise ValueError(
            f"Target column '{TARGET}' not found."
        )


    # --------------------------------------------------------
    # Select only required columns
    # --------------------------------------------------------

    data = df[
        FEATURES + [TARGET]
    ].copy()


    # --------------------------------------------------------
    # Convert numeric
    # --------------------------------------------------------

    for column in data.columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )


    # --------------------------------------------------------
    # Remove invalid records
    # --------------------------------------------------------

    before = len(data)

    data = data.replace(
        [np.inf, -np.inf],
        np.nan
    )


    data = data.dropna()


    after = len(data)


    print()
    print("Records before cleaning:", before)
    print("Records after cleaning:", after)
    print("Removed:", before - after)


    if after == 0:

        raise ValueError(
            "No valid records remain after cleaning."
        )


    X = data[FEATURES]

    y = data[TARGET]


    print()
    print("Training records:", len(X))
    print("Features:", len(FEATURES))


    print()
    print("Target statistics:")

    print(
        y.describe()
    )


    return X, y


# ============================================================
# TRAIN RANDOM FOREST
# ============================================================

def train_model(X, y):

    print()
    print("=" * 70)
    print("TRAINING RANDOM FOREST")
    print("=" * 70)


    if len(X) < 10:

        raise ValueError(
            "Not enough public records for training."
        )


    # --------------------------------------------------------
    # 80 / 20 split
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.20,

        random_state=42
    )


    print()
    print("Training samples:", len(X_train))
    print("Testing samples:", len(X_test))


    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    model = RandomForestRegressor(

        n_estimators=300,

        max_depth=12,

        min_samples_split=3,

        min_samples_leaf=1,

        max_features="sqrt",

        random_state=42,

        n_jobs=-1
    )


    model.fit(
        X_train,
        y_train
    )


    # --------------------------------------------------------
    # Test prediction
    # --------------------------------------------------------

    predictions = model.predict(
        X_test
    )


    mae = mean_absolute_error(
        y_test,
        predictions
    )


    mse = mean_squared_error(
        y_test,
        predictions
    )


    rmse = np.sqrt(
        mse
    )


    r2 = r2_score(
        y_test,
        predictions
    )


    # --------------------------------------------------------
    # Cross validation
    # --------------------------------------------------------

    n_splits = min(
        5,
        len(X)
    )


    kfold = KFold(

        n_splits=n_splits,

        shuffle=True,

        random_state=42
    )


    cv_scores = cross_val_score(

        model,

        X,

        y,

        cv=kfold,

        scoring="r2",

        n_jobs=-1
    )


    cv_mean = cv_scores.mean()

    cv_std = cv_scores.std()


    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    metrics = {

        "training_records": int(len(X)),

        "training_samples": int(len(X_train)),

        "testing_samples": int(len(X_test)),

        "features": int(len(FEATURES)),

        "MAE": float(mae),

        "MSE": float(mse),

        "RMSE": float(rmse),

        "R2": float(r2),

        "CV_R2_Mean": float(cv_mean),

        "CV_R2_Std": float(cv_std)
    }


    print()
    print("=" * 70)
    print("MODEL PERFORMANCE")
    print("=" * 70)

    print(
        f"MAE:       {mae:.4f}"
    )

    print(
        f"MSE:       {mse:.4f}"
    )

    print(
        f"RMSE:      {rmse:.4f}"
    )

    print(
        f"R²:        {r2:.4f}"
    )

    print(
        f"CV R²:     {cv_mean:.4f} ± {cv_std:.4f}"
    )


    return model, metrics


# ============================================================
# SAVE MODEL
# ============================================================

def save_model(model, metrics):

    print()
    print("=" * 70)
    print("SAVING TRAINED MODEL")
    print("=" * 70)


    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Save estimator directly
    # --------------------------------------------------------

    joblib.dump(
        model,
        MODEL_PATH
    )


    # --------------------------------------------------------
    # Save configuration separately
    # --------------------------------------------------------

    config = CONFIG.copy()

    config["metrics"] = metrics


    with open(
        CONFIG_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            config,
            file,
            indent=4
        )


    print()
    print("Model saved:")
    print(MODEL_PATH)

    print()
    print("Configuration saved:")
    print(CONFIG_PATH)


# ============================================================
# TEST SAVED MODEL
# ============================================================

def verify_model(model, X):

    print()
    print("=" * 70)
    print("VERIFYING SAVED MODEL")
    print("=" * 70)


    sample = X.iloc[
        [0]
    ]


    prediction = model.predict(
        sample
    )[0]


    print()
    print(
        "Sample predicted BSEI:",
        round(float(prediction), 2)
    )


    print()
    print("Model type:")

    print(
        type(model).__name__
    )


    if not hasattr(
        model,
        "predict"
    ):

        raise RuntimeError(
            "Saved model does not support predict()."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("UNICON PUBLIC BSEI RANDOM FOREST TRAINING")
    print("=" * 70)


    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_dataset()


    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    X, y = prepare_data(
        df
    )


    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    model, metrics = train_model(
        X,
        y
    )


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_model(
        model,
        metrics
    )


    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    verify_model(
        model,
        X
    )


    print()
    print("=" * 70)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print()
    print("Dataset: UNICON Public Dataset")
    print("Model: Random Forest Regressor")

    print()
    print("BSEI weights:")

    print("Energy:       45%")
    print("Water:        35%")
    print("Environment:  20%")

    print()
    print("Training records:", metrics["training_records"])

    print()
    print("Model file:")
    print(MODEL_PATH)

    print()
    print("DONE.")


if __name__ == "__main__":

    main()