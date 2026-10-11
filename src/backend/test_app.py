import json
import unittest
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch

import numpy as np
import pandas as pd

import app as backend


def sensor_rows(records):
    defaults = {
        "Timestamp": "2026-08-01",
        "Building_ID": "Academic",
        "Energy_Consumption_kWh": 500.0,
        "Water_Consumption_L": 1000.0,
        "Occupancy": 100.0,
        "Temperature_C": backend.TEMPERATURE_REFERENCE,
        "Humidity_Percent": backend.HUMIDITY_REFERENCE,
        "CO2_Level_ppm": 500.0,
        "BSEI": 70.0
    }
    return pd.DataFrame([
        {**defaults, **record}
        for record in records
    ])


class BuildingSummaryTests(unittest.TestCase):

    def test_preserves_preferred_order_and_discovers_buildings(self):
        data = sensor_rows([
            {"Building_ID": "Placement"},
            {"Building_ID": "library"},
            {"Building_ID": " Academic "},
            {"Building_ID": "Main"},
            {"Building_ID": "LIBRARY"},
            {"Building_ID": "Hostel"},
            {"Building_ID": "Atrium"}
        ])

        summaries = backend.get_building_summary(data)

        self.assertEqual(
            [item["Building_ID"] for item in summaries],
            ["Academic", "Main", "Hostel", "Placement", "Atrium", "library"]
        )
        library = summaries[5]
        self.assertEqual(library["Records"], 2)
        self.assertEqual(library["Energy_Consumption_kWh"], 500.0)
        self.assertIn("library", library["Recommendation"])

    def test_empty_missing_and_invalid_building_ids(self):
        self.assertEqual(backend.get_building_summary(pd.DataFrame()), [])
        self.assertEqual(
            backend.get_building_summary(pd.DataFrame({"Energy_Consumption_kWh": [1]})),
            []
        )
        data = sensor_rows([
            {"Building_ID": None},
            {"Building_ID": "   "},
            {"Building_ID": "nan"}
        ])
        self.assertEqual(backend.get_building_summary(data), [])

    def test_missing_and_nonnumeric_metrics_are_not_reported_as_zero(self):
        data = pd.DataFrame({
            "Building_ID": ["Library"],
            "Energy_Consumption_kWh": ["not-a-number"],
            "Water_Consumption_L": [None],
            "BSEI": ["invalid"]
        })

        summary = backend.get_building_summary(data)[0]
        self.assertIsNone(summary["Energy_Consumption_kWh"])
        self.assertIsNone(summary["Water_Consumption_L"])
        self.assertIsNone(summary["BSEI"])
        self.assertEqual(summary["Records"], 1)
        self.assertIn("Collect complete sensor readings", summary["Recommendation"])

    def test_current_bsei_formula_is_preserved(self):
        result = backend.calculate_bsei(800, 2000, 25, 60)
        relative_energy = 800 / backend.ENERGY_REFERENCE
        relative_water = 2000 / backend.WATER_REFERENCE
        energy_efficiency = 100 / (1 + relative_energy)
        water_efficiency = 100 / (1 + relative_water)
        temperature_deviation = (25 - backend.TEMPERATURE_REFERENCE) / backend.TEMPERATURE_STD
        humidity_deviation = (60 - backend.HUMIDITY_REFERENCE) / backend.HUMIDITY_STD
        environmental_deviation = np.sqrt(
            temperature_deviation ** 2 + humidity_deviation ** 2
        )
        environmental_efficiency = 100 / (1 + environmental_deviation)
        expected = (
            energy_efficiency * 0.45
            + water_efficiency * 0.35
            + environmental_efficiency * 0.20
        )
        self.assertAlmostEqual(result, expected)


