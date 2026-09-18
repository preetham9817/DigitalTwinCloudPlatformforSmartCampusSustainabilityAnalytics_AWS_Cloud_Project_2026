const API_URL = "http://127.0.0.1:5000";

let energyChart = null;


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    try {

        const response =
            await fetch(`${API_URL}/api/analytics`);

        const data =
            await response.json();


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

    }

    catch (error) {

        console.error(
            "Error loading dashboard:",
            error
        );

    }

}


// ============================================================
// BUILDING SUSTAINABILITY
// ============================================================

async function loadBuildingScores() {

    try {

        const response =
            await fetch(
                `${API_URL}/api/sustainability`
            );

        const data =
            await response.json();


        const container =
            document.getElementById(
                "buildingScores"
            );


        container.innerHTML = "";


        const scores =
            data.sustainability_scores;


        for (
            const building in scores
        ) {

            const score =
                scores[building];


            const item =
                document.createElement("div");


            item.className =
                "building-item";


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
                        style="width: ${score}%"
                    ></div>

                </div>

            `;


            container.appendChild(item);

        }

    }

    catch (error) {

        console.error(
            "Error loading building data:",
            error
        );

    }

}


// ============================================================
// ENERGY CHART
// ============================================================

async function loadEnergyChart() {

    try {

        const response =
            await fetch(
                `${API_URL}/api/sensor-data`
            );


        const data =
            await response.json();


        const selectedData =
            data.slice(0, 20);


        const labels =
            selectedData.map(
                item => item.Timestamp
            );


        const energyValues =
            selectedData.map(
                item =>
                    item.Energy_Consumption_kWh
            );


        const ctx =
            document.getElementById(
                "energyChart"
            );


        if (!ctx) {
            return;
        }


        if (energyChart) {

            energyChart.destroy();

        }


        energyChart =
            new Chart(
                ctx,
                {

                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                label:
                                    "Energy Consumption",

                                data:
                                    energyValues,

                                borderColor:
                                    "#4f9cff",

                                backgroundColor:
                                    "rgba(79, 156, 255, 0.08)",

                                borderWidth:
                                    2,

                                fill:
                                    true,

                                tension:
                                    0.35,

                                pointRadius:
                                    2,

                                pointHoverRadius:
                                    5

                            }

                        ]

                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        plugins: {

                            legend: {

                                display:
                                    false

                            }

                        },

                        scales: {

                            x: {

                                grid: {
                                    display: false
                                },

                                ticks: {

                                    color:
                                        "#718096",

                                    maxTicksLimit:
                                        6

                                }

                            },

                            y: {

                                grid: {

                                    color:
                                        "rgba(255,255,255,0.05)"

                                },

                                ticks: {

                                    color:
                                        "#718096"

                                }

                            }

                        }

                    }

                }
            );

    }

    catch (error) {

        console.error(
            "Error loading energy chart:",
            error
        );

    }

}


// ============================================================
// PREDICTIVE ANALYSIS
// ============================================================

async function loadPredictiveAnalysis() {

    try {

        const response =
            await fetch(
                `${API_URL}/api/predictive-analysis`
            );


        const data =
            await response.json();


        renderAttentionAreas(
            data.attention_areas
        );


        renderPredictiveBuildings(
            data.building_analysis
        );


        renderTrends(
            data.trend_analysis
        );


        renderFeatureImportance(
            data.feature_importance
        );


        renderImprovementAreas(
            data.improvement_areas
        );


        renderBuildingRecommendations(
            data.building_recommendations
        );

    }

    catch (error) {

        console.error(
            "Predictive analysis error:",
            error
        );


        showPredictiveError();

    }

}


// ============================================================
// ATTENTION AREAS
// ============================================================

function renderAttentionAreas(
    areas
) {

    const container =
        document.getElementById(
            "attentionAreas"
        );


    container.innerHTML = "";


    if (
        !areas ||
        areas.length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">

                No major attention areas
                detected from the current dataset.

            </div>

        `;

        return;

    }


    areas.forEach(
        area => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "attention-card";


            let icon =
                "⚠";


            if (
                area.area.includes(
                    "Energy"
                )
            ) {

                icon = "⚡";

            }

            else if (
                area.area.includes(
                    "Water"
                )
            ) {

                icon = "💧";

            }

            else if (
                area.area.includes(
                    "CO"
                )
            ) {

                icon = "🌫";

            }

            else if (
                area.area.includes(
                    "Sustainability"
                )
            ) {

                icon = "🌱";

            }


            card.innerHTML = `

                <div class="attention-icon">

                    ${icon}

                </div>


                <div class="attention-content">

                    <div class="attention-title-row">

                        <h4>
                            ${area.area}
                        </h4>

                        <span
                            class="severity ${getSeverityClass(area.severity)}"
                        >
                            ${area.severity}
                        </span>

                    </div>


                    <p>
                        ${area.description}
                    </p>


                    <div class="recommendation-text">

                        <strong>
                            Suggested action:
                        </strong>

                        ${area.recommendation}

                    </div>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}


// ============================================================
// SEVERITY CLASS
// ============================================================

function getSeverityClass(
    severity
) {

    if (!severity) {

        return "severity-monitor";

    }


    const value =
        severity.toLowerCase();


    if (
        value === "high"
    ) {

        return "severity-high";

    }


    if (
        value === "attention"
    ) {

        return "severity-attention";

    }


    return "severity-monitor";

}


// ============================================================
// BUILDING PREDICTIVE ANALYSIS
// ============================================================

function renderPredictiveBuildings(
    buildings
) {

    const container =
        document.getElementById(
            "predictiveBuildings"
        );


    container.innerHTML = "";


    if (
        !buildings ||
        buildings.length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">
                No building analysis available.
            </div>

        `;

        return;

    }


    buildings.forEach(
        building => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "predictive-building";


            const score =
                Number(
                    building.sustainability_score
                );


            let scoreClass =
                "score-good";


            if (
                score < 70
            ) {

                scoreClass =
                    "score-low";

            }

            else if (
                score < 80
            ) {

                scoreClass =
                    "score-medium";

            }


            const difference =
                Number(
                    building.score_difference
                );


            const differenceText =
                difference >= 0
                    ? `+${difference.toFixed(2)}`
                    : difference.toFixed(2);


            const differenceClass =
                difference >= 0
                    ? "difference-positive"
                    : "difference-negative";


            card.innerHTML = `

                <div class="predictive-building-header">

                    <div>

                        <h4>
                            ${building.building}
                        </h4>

                        <span>
                            Sustainability Score
                        </span>

                    </div>


                    <strong
                        class="${scoreClass}"
                    >
                        ${score.toFixed(2)}
                    </strong>

                </div>


                <div class="building-score-track">

                    <div
                        class="building-score-fill"
                        style="width: ${Math.min(score, 100)}%"
                    ></div>

                </div>


                <div class="building-metrics">

                    <div>

                        <span>
                            Energy
                        </span>

                        <strong>
                            ${building.energy}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Water
                        </span>

                        <strong>
                            ${building.water}
                        </strong>

                    </div>


                    <div>

                        <span>
                            CO₂
                        </span>

                        <strong>
                            ${building.co2}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Campus Difference
                        </span>

                        <strong
                            class="${differenceClass}"
                        >
                            ${differenceText}
                        </strong>

                    </div>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}


// ============================================================
// TREND ANALYSIS
// ============================================================

function renderTrends(
    trends
) {

    const container =
        document.getElementById(
            "trendAnalysis"
        );


    container.innerHTML = "";


    if (
        !trends ||
        Object.keys(trends).length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">

                Historical trend data
                is not available.

            </div>

        `;

        return;

    }


    const labels = {

        energy:
            "Energy",

        water:
            "Water",

        co2:
            "CO₂",

        sustainability:
            "Sustainability"

    };


    const icons = {

        energy:
            "⚡",

        water:
            "💧",

        co2:
            "🌫",

        sustainability:
            "🌱"

    };


    for (
        const key in trends
    ) {

        const item =
            trends[key];


        const card =
            document.createElement(
                "div"
            );


        card.className =
            "trend-card";


        const percentage =
            Number(
                item.percentage_change
            );


        let directionClass =
            "trend-stable";


        let arrow =
            "→";


        if (
            item.direction ===
            "Increasing"
        ) {

            directionClass =
                "trend-increasing";

            arrow =
                "↗";

        }

        else if (
            item.direction ===
            "Decreasing"
        ) {

            directionClass =
                "trend-decreasing";

            arrow =
                "↘";

        }


        card.innerHTML = `

            <div class="trend-icon">

                ${icons[key] || "•"}

            </div>


            <div class="trend-info">

                <span>
                    ${labels[key] || key}
                </span>

                <strong
                    class="${directionClass}"
                >
                    ${arrow}
                    ${item.direction}
                </strong>

                <small>

                    ${percentage >= 0 ? "+" : ""}
                    ${percentage.toFixed(2)}%

                    historical change

                </small>

            </div>

        `;


        container.appendChild(
            card
        );

    }

}


// ============================================================
// FEATURE IMPORTANCE
// ============================================================

function renderFeatureImportance(
    features
) {

    const container =
        document.getElementById(
            "featureImportance"
        );


    container.innerHTML = "";


    if (
        !features ||
        Object.keys(features).length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">

                Model feature importance
                is not available.

            </div>

        `;

        return;

    }


    const featureNames = {

        Energy_Consumption_kWh:
            "Energy Consumption",

        Water_Consumption_L:
            "Water Consumption",

        Temperature_C:
            "Temperature",

        Humidity_Percent:
            "Humidity",

        CO2_Level_ppm:
            "CO₂ Level",

        Occupancy:
            "Occupancy"

    };


    const featureIcons = {

        Energy_Consumption_kWh:
            "⚡",

        Water_Consumption_L:
            "💧",

        Temperature_C:
            "🌡",

        Humidity_Percent:
            "💦",

        CO2_Level_ppm:
            "🌫",

        Occupancy:
            "👥"

    };


    const sortedFeatures =
        Object.entries(features)
        .sort(
            (a, b) =>
                b[1] - a[1]
        );


    sortedFeatures.forEach(
        ([feature, importance]) => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "feature-item";


            item.innerHTML = `

                <div class="feature-header">

                    <span>

                        <span class="feature-icon">

                            ${featureIcons[feature] || "•"}

                        </span>

                        ${featureNames[feature] || feature}

                    </span>


                    <strong>
                        ${Number(importance).toFixed(2)}%
                    </strong>

                </div>


                <div class="feature-track">

                    <div
                        class="feature-fill"
                        style="width: ${Math.min(Number(importance), 100)}%"
                    ></div>

                </div>

            `;


            container.appendChild(
                item
            );

        }
    );

}


// ============================================================
// IMPROVEMENT AREAS
// ============================================================

function renderImprovementAreas(
    areas
) {

    const container =
        document.getElementById(
            "improvementAreas"
        );


    container.innerHTML = "";


    if (
        !areas ||
        areas.length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">

                No improvement areas
                identified.

            </div>

        `;

        return;

    }


    areas.forEach(
        area => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "improvement-card";


            let icon =
                "💡";


            if (
                area.area.includes(
                    "Energy"
                )
            ) {

                icon =
                    "⚡";

            }

            else if (
                area.area.includes(
                    "Water"
                )
            ) {

                icon =
                    "💧";

            }

            else if (
                area.area.includes(
                    "Environmental"
                )
            ) {

                icon =
                    "🌬";

            }


            card.innerHTML = `

                <div class="improvement-icon">

                    ${icon}

                </div>


                <div>

                    <h4>
                        ${area.area}
                    </h4>

                    <p>
                        ${area.reason}
                    </p>

                    <div class="improvement-action">

                        <strong>
                            Action:
                        </strong>

                        ${area.action}

                    </div>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}


// ============================================================
// BUILDING RECOMMENDATIONS
// ============================================================

function renderBuildingRecommendations(
    recommendations
) {

    const container =
        document.getElementById(
            "buildingRecommendations"
        );


    container.innerHTML = "";


    if (
        !recommendations ||
        recommendations.length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">

                No building-specific recommendations
                were generated from the current dataset.

            </div>

        `;

        return;

    }


    recommendations.forEach(
        item => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "recommendation-item";


            const list =
                item.recommendations
                .map(
                    recommendation => `

                        <li>
                            ${recommendation}
                        </li>

                    `
                )
                .join("");


            card.innerHTML = `

                <div class="recommendation-building">

                    <span class="recommendation-building-icon">
                        🏢
                    </span>

                    <strong>
                        ${item.building}
                    </strong>

                </div>


                <ul>
                    ${list}
                </ul>

            `;


            container.appendChild(
                card
            );

        }
    );

}


