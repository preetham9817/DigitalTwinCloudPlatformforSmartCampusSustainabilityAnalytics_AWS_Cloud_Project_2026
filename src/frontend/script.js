const API_URL = "http://127.0.0.1:5000";

/* =========================
   LOAD DASHBOARD DATA
========================= */

async function loadDashboard() {

    try {

        const response = await fetch(`${API_URL}/api/analytics`);

        const data = await response.json();

        document.getElementById("energy").textContent =
            data.average_energy;

        document.getElementById("water").textContent =
            data.average_water;

        document.getElementById("occupancy").textContent =
            data.average_occupancy;

        document.getElementById("sustainability").textContent =
            data.average_sustainability_score;

        document.getElementById("temperature").textContent =
            data.average_temperature;

        document.getElementById("humidity").textContent =
            data.average_humidity;

        document.getElementById("co2").textContent =
            data.average_co2;

        document.getElementById("records").textContent =
            data.total_records;

        loadBuildingScores();

    } catch (error) {

        console.error("Error loading dashboard:", error);

    }
}


/* =========================
   BUILDING SUSTAINABILITY
========================= */

async function loadBuildingScores() {

    try {

        const response =
            await fetch(`${API_URL}/api/sustainability`);

        const data = await response.json();

        const container =
            document.getElementById("buildingScores");

        container.innerHTML = "";

        const scores = data.sustainability_scores;

        for (const building in scores) {

            const score = scores[building];

            const item = document.createElement("div");

            item.className = "building-item";

            item.innerHTML = `
                <div class="building-header">

                    <span class="building-name">
                        ${building}
                    </span>

                    <span class="building-score">
                        ${score}
                    </span>

                </div>

                <div class="progress">

                    <div
                        class="progress-bar"
                        style="width: ${score}%">
                    </div>

                </div>
            `;

            container.appendChild(item);
        }

    } catch (error) {

        console.error(
            "Error loading building data:",
            error
        );

    }
}


/* =========================
   ENERGY CHART
========================= */

async function loadEnergyChart() {

    try {

        const response =
            await fetch(`${API_URL}/api/sensor-data`);

        const data = await response.json();

        const selectedData = data.slice(0, 20);

        const labels = selectedData.map(
            item => item.Timestamp
        );

        const energyValues = selectedData.map(
            item => item.Energy_Consumption_kWh
        );

        const ctx =
            document.getElementById("energyChart");

        if (!ctx) return;

        new Chart(ctx, {

            type: "line",

            data: {

                labels: labels,

                datasets: [{

                    label: "Energy Consumption",

                    data: energyValues,

                    borderColor: "#4f9cff",

                    backgroundColor:
                        "rgba(79, 156, 255, 0.08)",

                    borderWidth: 2,

                    fill: true,

                    tension: 0.35,

                    pointRadius: 2,

                    pointHoverRadius: 5

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    x: {

                        grid: {
                            display: false
                        },

                        ticks: {
                            color: "#718096",
                            maxTicksLimit: 6
                        }

                    },

                    y: {

                        grid: {
                            color:
                                "rgba(255,255,255,0.05)"
                        },

                        ticks: {
                            color: "#718096"
                        }

                    }

                }

            }

        });

    } catch (error) {

        console.error(
            "Error loading energy chart:",
            error
        );

    }
}


/* =========================
   ML PREDICTION
========================= */

async function predictScore() {

    const energy =
        document.getElementById("p_energy").value;

    const water =
        document.getElementById("p_water").value;

    const temperature =
        document.getElementById("p_temperature").value;

    const humidity =
        document.getElementById("p_humidity").value;

    const co2 =
        document.getElementById("p_co2").value;

    const occupancy =
        document.getElementById("p_occupancy").value;


    const result =
        document.getElementById("predictionResult");

    result.textContent = "Calculating prediction...";


    try {

        const response = await fetch(
            `${API_URL}/api/predict`,
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    Energy_Consumption_kWh:
                        Number(energy),

                    Water_Consumption_L:
                        Number(water),

                    Temperature_C:
                        Number(temperature),

                    Humidity_Percent:
                        Number(humidity),

                    CO2_Level_ppm:
                        Number(co2),

                    Occupancy:
                        Number(occupancy)

                })

            }
        );


        const data = await response.json();


        if (data.predicted_sustainability_score !== undefined) {

            result.innerHTML = `
                Predicted Sustainability Score:
                <strong>
                    ${data.predicted_sustainability_score}
                </strong>
            `;

        } else {

            result.textContent =
                "Prediction failed.";

        }

    } catch (error) {

        console.error(
            "Prediction error:",
            error
        );

        result.textContent =
            "Unable to connect to backend.";

    }
}


/* =========================
   START DASHBOARD
========================= */

loadDashboard();

loadEnergyChart();