class HistoricalTrendTests(unittest.TestCase):

    def test_daily_summary_excludes_bad_dates_and_sorts_chronologically(self):
        data = sensor_rows([
            {
                "Timestamp": "02-09-2026",
                "Energy_Consumption_kWh": 4,
                "Water_Consumption_L": 40
            },
            {"Timestamp": "invalid", "Energy_Consumption_kWh": 100},
            {
                "Timestamp": "02-08-2026",
                "Energy_Consumption_kWh": 2,
                "Water_Consumption_L": 20
            },
            {
                "Timestamp": "01-08-2026",
                "Energy_Consumption_kWh": 1,
                "Water_Consumption_L": 10
            }
        ])

        daily = backend.daily_campus_summary(data)

        self.assertEqual(
            [str(date) for date in daily["Date"]],
            ["2026-08-01", "2026-08-02", "2026-09-02"]
        )
        self.assertEqual(daily["Energy_Consumption_kWh"].tolist(), [1, 2, 4])

    def test_dashboard_csv_dates_are_day_first_and_not_fabricated(self):
        data = backend.load_sensor_data()

        self.assertEqual(len(data), 244)
        self.assertEqual(data["Timestamp"].min(), pd.Timestamp("2026-08-01"))
        self.assertEqual(data["Timestamp"].max(), pd.Timestamp("2026-09-30"))
        self.assertEqual(
            len(backend.daily_campus_summary(data)),
            61
        )


