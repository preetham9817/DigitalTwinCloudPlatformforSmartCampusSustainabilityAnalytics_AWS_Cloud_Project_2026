import json
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")

BUCKET_NAME = "digital-twin-campus-2026-preetham"
PROCESSED_PREFIX = "processed-data/"

# BSEI weights
ENERGY_WEIGHT = 0.45
WATER_WEIGHT = 0.35
ENVIRONMENT_WEIGHT = 0.20

# UNICON reference values
ENERGY_REFERENCE = 772.8378
WATER_REFERENCE = 335464.242
TEMPERATURE_REFERENCE = 17.5706
HUMIDITY_REFERENCE = 71.0625
TEMPERATURE_STD = 4.9704
HUMIDITY_STD = 12.2897


def calculate_bsei(energy, water, temperature, humidity):
    relative_energy = energy / ENERGY_REFERENCE
    relative_water = water / WATER_REFERENCE

    energy_efficiency = 100 / (1 + relative_energy)
    water_efficiency = 100 / (1 + relative_water)

    temperature_deviation = abs(
        temperature - TEMPERATURE_REFERENCE
    ) / TEMPERATURE_STD

    humidity_deviation = abs(
        humidity - HUMIDITY_REFERENCE
    ) / HUMIDITY_STD

    environmental_deviation = (
        temperature_deviation + humidity_deviation
    ) / 2

    environmental_efficiency = (
        100 / (1 + environmental_deviation)
    )

    bsei = (
        energy_efficiency * ENERGY_WEIGHT
        + water_efficiency * WATER_WEIGHT
        + environmental_efficiency * ENVIRONMENT_WEIGHT
    )

    return {
        "bsei": round(max(0, min(100, bsei)), 2),
        "energy_efficiency": round(energy_efficiency, 2),
        "water_efficiency": round(water_efficiency, 2),
        "environmental_efficiency": round(
            environmental_efficiency, 2
        )
    }


def lambda_handler(event, context):

    print("Received sensor event:")
    print(json.dumps(event))

    try:
        # Support both direct JSON and IoT message formats
        if isinstance(event, str):
            event = json.loads(event)

        # Extract sensor values
        building_id = event.get(
            "Building_ID",
            event.get("building_id", "Unknown")
        )

        energy = float(event.get(
            "Energy_Consumption_kWh",
            event.get("energy_consumption_kWh", 0)
        ))

        water = float(event.get(
            "Water_Consumption_L",
            event.get("water_consumption_L", 0)
        ))

        occupancy = float(event.get(
            "Occupancy",
            event.get("occupancy", 0)
        ))

        temperature = float(event.get(
            "Temperature_C",
            event.get("temperature_C", 0)
        ))

        humidity = float(event.get(
            "Humidity_Percent",
            event.get("humidity_percent", 0)
        ))

        co2 = float(event.get(
            "CO2_Level_ppm",
            event.get("co2_level_ppm", 0)
        ))

        # Calculate BSEI
        bsei_result = calculate_bsei(
            energy,
            water,
            temperature,
            humidity
        )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        # Processed result
        processed_data = {
            "timestamp": timestamp,
            "Building_ID": building_id,
            "Energy_Consumption_kWh": energy,
            "Water_Consumption_L": water,
            "Occupancy": occupancy,
            "Temperature_C": temperature,
            "Humidity_Percent": humidity,
            "CO2_Level_ppm": co2,

            "BSEI": bsei_result["bsei"],

            "BSEI_Components": {
                "Energy_Efficiency": bsei_result[
                    "energy_efficiency"
                ],
                "Water_Efficiency": bsei_result[
                    "water_efficiency"
                ],
                "Environmental_Efficiency": bsei_result[
                    "environmental_efficiency"
                ]
            },

            "BSEI_Weights": {
                "Energy": ENERGY_WEIGHT,
                "Water": WATER_WEIGHT,
                "Environment": ENVIRONMENT_WEIGHT
            }
        }

        # Unique S3 object name
        safe_building = str(building_id).replace(
            " ",
            "_"
        )

        file_name = (
            f"{PROCESSED_PREFIX}"
            f"{safe_building}_"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}.json"
        )

        # Save processed data to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=json.dumps(processed_data),
            ContentType="application/json"
        )

        print("BSEI calculation completed:")
        print(json.dumps(processed_data))

        print(
            f"Processed data saved to "
            f"s3://{BUCKET_NAME}/{file_name}"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Sensor data processed successfully",
                "BSEI": bsei_result["bsei"],
                "Building_ID": building_id,
                "s3_key": file_name
            })
        }

    except Exception as e:

        print("ERROR:")
        print(str(e))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }