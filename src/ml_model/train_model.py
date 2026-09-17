import pandas as pd
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# Dataset path
DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../dataset/combined_sensor_data.csv"
)

# Load dataset
df = pd.read_csv(DATA_PATH)

print("Dataset loaded successfully")
print("Total records:", len(df))


# Features used for prediction
features = [
    "Energy_Consumption_kWh",
    "Water_Consumption_L",
    "Temperature_C",
    "Humidity_Percent",
    "CO2_Level_ppm",
    "Occupancy"
]

target = "Sustainability_Score"


# Input and output
X = df[features]
y = df[target]


# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


print("Training records:", len(X_train))
print("Testing records:", len(X_test))


# Create ML model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)


# Train model
model.fit(X_train, y_train)

print("Model training completed")


# Predictions
y_pred = model.predict(X_test)


# Evaluation
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)


print("\nModel Performance:")
print("MAE:", round(mae, 2))
print("MSE:", round(mse, 2))
print("R2 Score:", round(r2, 2))


# Save trained model
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "sustainability_model.pkl"
)

joblib.dump(model, MODEL_PATH)

print("\nModel saved successfully:")
print(MODEL_PATH)