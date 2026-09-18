const API_URL = "http://127.0.0.1:5000";

let energyChart = null;

let digitalTwinBuildings = [];
let digitalTwinRecommendations = [];


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    try {

        const response =
            await fetch(`${API_URL}/api/analytics`);

        if (!response.ok) {
            throw new Error("Analytics request failed");
        }

        const data =
            await response.json();


        document.getElementById("energy").textContent =
            Number(data.average_energy).toFixed(2);

        document.getElementById("water").textContent =
            Number(data.average_water).toFixed(2);

        document.getElementById("occupancy").textContent =
            Number(data.average_occupancy).toFixed(2);

        document.getElementById("sustainability").textContent =
            Number(data.average_sustainability_score).toFixed(2);

        document.getElementById("temperature").textContent =
            Number(data.average_temperature).toFixed(2);

        document.getElementById("humidity").textContent =
            Number(data.average_humidity).toFixed(2);

        document.getElementById("co2").textContent =
            Number(data.average_co2).toFixed(2);

        document.getElementById("records").textContent =
            data.total_records;


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

        /*
            We use predictive-analysis here because it already
            contains the average sustainability score for every
            building.
        */

        const response =
            await fetch(
                `${API_URL}/api/predictive-analysis`
            );

        if (!response.ok) {

            throw new Error(
                "Building analysis request failed"
            );

        }

        const data =
            await response.json();


        const container =
            document.getElementById(
                "buildingScores"
            );


        if (!container) {

            console.error(
                "buildingScores element not found"
            );

            return;

        }


        container.innerHTML = "";


        const buildings =
            data.building_analysis || [];


        if (buildings.length === 0) {

            container.innerHTML = `
                <div class="no-data">
                    No building data available.
                </div>
            `;

            return;

        }


        const buildingOrder = [
            "Academic",
            "Main",
            "Hostel",
            "Placement"
        ];


        buildings.sort(
            (a, b) =>
                buildingOrder.indexOf(a.building) -
                buildingOrder.indexOf(b.building)
        );


        buildings.forEach(
            building => {

                const score =
                    Number(
                        building.sustainability_score
                    );


                const item =
                    document.createElement(
                        "div"
                    );


                item.className =
                    "building-item";


                item.innerHTML = `

                    <div class="building-header">

                        <span class="building-name">
                            ${building.building}
                        </span>

                        <span class="building-score">
                            ${score.toFixed(2)}
                        </span>

                    </div>


                    <div class="progress">

                        <div
                            class="progress-bar"
                            style="width: ${Math.min(score, 100)}%"
                        ></div>

                    </div>

                `;


                container.appendChild(
                    item
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Error loading building data:",
            error
        );


        const container =
            document.getElementById(
                "buildingScores"
            );


        if (container) {

            container.innerHTML = `

                <div class="no-data error-message">

                    Unable to load building data.

                    <br><br>

                    Make sure the Flask backend
                    is running on port 5000.

                </div>

            `;

        }

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


        if (!response.ok) {

            throw new Error(
                "Sensor data request failed"
            );

        }


        const data =
            await response.json();


        if (
            !Array.isArray(data) ||
            data.length === 0
        ) {

            console.error(
                "No sensor data available"
            );

            return;

        }


        /*
            Create campus-wide daily energy totals.

            Each date has 4 building records:

            Academic
            Hostel
            Main
            Placement

            We add them together to get one campus value
            for each date.
        */

        const dailyEnergy = {};


        data.forEach(
            item => {

                const date =
                    item.Timestamp;


                const energy =
                    Number(
                        item.Energy_Consumption_kWh
                    );


                if (
                    !date ||
                    Number.isNaN(energy)
                ) {

                    return;

                }


                if (
                    !dailyEnergy[date]
                ) {

                    dailyEnergy[date] = 0;

                }


                dailyEnergy[date] +=
                    energy;

            }
        );


        /*
            Sort DD-MM-YYYY dates properly.
        */

        const sortedDates =
            Object.keys(
                dailyEnergy
            ).sort(
                (a, b) => {

                    const [
                        dayA,
                        monthA,
                        yearA
                    ] =
                        a.split("-")
                         .map(Number);


                    const [
                        dayB,
                        monthB,
                        yearB
                    ] =
                        b.split("-")
                         .map(Number);


                    return new Date(
                        yearA,
                        monthA - 1,
                        dayA
                    ) -
                    new Date(
                        yearB,
                        monthB - 1,
                        dayB
                    );

                }
            );


        const energyValues =
            sortedDates.map(
                date =>
                    Number(
                        dailyEnergy[
                            date
                        ].toFixed(2)
                    )
            );


        const canvas =
            document.getElementById(
                "energyChart"
            );


        const wrapper =
            document.getElementById(
                "energyChartWrapper"
            );


        if (!canvas) {

            console.error(
                "energyChart canvas not found"
            );

            return;

        }


        /*
            Destroy old chart.
        */

        if (energyChart) {

            energyChart.destroy();

        }


        /*
            Make the canvas wider than the visible
            panel.

            One date gets approximately 55px.

            Minimum width = 1200px.
        */

        const chartWidth =
            Math.max(
                1200,
                sortedDates.length * 55
            );


        canvas.width =
            chartWidth;


        canvas.height =
            340;


        canvas.style.width =
            `${chartWidth}px`;


        canvas.style.height =
            "340px";


        /*
            Create chart.
        */

        energyChart =
            new Chart(
                canvas,
                {

                    type: "line",


                    data: {

                        labels:
                            sortedDates,

                        datasets: [

                            {

                                label:
                                    "Campus Energy Consumption",

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
                            false,

                        maintainAspectRatio:
                            false,


                        interaction: {

                            intersect:
                                false,

                            mode:
                                "index"

                        },


                        plugins: {

                            legend: {

                                display:
                                    false

                            },


                            tooltip: {

                                callbacks: {

                                    label:
                                        function(context) {

                                            return (
                                                " Energy: " +
                                                Number(
                                                    context.raw
                                                ).toLocaleString(
                                                    undefined,
                                                    {
                                                        maximumFractionDigits: 2
                                                    }
                                                ) +
                                                " kWh"
                                            );

                                        }

                                }

                            }

                        },


                        scales: {

                            x: {

                                grid: {

                                    display:
                                        false

                                },


                                ticks: {

                                    color:
                                        "#718096",

                                    maxTicksLimit:
                                        12,

                                    autoSkip:
                                        true,

                                    maxRotation:
                                        0,

                                    minRotation:
                                        0

                                }

                            },


                            y: {

                                beginAtZero:
                                    false,


                                grid: {

                                    color:
                                        "rgba(255,255,255,0.05)"

                                },


                                ticks: {

                                    color:
                                        "#718096",

                                    callback:
                                        function(value) {

                                            return (
                                                Number(
                                                    value
                                                ).toLocaleString() +
                                                " kWh"
                                            );

                                        }

                                }

                            }

                        }

                    }

                }
            );


        /*
            Make sure wrapper scrolls to the beginning.
        */

        if (wrapper) {

            wrapper.scrollLeft = 0;

        }

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


        if (!response.ok) {

            throw new Error(
                "Predictive analysis request failed"
            );

        }


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


    if (!container) {
        return;
    }


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
                    "CO"
                )
            ) {

                icon =
                    "🌫";

            }

            else if (
                area.area.includes(
                    "Sustainability"
                )
            ) {

                icon =
                    "🌱";

            }


            card.innerHTML = `

                <div class="attention-icon">

                    ${icon}

                </div>


                <div class="attention-content">

                    <div
                        class="attention-title-row"
                    >

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


                    <div
                        class="recommendation-text"
                    >

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
// SEVERITY
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
// PREDICTIVE BUILDINGS
// ============================================================

function renderPredictiveBuildings(
    buildings
) {

    const container =
        document.getElementById(
            "predictiveBuildings"
        );


    if (!container) {
        return;
    }


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

                <div
                    class="predictive-building-header"
                >

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


                <div
                    class="building-score-track"
                >

                    <div
                        class="building-score-fill"
                        style="
                            width:
                            ${Math.min(score, 100)}%
                        "
                    ></div>

                </div>


                <div
                    class="building-metrics"
                >

                    <div>

                        <span>
                            Energy
                        </span>

                        <strong>
                            ${Number(
                                building.energy
                            ).toFixed(2)}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Water
                        </span>

                        <strong>
                            ${Number(
                                building.water
                            ).toFixed(2)}
                        </strong>

                    </div>


                    <div>

                        <span>
                            CO₂
                        </span>

                        <strong>
                            ${Number(
                                building.co2
                            ).toFixed(2)}
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


    if (!container) {
        return;
    }


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


    if (!container) {
        return;
    }


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
        Object.entries(
            features
        ).sort(
            (a, b) =>
                Number(b[1]) -
                Number(a[1])
        );


    sortedFeatures.forEach(
        ([feature, importance]) => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "feature-item";


            const value =
                Number(
                    importance
                );


            item.innerHTML = `

                <div
                    class="feature-header"
                >

                    <span>

                        <span
                            class="feature-icon"
                        >

                            ${
                                featureIcons[
                                    feature
                                ] || "•"
                            }

                        </span>

                        ${
                            featureNames[
                                feature
                            ] || feature
                        }

                    </span>


                    <strong>
                        ${value.toFixed(2)}%
                    </strong>

                </div>


                <div
                    class="feature-track"
                >

                    <div
                        class="feature-fill"
                        style="
                            width:
                            ${Math.min(value, 100)}%
                        "
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


    if (!container) {
        return;
    }


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

                <div
                    class="improvement-icon"
                >

                    ${icon}

                </div>


                <div>

                    <h4>
                        ${area.area}
                    </h4>

                    <p>
                        ${area.reason}
                    </p>


                    <div
                        class="improvement-action"
                    >

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


    if (!container) {
        return;
    }


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
                (
                    item.recommendations || []
                )
                .map(
                    recommendation => `

                        <li>
                            ${recommendation}
                        </li>

                    `
                )
                .join("");


            card.innerHTML = `

                <div
                    class="recommendation-building"
                >

                    <span
                        class="recommendation-building-icon"
                    >
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

                    <div
                        class="no-data error-message"
                    >

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
        Number(
            document.getElementById(
                "p_energy"
            ).value
        );


    const water =
        Number(
            document.getElementById(
                "p_water"
            ).value
        );


    const temperature =
        Number(
            document.getElementById(
                "p_temperature"
            ).value
        );


    const humidity =
        Number(
            document.getElementById(
                "p_humidity"
            ).value
        );


    const co2 =
        Number(
            document.getElementById(
                "p_co2"
            ).value
        );


    const occupancy =
        Number(
            document.getElementById(
                "p_occupancy"
            ).value
        );


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
                                energy,

                            Water_Consumption_L:
                                water,

                            Temperature_C:
                                temperature,

                            Humidity_Percent:
                                humidity,

                            CO2_Level_ppm:
                                co2,

                            Occupancy:
                                occupancy

                        })

                }
            );


        if (!response.ok) {

            throw new Error(
                "Prediction request failed"
            );

        }


        const data =
            await response.json();


        if (
            data.predicted_sustainability_score
            !== undefined
        ) {

            result.innerHTML = `

                Predicted Sustainability Score:

                <strong>

                    ${
                        Number(
                            data.predicted_sustainability_score
                        ).toFixed(2)
                    }

                </strong>

                <span
                    class="prediction-scale"
                >
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
// DIGITAL TWIN
// ============================================================

async function loadDigitalTwin() {

    try {

        const response =
            await fetch(
                `${API_URL}/api/predictive-analysis`
            );


        if (!response.ok) {

            throw new Error(
                "Digital Twin API request failed"
            );

        }


        const data =
            await response.json();


        console.log(
            "Digital Twin Data:",
            data
        );


        digitalTwinBuildings =
            data.building_analysis || [];


        digitalTwinRecommendations =
            data.building_recommendations || [];


        digitalTwinBuildings.forEach(
            building => {

                const element =
                    document.getElementById(
                        `twinScore${building.building}`
                    );


                if (element) {

                    element.textContent =
                        Number(
                            building.sustainability_score
                        ).toFixed(1);

                }

            }
        );


        if (
            digitalTwinBuildings.length > 0
        ) {

            selectTwinBuilding(
                digitalTwinBuildings[0].building
            );

        }

    }

    catch (error) {

        console.error(
            "Digital Twin Error:",
            error
        );


        const details =
            document.getElementById(
                "twinBuildingDetails"
            );


        if (details) {

            details.innerHTML = `

                <div class="no-data">

                    Unable to load Digital Twin data.

                </div>

            `;

        }

    }

}


// ============================================================
// SELECT DIGITAL TWIN BUILDING
// ============================================================

function selectTwinBuilding(
    buildingName
) {

    console.log(
        "Selected building:",
        buildingName
    );


    const building =
        digitalTwinBuildings.find(
            item =>
                item.building ===
                buildingName
        );


    if (!building) {

        console.error(
            "Building data not found:",
            buildingName
        );

        return;

    }


    document
        .querySelectorAll(
            ".twin-building"
        )
        .forEach(
            button => {

                button.classList.remove(
                    "active"
                );

            }
        );


    const selectedButton =
        document.querySelector(
            `.twin-building[data-building="${buildingName}"]`
        );


    if (selectedButton) {

        selectedButton.classList.add(
            "active"
        );

    }


    const recommendationData =
        digitalTwinRecommendations.find(
            item =>
                item.building ===
                buildingName
        );


    let recommendation =
        "No specific recommendation available.";


    if (
        recommendationData &&
        recommendationData.recommendations &&
        recommendationData.recommendations.length > 0
    ) {

        recommendation =
            recommendationData
                .recommendations
                .join(", ");

    }


    const details =
        document.getElementById(
            "twinBuildingDetails"
        );


    if (!details) {
        return;
    }


    details.innerHTML = `

        <div
            class="twin-details-header"
        >

            <div
                class="twin-details-title"
            >

                <span>
                    🏢
                </span>

                <h4>
                    ${buildingName} Building
                </h4>

            </div>


            <div
                class="twin-details-score"
            >

                <span>
                    Sustainability
                </span>

                <strong>

                    ${
                        Number(
                            building.sustainability_score
                        ).toFixed(2)
                    }

                </strong>

            </div>

        </div>


        <div class="twin-metrics">


            <div class="twin-metric">

                <span
                    class="twin-metric-label"
                >
                    Energy
                </span>

                <strong>

                    ${
                        Number(
                            building.energy
                        ).toFixed(2)
                    }

                </strong>

                <small>
                    kWh
                </small>

            </div>


            <div class="twin-metric">

                <span
                    class="twin-metric-label"
                >
                    Water
                </span>

                <strong>

                    ${
                        Number(
                            building.water
                        ).toFixed(2)
                    }

                </strong>

                <small>
                    L
                </small>

            </div>


            <div class="twin-metric">

                <span
                    class="twin-metric-label"
                >
                    CO₂
                </span>

                <strong>

                    ${
                        Number(
                            building.co2
                        ).toFixed(2)
                    }

                </strong>

                <small>
                    ppm
                </small>

            </div>


            <div class="twin-metric">

                <span
                    class="twin-metric-label"
                >
                    Occupancy
                </span>

                <strong>

                    ${
                        Number(
                            building.occupancy
                        ).toFixed(2)
                    }

                </strong>

                <small>
                    people
                </small>

            </div>


        </div>


        <div class="twin-recommendation">

            <strong>
                Recommendation:
            </strong>

            ${recommendation}

        </div>

    `;

}


// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadDashboard();

        loadBuildingScores();

        loadEnergyChart();

        loadPredictiveAnalysis();

        loadDigitalTwin();

    }
);