class AlertsAndRecommendationsTests(unittest.TestCase):

    def test_energy_above_old_reference_alone_does_not_create_alert(self):
        data = sensor_rows([{
            "Energy_Consumption_kWh": backend.ENERGY_REFERENCE + 1,
            "Water_Consumption_L": backend.WATER_REFERENCE + 1,
            "CO2_Level_ppm": 500
        }])
        with patch.object(backend, "load_sensor_data", return_value=data):
            response = backend.app.test_client().get("/api/predictive-analysis")

        self.assertEqual(response.status_code, 200)
        alerts = response.get_json()["attentionAreas"]
        self.assertEqual(alerts, [])

    def test_alerts_use_low_bsei_and_component_efficiency_comparisons(self):
        data = sensor_rows([
            {
                "Building_ID": "Academic",
                "Energy_Consumption_kWh": 5000,
                "BSEI": 40
            },
            {
                "Building_ID": "Main",
                "Energy_Consumption_kWh": 500,
                "BSEI": 80
            }
        ])
        with patch.object(backend, "load_sensor_data", return_value=data):
            response = backend.app.test_client().get("/api/predictive-analysis")

        self.assertEqual(response.status_code, 200)
        alerts = response.get_json()["attentionAreas"]
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert["affected"], "Academic")
        self.assertEqual(alert["component"], "energy")
        self.assertEqual(alert["metric"], "Energy component efficiency")
        self.assertEqual(alert["unit"], "% efficiency")
        self.assertEqual(alert["bsei"], 40.0)
        self.assertEqual(
            alert["value"],
            round(100 / (1 + 5000 / backend.ENERGY_REFERENCE), 2)
        )
        self.assertIn("below the campus building mean", alert["message"])
        self.assertIn("weighted BSEI gap", alert["message"])
        self.assertIn("operating schedules", alert["recommendation"])
        self.assertNotIn("reference", alert)
        self.assertNotIn("UNICON", str(alert))

    def test_environment_alert_uses_peer_efficiency_not_co2_threshold(self):
        data = sensor_rows([
            {
                "Building_ID": "Academic",
                "Temperature_C": 80,
                "Humidity_Percent": 100,
                "CO2_Level_ppm": 500,
                "BSEI": 70
            },
            {
                "Building_ID": "Main",
                "CO2_Level_ppm": 900,
                "BSEI": 70
            }
        ])
        with patch.object(backend, "load_sensor_data", return_value=data):
            response = backend.app.test_client().get("/api/predictive-analysis")

        self.assertEqual(response.status_code, 200)
        alerts = response.get_json()["attentionAreas"]
        environment = next(
            alert for alert in alerts if alert["affected"] == "Academic"
        )
        self.assertEqual(environment["component"], "environment")
        self.assertEqual(environment["metric"], "Environment component efficiency")
        self.assertLess(environment["value"], 100)
        self.assertIn("below the campus building mean", environment["message"])
        self.assertIn("temperature and humidity", environment["recommendation"])
        self.assertNotIn("900", str(alerts))
        self.assertNotIn("700 ppm", str(alerts))

    def test_water_alert_uses_measured_gap_and_consumption(self):
        data = sensor_rows([
            {
                "Building_ID": "Hostel",
                "Energy_Consumption_kWh": 5000,
                "Water_Consumption_L": 199395.04
            },
            {
                "Building_ID": "Main",
                "Energy_Consumption_kWh": 500,
                "Water_Consumption_L": 1000
            }
        ])
        with patch.object(backend, "load_sensor_data", return_value=data):
            response = backend.app.test_client().get("/api/predictive-analysis")

        self.assertEqual(response.status_code, 200)
        alerts = response.get_json()["attentionAreas"]
        hostel_alerts = [
            alert for alert in alerts
            if alert["affected"] == "Hostel"
        ]
        energy_alert = next(
            alert for alert in hostel_alerts
            if alert["component"] == "energy"
        )
        water_alert = next(
            alert for alert in hostel_alerts
            if alert["component"] == "water"
        )
        hostel_data = data[data["Building_ID"] == "Hostel"]
        expected_efficiency = backend.calculate_component_efficiencies(
            hostel_data
        )["water"]
        expected_gap = backend.calculate_weighted_bsei_gaps(
            hostel_data
        )["water"]

        self.assertEqual(energy_alert["title"], "Energy Monitoring Priority")
        self.assertEqual(
            water_alert["title"],
            "Water Efficiency Monitoring Priority"
        )
        self.assertEqual(water_alert["status"], "Monitor")
        self.assertEqual(water_alert["value"], round(expected_efficiency, 2))
        self.assertEqual(water_alert["weightedGap"], round(expected_gap, 2))
        self.assertEqual(water_alert["observedConsumption"], 199395.04)
        self.assertEqual(
            water_alert["consumptionUnit"],
            "L per sensor record"
        )
        self.assertIn(
            f"{expected_gap:.2f}-point weighted BSEI gap",
            water_alert["message"]
        )
        self.assertIn("Review water-use patterns", water_alert["recommendation"])
        self.assertIn("conservation opportunities", water_alert["recommendation"])
        self.assertNotIn("leak", water_alert["message"].lower())
        self.assertNotIn("UNICON", str(water_alert))
        self.assertNotIn("reference", str(water_alert).lower())

    def test_no_alerts_when_building_scores_match_the_campus(self):
        data = sensor_rows([
            {"Building_ID": "Academic"},
            {"Building_ID": "Main"}
        ])
        with patch.object(backend, "load_sensor_data", return_value=data):
            response = backend.app.test_client().get("/api/predictive-analysis")

        self.assertEqual(response.status_code, 200)
        alerts = response.get_json()["attentionAreas"]
        self.assertEqual(alerts, [])
        self.assertFalse(
            any(alert["component"] == "water" for alert in alerts)
        )

    def test_missing_or_nonnumeric_values_do_not_create_alerts(self):
        data = sensor_rows([{
            "Energy_Consumption_kWh": "invalid",
            "Water_Consumption_L": np.nan,
            "CO2_Level_ppm": None,
            "BSEI": "invalid"
        }])
        with patch.object(backend, "load_sensor_data", return_value=data):
            response = backend.app.test_client().get("/api/predictive-analysis")

        self.assertEqual(response.status_code, 200)
        alerts = response.get_json()["attentionAreas"]
        self.assertEqual(alerts, [])

    def test_recommendations_cover_low_medium_and_high_bsei(self):
        low = backend.generate_building_recommendation({
            "Building_ID": "Library",
            "BSEI": 30,
            "Energy_Consumption_kWh": 1800,
            "Water_Consumption_L": 1000,
            "Temperature_C": backend.TEMPERATURE_REFERENCE,
            "Humidity_Percent": backend.HUMIDITY_REFERENCE,
            "CO2_Level_ppm": 500
        })
        medium = backend.generate_building_recommendation({
            "Building_ID": "Hostel",
            "BSEI": 50,
            "Energy_Consumption_kWh": 100,
            "Water_Consumption_L": backend.WATER_REFERENCE * 2,
            "Temperature_C": backend.TEMPERATURE_REFERENCE,
            "Humidity_Percent": backend.HUMIDITY_REFERENCE,
            "CO2_Level_ppm": 500
        })
        high = backend.generate_building_recommendation({
            "Building_ID": "Main",
            "BSEI": 80,
            "Energy_Consumption_kWh": 100,
            "Water_Consumption_L": 100,
            "Temperature_C": 80,
            "Humidity_Percent": 100,
            "CO2_Level_ppm": 701
        })
        incomplete = backend.generate_building_recommendation({
            "Building_ID": "Placement",
            "BSEI": 30,
            "Energy_Consumption_kWh": 1800,
            "Water_Consumption_L": 1000
        })

        self.assertIn("Library", low)
        self.assertIn("conservation opportunities", medium)
        self.assertIn("Hostel", medium)
        self.assertIn("Review temperature, humidity, and CO2 conditions", high)
        self.assertIn("701.00 ppm", high)
        self.assertIn("complete energy, water", incomplete)
        self.assertIn("1800.00 kWh per sensor record", low)
        self.assertIn("670928.48 L per sensor record", medium)
        self.assertIn("BSEI is 30.00", low)
        self.assertIn("efficiency and a", low)
        self.assertIn("Also monitor", low)
        self.assertNotIn("UNICON", low)
        self.assertNotIn("reference", low.lower())
        self.assertNotIn("unnecessary", low.lower())

    def test_weighted_bsei_gaps_match_the_existing_formula(self):
        data = sensor_rows([
            {
                "Energy_Consumption_kWh": 700,
                "Water_Consumption_L": 2000,
                "Temperature_C": 24,
                "Humidity_Percent": 55
            },
            {
                "Energy_Consumption_kWh": 1300,
                "Water_Consumption_L": 8000,
                "Temperature_C": 26,
                "Humidity_Percent": 65
            }
        ])
        data["BSEI"] = data.apply(
            backend.calculate_bsei_from_row,
            axis=1
        )

        gaps = backend.calculate_weighted_bsei_gaps(data)

        self.assertEqual(set(gaps), {"energy", "water", "environment"})
        self.assertAlmostEqual(
            sum(gaps.values()),
            100 - data["BSEI"].mean()
        )

    def test_recommendation_selection_follows_largest_calculated_gap(self):
        cases = [
            (
                "energy",
                {
                    "Energy_Consumption_kWh": 5000,
                    "Water_Consumption_L": 1000,
                    "Temperature_C": backend.TEMPERATURE_REFERENCE,
                    "Humidity_Percent": backend.HUMIDITY_REFERENCE
                },
                "high-load consumption"
            ),
            (
                "water",
                {
                    "Energy_Consumption_kWh": 100,
                    "Water_Consumption_L": 800000,
                    "Temperature_C": backend.TEMPERATURE_REFERENCE,
                    "Humidity_Percent": backend.HUMIDITY_REFERENCE
                },
                "conservation opportunities"
            ),
            (
                "environment",
                {
                    "Energy_Consumption_kWh": 100,
                    "Water_Consumption_L": 100,
                    "Temperature_C": 80,
                    "Humidity_Percent": 100
                },
                "Review temperature, humidity, and CO2 conditions"
            )
        ]

        for expected_component, metrics, expected_action in cases:
            with self.subTest(component=expected_component):
                gaps = backend.calculate_weighted_bsei_gaps(
                    pd.DataFrame([metrics])
                )
                component, gap = backend.select_weighted_bsei_gap(gaps)
                self.assertEqual(component, expected_component)
                self.assertEqual(gap, gaps[expected_component])
                summary = {
                    "Building_ID": "Test Building",
                    "BSEI": backend.calculate_bsei(
                        metrics["Energy_Consumption_kWh"],
                        metrics["Water_Consumption_L"],
                        metrics["Temperature_C"],
                        metrics["Humidity_Percent"]
                    ),
                    "CO2_Level_ppm": 500,
                    **metrics
                }
                recommendation = backend.generate_building_recommendation(
                    summary,
                    gaps
                )
                self.assertIn(expected_action, recommendation)

    def test_building_recommendations_reflect_different_measured_energy(self):
        data = sensor_rows([
            {
                "Building_ID": "Academic",
                "Energy_Consumption_kWh": 2700
            },
            {
                "Building_ID": "Main",
                "Energy_Consumption_kWh": 2300
            }
        ])
        data["BSEI"] = data.apply(
            backend.calculate_bsei_from_row,
            axis=1
        )

        summaries = backend.get_building_summary(data)
        academic, main = summaries

        self.assertIn("2700.00 kWh per sensor record", academic["Recommendation"])
        self.assertIn("2300.00 kWh per sensor record", main["Recommendation"])
        self.assertEqual(academic["Recommendation_Component"], "energy")
        self.assertEqual(main["Recommendation_Component"], "energy")
        self.assertGreater(academic["Recommendation_Gap"], 0)
        self.assertGreater(main["Recommendation_Gap"], 0)
        self.assertNotEqual(
            academic["Recommendation"],
            main["Recommendation"]
        )

    def test_environment_recommendation_uses_measured_temperature_and_humidity(self):
        bsei = backend.calculate_bsei(
            0,
            0,
            50,
            100
        )
        recommendation = backend.generate_building_recommendation({
            "Building_ID": "Library",
            "BSEI": bsei,
            "Energy_Consumption_kWh": 0,
            "Water_Consumption_L": 0,
            "Temperature_C": 50,
            "Humidity_Percent": 100,
            "CO2_Level_ppm": 500
        })

        self.assertIn("Mean conditions in Library", recommendation)
        self.assertIn("50.00 °C", recommendation)
        self.assertIn("100.00% humidity", recommendation)

    def test_checked_in_data_priorities_use_scores_without_reference_text(self):
        data = backend.load_sensor_data()
        with patch.object(backend, "load_sensor_data", return_value=data):
            response = backend.app.test_client().get("/api/predictive-analysis")

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        hostel_water_alert = next(
            alert for alert in result["attentionAreas"]
            if alert["affected"] == "Hostel"
            and alert["component"] == "water"
        )
        self.assertEqual(hostel_water_alert["value"], 62.79)
        self.assertEqual(hostel_water_alert["weightedGap"], 13.02)
        self.assertEqual(
            hostel_water_alert["observedConsumption"],
            199395.04
        )
        for alert in result["attentionAreas"]:
            self.assertIn(alert["component"], {"energy", "water", "environment"})
            self.assertIsNotNone(alert["bsei"])
            self.assertIsNotNone(alert["value"])
            self.assertIsNotNone(alert["weightedGap"])
            self.assertNotIn("UNICON", str(alert))
            self.assertNotIn("reference", str(alert).lower())

        for building in result["buildingRecommendations"]:
            gaps = building["Recommendation_Gaps"]
            largest_component = max(gaps, key=gaps.get)
            self.assertEqual(
                building["Recommendation_Component"],
                largest_component
            )
            self.assertEqual(
                building["Recommendation_Gap"],
                gaps[largest_component]
            )
            self.assertTrue(building["Recommendation_Efficiencies"])
            self.assertIn(
                f"{building['BSEI']:.2f}",
                building["Recommendation"]
            )
            self.assertNotIn("UNICON", building["Recommendation"])
            self.assertNotIn("reference", building["Recommendation"].lower())

        recommendations = {
            building["Building_ID"]: building["Recommendation"]
            for building in result["buildingRecommendations"]
        }
        self.assertEqual(
            result["buildingRecommendations"][0]["Recommendation_Component"],
            "energy"
        )
        self.assertAlmostEqual(
            result["buildingRecommendations"][0]["Recommendation_Gap"],
            34.52,
            places=1
        )
        academic_gaps = result["buildingRecommendations"][0]["Recommendation_Gaps"]
        self.assertEqual(
            set(academic_gaps),
            {"energy", "water", "environment"}
        )
        self.assertGreater(academic_gaps["energy"], academic_gaps["water"])
        self.assertGreater(
            academic_gaps["energy"],
            academic_gaps["environment"]
        )
        self.assertIn("2710.89 kWh per sensor record", recommendations["Academic"])
        self.assertIn("2306.34 kWh per sensor record", recommendations["Main"])
        self.assertNotEqual(
            recommendations["Academic"],
            recommendations["Main"]
        )