// ============================================================
// PREDICTIVE ERROR
// ============================================================

function showPredictiveError() {

    const ids = [

        "attentionAreas",
        "predictiveBuildings",
        "trendAnalysis",
        "featureImportance",
        "improvementAreas",
        "buildingRecommendations"

    ];


    ids.forEach(
        id => {

            const element =
                document.getElementById(
                    id
                );


            if (element) {

                element.innerHTML = `

                    <div class="no-data error-message">

                        Unable to load predictive
                        analysis from the backend.

                        <br><br>

                        Make sure the Flask backend
                        is running on port 5000.

                    </div>

                `;

            }

        }
    );

}


// ============================================================
// INDIVIDUAL ML PREDICTION
// ============================================================

async function predictScore() {

    const energy =
        document.getElementById(
            "p_energy"
        ).value;


    const water =
        document.getElementById(
            "p_water"
        ).value;


    const temperature =
        document.getElementById(
            "p_temperature"
        ).value;


    const humidity =
        document.getElementById(
            "p_humidity"
        ).value;


    const co2 =
        document.getElementById(
            "p_co2"
        ).value;


    const occupancy =
        document.getElementById(
            "p_occupancy"
        ).value;


    const result =
        document.getElementById(
            "predictionResult"
        );


    result.innerHTML =
        "Calculating prediction...";


    try {

        const response =
            await fetch(
                `${API_URL}/api/predict`,
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

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


        const data =
            await response.json();


        if (
            data.predicted_sustainability_score
            !== undefined
        ) {

            result.innerHTML = `

                Predicted Sustainability Score:

                <strong>

                    ${data.predicted_sustainability_score}

                </strong>

                <span class="prediction-scale">
                    / 100
                </span>

            `;

        }

        else {

            result.textContent =
                "Prediction failed.";

        }

    }

    catch (error) {

        console.error(
            "Prediction error:",
            error
        );


        result.textContent =
            "Unable to connect to backend.";

    }

}


// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

loadDashboard();

loadEnergyChart();

loadPredictiveAnalysis();