class ApiContractTests(unittest.TestCase):

    def test_aws_data_route_returns_latest_s3_records_and_skips_bad_json(self):
        older = datetime(2026, 10, 7, 17, 0, tzinfo=timezone.utc)
        newer = datetime(2026, 10, 7, 17, 19, tzinfo=timezone.utc)

        class FakePaginator:
            def paginate(self, **kwargs):
                self.kwargs = kwargs
                return [{
                    "Contents": [
                        {
                            "Key": "processed-data/older.json",
                            "LastModified": older
                        },
                        {
                            "Key": "processed-data/newer.json",
                            "LastModified": newer
                        },
                        {
                            "Key": "processed-data/malformed.json",
                            "LastModified": newer
                        },
                        {
                            "Key": "processed-data/ignored.txt",
                            "LastModified": newer
                        }
                    ]
                }]

        class FakeS3:
            def __init__(self):
                self.paginator = FakePaginator()

            def get_paginator(self, name):
                self.asserted_paginator = name
                return self.paginator

            def get_object(self, Bucket, Key):
                bodies = {
                    "processed-data/older.json": b'{"Building_ID":"Main"}',
                    "processed-data/newer.json": (
                        b'{"Building_ID":"Hostel","BSEI":51.82}'
                    ),
                    "processed-data/malformed.json": b"{not-json"
                }
                return {"Body": BytesIO(bodies[Key])}

        s3 = FakeS3()
        with patch.object(backend.boto3, "client", return_value=s3) as client:
            response = backend.app.test_client().get("/api/aws-data")

        self.assertEqual(response.status_code, 200)
        client.assert_called_once_with("s3", region_name="us-east-1")
        self.assertEqual(s3.paginator.kwargs, {
            "Bucket": "digital-twin-campus-2026-preetham",
            "Prefix": "processed-data/"
        })
        result = response.get_json()
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["malformedRecords"], 1)
        self.assertEqual(
            [record["Building_ID"] for record in result["records"]],
            ["Hostel", "Main"]
        )
        self.assertEqual(
            result["records"][0]["s3Key"],
            "processed-data/newer.json"
        )
        self.assertEqual(result["region"], "us-east-1")

    def test_aws_data_route_returns_empty_state_when_prefix_is_empty(self):
        class FakePaginator:
            def paginate(self, **kwargs):
                return [{"Contents": []}]

        class FakeS3:
            def get_paginator(self, name):
                return FakePaginator()

        with patch.object(backend.boto3, "client", return_value=FakeS3()):
            response = backend.app.test_client().get("/api/aws-data")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["records"], [])
        self.assertEqual(response.get_json()["count"], 0)

    def test_aws_data_route_reports_missing_credentials(self):
        with patch.object(
            backend.boto3,
            "client",
            side_effect=backend.NoCredentialsError()
        ):
            response = backend.app.test_client().get("/api/aws-data")

        self.assertEqual(response.status_code, 503)
        self.assertIn("AWS credentials", response.get_json()["error"])

    def test_aws_history_route_applies_limit_and_reports_truncation(self):
        object_times = [
            datetime(2026, 10, day, tzinfo=timezone.utc)
            for day in (1, 2, 3)
        ]

        class FakePaginator:
            def paginate(self, **kwargs):
                return [{
                    "Contents": [
                        {
                            "Key": f"processed-data/record-{index}.json",
                            "LastModified": modified
                        }
                        for index, modified in enumerate(object_times)
                    ]
                }]

        class FakeS3:
            def get_paginator(self, name):
                return FakePaginator()

            def get_object(self, Bucket, Key):
                index = int(Key.rsplit("-", 1)[1].split(".", 1)[0])
                body = json.dumps({
                    "Building_ID": "Academic",
                    "timestamp": f"2026-10-0{index + 1}T00:00:00+00:00"
                }).encode()
                return {"Body": BytesIO(body)}

        with patch.object(backend.boto3, "client", return_value=FakeS3()):
            response = backend.app.test_client().get(
                "/api/aws-data/history?limit=2"
            )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["limit"], 2)
        self.assertTrue(result["hasMore"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(
            [record["timestamp"] for record in result["records"]],
            [
                "2026-10-02T00:00:00+00:00",
                "2026-10-03T00:00:00+00:00"
            ]
        )

    def test_aws_history_route_returns_empty_history(self):
        class FakePaginator:
            def paginate(self, **kwargs):
                return [{"Contents": []}]

        class FakeS3:
            def get_paginator(self, name):
                return FakePaginator()

        with patch.object(backend.boto3, "client", return_value=FakeS3()):
            response = backend.app.test_client().get(
                "/api/aws-data/history"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["records"], [])
        self.assertEqual(response.get_json()["count"], 0)
        self.assertFalse(response.get_json()["hasMore"])

    def test_aws_history_route_reports_expired_credentials(self):
        expired_token = backend.ClientError(
            {
                "Error": {
                    "Code": "ExpiredToken",
                    "Message": "The provided token has expired."
                },
                "ResponseMetadata": {
                    "RequestId": "test-expired-request"
                }
            },
            "ListObjectsV2"
        )

        with patch.object(
            backend.boto3,
            "client",
            side_effect=expired_token
        ):
            with self.assertLogs(backend.app.logger, level="ERROR") as logs:
                response = backend.app.test_client().get(
                    "/api/aws-data/history"
                )

        result = response.get_json()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(result["awsErrorCode"], "ExpiredToken")
        self.assertEqual(result["requestId"], "test-expired-request")
        self.assertIn("credentials have expired", result["error"])
        self.assertIn("ExpiredToken", "\n".join(logs.output))

    def test_aws_history_route_reports_s3_access_denied(self):
        access_denied = backend.ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "Access Denied"
                },
                "ResponseMetadata": {
                    "RequestId": "test-denied-request"
                }
            },
            "ListObjectsV2"
        )

        with patch.object(
            backend.boto3,
            "client",
            side_effect=access_denied
        ):
            response = backend.app.test_client().get(
                "/api/aws-data/history"
            )

        result = response.get_json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(result["awsErrorCode"], "AccessDenied")
        self.assertEqual(result["requestId"], "test-denied-request")
        self.assertIn("s3:ListBucket", result["error"])

    def test_aws_history_route_rejects_invalid_limits(self):
        with patch.object(backend.boto3, "client") as client:
            response = backend.app.test_client().get(
                "/api/aws-data/history?limit=not-a-number"
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("limit must be an integer", response.get_json()["error"])
        client.assert_not_called()

    def test_dashboard_routes_keep_contracts_with_valid_data(self):
        data = sensor_rows([
            {"Building_ID": "Academic"},
            {"Building_ID": "Library"}
        ])
        client = backend.app.test_client()

        with patch.object(backend, "load_sensor_data", return_value=data):
            analytics = client.get("/api/analytics")
            sustainability = client.get("/api/sustainability")
            energy_trend = client.get("/api/energy-trend")
            predictive = client.get("/api/predictive-analysis")

        self.assertEqual(analytics.status_code, 200)
        self.assertEqual(analytics.get_json()["energyConsumption"], 1000.0)
        self.assertEqual(analytics.get_json()["records"], 2)
        self.assertEqual(sustainability.status_code, 200)
        self.assertEqual(len(sustainability.get_json()["buildings"]), 2)
        self.assertEqual(energy_trend.status_code, 200)
        self.assertEqual(energy_trend.get_json()[0]["date"], "2026-08-01")
        self.assertEqual(predictive.status_code, 200)
        self.assertEqual(
            [row["Building_ID"] for row in predictive.get_json()["buildingPerformance"]],
            ["Academic", "Library"]
        )
        self.assertEqual(
            len(predictive.get_json()["buildingRecommendations"]),
            2
        )

    def test_health_model_info_and_prediction_routes(self):
        client = backend.app.test_client()
        self.assertEqual(client.get("/api/health").status_code, 200)
        self.assertEqual(client.get("/api/model-info").status_code, 200)

        class FakeModel:
            def predict(self, model_input):
                self.asserted_features = list(model_input.columns)
                return [70]

        with patch.object(backend, "PUBLIC_MODEL", FakeModel()):
            response = client.post(
                "/api/predict",
                json={
                    "energy_consumption_kWh": 500,
                    "water_consumption_L": 1000,
                    "air_temperature": 25,
                    "relative_humidity": 60
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("predictedBSEI", response.get_json())
        self.assertEqual(response.get_json()["model"], "Random Forest Regressor")


if __name__ == "__main__":
    unittest.main()
