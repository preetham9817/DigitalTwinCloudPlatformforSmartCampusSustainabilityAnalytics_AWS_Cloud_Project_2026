/* =========================================================
   DIGITAL TWIN CAMPUS
   AUTOMATIC BUILDING SYSTEM
========================================================= */

const API_BASE_URL = "http://127.0.0.1:5000";


let buildingData = [];
let energyTrendData = [];

let energyChartInstance = null;
let buildingChartInstance = null;

let selectedBuilding = null;


/* =========================================================
   BUILDING CONFIGURATION
========================================================= */

const buildingConfig = {

    Academic: {
        floors: 8,
        type: "Academic Building"
    },

    Main: {
        floors: 5,
        type: "Main Building"
    },

    Hostel: {
        floors: 10,
        type: "Hostel Building"
    },

    Placement: {
        floors: 4,
        type: "Placement Building"
    }

};


/* =========================================================
   DOM HELPERS
========================================================= */

function getElement(id) {

    return document.getElementById(id);

}


function setText(id, value) {

    const element = getElement(id);

    if (element) {

        element.textContent = value;

    }

}


/* =========================================================
   FORMAT
========================================================= */

function formatNumber(value, decimals = 2) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        !Number.isFinite(Number(value))
    ) {

        return "--";

    }

    return Number(value).toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }
    );

}


/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHTML(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


/* =========================================================
   FETCH
========================================================= */

async function fetchJSON(
    endpoint,
    options = {}
) {

    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
            ...options,

            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        }
    );


    let data;

    try {

        data = await response.json();

    } catch {

        throw new Error(
            `Invalid response from ${endpoint}`
        );

    }


    if (!response.ok) {

        throw new Error(
            data.error ||
            `Request failed: ${response.status}`
        );

    }


    return data;

}


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeDashboard();

        setupPredictionForm();

    }
);


async function initializeDashboard() {

    try {

        await loadAnalytics();

    } catch (error) {

        console.error(
            "Analytics error:",
            error
        );

    }


    try {

        await loadSustainability();

    } catch (error) {

        console.error(
            "Sustainability error:",
            error
        );

        generateFallbackInsights();

    }


    try {

        await loadEnergyTrend();

    } catch (error) {

        console.error(
            "Energy trend error:",
            error
        );

    }


    try {

        await loadPredictiveAnalysis();

    } catch (error) {

        console.error(
            "Predictive analysis error:",
            error
        );

        generateFallbackInsights();

    }

}


/* =========================================================
   ANALYTICS
========================================================= */

async function loadAnalytics() {

    const data =
        await fetchJSON(
            "/api/analytics"
        );


    setText(
        "energy",
        formatNumber(
            data.energyConsumption
        )
    );


    setText(
        "water",
        formatNumber(
            data.waterConsumption
        )
    );


    setText(
        "occupancy",
        formatNumber(
            data.occupancy
        )
    );


    setText(
        "sustainability",
        formatNumber(
            data.bsei
        )
    );


    setText(
        "temperature",
        formatNumber(
            data.temperature
        )
    );


    setText(
        "humidity",
        formatNumber(
            data.humidity
        )
    );


    setText(
        "co2",
        formatNumber(
            data.co2
        )
    );

}


/* =========================================================
   SUSTAINABILITY
========================================================= */

async function loadSustainability() {

    const data =
        await fetchJSON(
            "/api/sustainability"
        );


    if (
        !data ||
        !Array.isArray(data.buildings)
    ) {

        throw new Error(
            "Building data unavailable"
        );

    }


    buildingData =
        data.buildings;


    renderBuildingTabs();

    updateDigitalTwin();

    renderBuildingChart();

    generateFallbackInsights();

}


/* =========================================================
   BUILDING NAME
========================================================= */

function formatBuildingName(id) {

    const value =
        String(id || "").trim();


    if (!value) {

        return "Unknown Building";

    }


    return value
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );

}


/* =========================================================
   BUILDING CONFIG
========================================================= */

function getBuildingConfig(name) {

    const key =
        Object.keys(buildingConfig)
            .find(
                item =>
                    item.toLowerCase() ===
                    String(name).toLowerCase()
            );


    if (key) {

        return buildingConfig[key];

    }


    return {

        floors: "Not specified",

        type:
            `${formatBuildingName(name)} Building`

    };

}


/* =========================================================
   FIND BUILDING
========================================================= */

function findBuilding(name) {

    if (!Array.isArray(buildingData)) {

        return null;

    }


    return buildingData.find(
        building => {

            const id =
                String(
                    building.Building_ID || ""
                ).toLowerCase();


            return (
                id ===
                String(name).toLowerCase()
            );

        }
    ) || null;

}


/* =========================================================
   RENDER BUILDING TABS
========================================================= */

function renderBuildingTabs() {

    const container =
        getElement("buildingTabs");


    if (!container) {

        return;

    }


    container.innerHTML = "";


    if (!buildingData.length) {

        container.innerHTML = `
            <div class="no-buildings">
                No building data available.
            </div>
        `;

        return;

    }


    buildingData.forEach(
        (building, index) => {

            const name =
                String(
                    building.Building_ID ||
                    `Building ${index + 1}`
                );


            const displayName =
                formatBuildingName(name);


            const config =
                getBuildingConfig(name);


            const button =
                document.createElement("button");


            button.type = "button";

            button.className =
                "building-card";


            button.dataset.building =
                name;


            button.innerHTML = `

                <span class="building-label">

                    ${escapeHTML(
                        getBuildingLabel(name)
                    )}

                </span>

                <h3>
                    ${escapeHTML(
                        config.type ||
                        `${displayName} Building`
                    )}
                </h3>

                <span class="building-score-label">
                    BSEI
                </span>

                <strong>
                    ${formatNumber(
                        building.BSEI
                    )}
                </strong>

                <span class="view-details">
                    View details →
                </span>

            `;


            button.addEventListener(
                "click",
                () => {

                    selectBuilding(name);

                }
            );


            container.appendChild(button);

        }
    );


    updateBuildingCount();

}


/* =========================================================
   BUILDING LABEL
========================================================= */

function getBuildingLabel(name) {

    const lower =
        String(name).toLowerCase();


    if (lower.includes("academic")) {

        return "ACADEMIC";

    }


    if (lower.includes("main")) {

        return "ADMINISTRATION";

    }


    if (lower.includes("hostel")) {

        return "RESIDENTIAL";

    }


    if (lower.includes("placement")) {

        return "CAREER CENTRE";

    }


    return "CAMPUS BUILDING";

}


/* =========================================================
   BUILDING COUNT
========================================================= */

function updateBuildingCount() {

    const badge =
        getElement(
            "buildingCountBadge"
        );


    if (!badge) {

        return;

    }


    badge.textContent =
        `${buildingData.length} ${
            buildingData.length === 1
                ? "Building"
                : "Buildings"
        }`;

}


/* =========================================================
   DIGITAL TWIN
========================================================= */

function updateDigitalTwin() {

    if (!buildingData.length) {

        return;

    }


    if (
        !selectedBuilding ||
        !findBuilding(selectedBuilding)
    ) {

        selectedBuilding =
            buildingData[0].Building_ID;

    }


    selectBuilding(
        selectedBuilding
    );

}


/* =========================================================
   SELECT BUILDING
========================================================= */

function selectBuilding(name) {

    selectedBuilding =
        name;


    document
        .querySelectorAll(
            ".building-card"
        )
        .forEach(
            card => {

                card.classList.remove(
                    "active"
                );


                if (
                    String(
                        card.dataset.building
                    ).toLowerCase()
                    ===
                    String(name).toLowerCase()
                ) {

                    card.classList.add(
                        "active"
                    );

                }

            }
        );


    const building =
        findBuilding(name);


    if (!building) {

        return;

    }


    const config =
        getBuildingConfig(name);


    const displayName =
        formatBuildingName(
            building.Building_ID
        );


    setText(
        "twinBuildingName",
        config.type ||
        `${displayName} Building`
    );


    setText(
        "twinBuildingType",
        displayName
    );


    setText(
        "twinSelectedBsei",
        formatNumber(
            building.BSEI
        )
    );


    setText(
        "twinFloors",
        config.floors
    );


    setText(
        "twinEnergy",
        formatNumber(
            building.Energy_Consumption_kWh
        )
    );


    setText(
        "twinWater",
        formatNumber(
            building.Water_Consumption_L
        )
    );


    setText(
        "twinOccupancy",
        formatNumber(
            building.Occupancy
        )
    );


    setText(
        "twinCO2",
        formatNumber(
            building.CO2_Level_ppm
        )
    );


    setText(
        "twinTemperature",
        formatNumber(
            building.Temperature_C
        )
    );


    setText(
        "twinHumidity",
        formatNumber(
            building.Humidity_Percent
        )
    );


    setText(
        "twinRecommendation",
        building.Recommendation ||
        generateRecommendation(building)
    );

}


/* =========================================================
   RECOMMENDATION
========================================================= */

function generateRecommendation(
    building
) {

    const bsei =
        Number(
            building.BSEI || 0
        );


    if (bsei < 40) {

        return (
            "Review energy and water consumption patterns " +
            "and prioritize efficiency improvements."
        );

    }


    if (bsei < 55) {

        return (
            "Review energy and water consumption patterns " +
            "and continue monitoring environmental performance."
        );

    }


    return (
        "Continue monitoring resource consumption " +
        "and maintain current sustainability performance."
    );

}


/* =========================================================
   ENERGY TREND
========================================================= */

async function loadEnergyTrend() {

    const data =
        await fetchJSON(
            "/api/energy-trend"
        );


    if (!Array.isArray(data)) {

        return;

    }


    energyTrendData =
        data;


    renderEnergyChart();

}


/* =========================================================
   ENERGY CHART
========================================================= */

function renderEnergyChart() {

    const canvas =
        getElement(
            "energyChart"
        );


    if (
        !canvas ||
        energyTrendData.length === 0
    ) {

        return;

    }


    if (energyChartInstance) {

        energyChartInstance.destroy();

    }


    const labels =
        energyTrendData.map(
            item =>
                item.date || ""
        );


    const energy =
        energyTrendData.map(
            item =>
                Number(
                    item.energy || 0
                )
        );


    const water =
        energyTrendData.map(
            item =>
                Number(
                    item.water || 0
                )
        );


    energyChartInstance =
        new Chart(
            canvas,
            {

                type: "line",

                data: {

                    labels,

                    datasets: [

                        {

                            label:
                                "Energy (kWh)",

                            data:
                                energy,

                            borderColor:
                                "#1f6fe5",

                            backgroundColor:
                                "rgba(31,111,229,.10)",

                            borderWidth: 2,

                            pointRadius: 2,

                            tension: .35,

                            fill: true

                        },


                        {

                            label:
                                "Water (L)",

                            data:
                                water,

                            borderColor:
                                "#20b879",

                            backgroundColor:
                                "rgba(32,184,121,.06)",

                            borderWidth: 2,

                            pointRadius: 2,

                            tension: .35,

                            fill: false

                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {

                        mode: "index",

                        intersect: false

                    },


                    plugins: {

                        legend: {

                            labels: {

                                color:
                                    "#526b89",

                                font: {

                                    family:
                                        "Inter",

                                    size: 11

                                }

                            }

                        }

                    },


                    scales: {

                        x: {

                            ticks: {

                                color:
                                    "#7890ac",

                                maxTicksLimit:
                                    8,

                                font: {

                                    family:
                                        "Inter",

                                    size: 10

                                }

                            },

                            grid: {

                                color:
                                    "#e9eef5"

                            }

                        },


                        y: {

                            ticks: {

                                color:
                                    "#7890ac",

                                font: {

                                    family:
                                        "Inter",

                                    size: 10

                                }

                            },

                            grid: {

                                color:
                                    "#e9eef5"

                            }

                        }

                    }

                }

            }
        );

}


/* =========================================================
   BUILDING CHART
========================================================= */

function renderBuildingChart() {

    const canvas =
        getElement(
            "buildingChart"
        );


    if (
        !canvas ||
        buildingData.length === 0
    ) {

        return;

    }


    if (buildingChartInstance) {

        buildingChartInstance.destroy();

    }


    const labels =
        buildingData.map(
            building =>
                formatBuildingName(
                    building.Building_ID
                )
        );


    const values =
        buildingData.map(
            building =>
                Number(
                    building.BSEI || 0
                )
        );


    buildingChartInstance =
        new Chart(
            canvas,
            {

                type: "bar",

                data: {

                    labels,

                    datasets: [

                        {

                            label:
                                "BSEI",

                            data:
                                values,

                            backgroundColor:
                                "#1f6fe5",

                            borderRadius: 6,

                            maxBarThickness: 65

                        }

                    ]

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

                            ticks: {

                                color:
                                    "#526b89",

                                font: {

                                    family:
                                        "Inter",

                                    size: 10

                                }

                            },

                            grid: {

                                display: false

                            }

                        },


                        y: {

                            beginAtZero: true,

                            max: 100,

                            ticks: {

                                color:
                                    "#7890ac",

                                font: {

                                    family:
                                        "Inter",

                                    size: 10

                                }

                            },

                            grid: {

                                color:
                                    "#e9eef5"

                            }

                        }

                    }

                }

            }
        );

}


/* =========================================================
   PREDICTIVE ANALYSIS
========================================================= */

async function loadPredictiveAnalysis() {

    const data =
        await fetchJSON(
            "/api/predictive-analysis"
        );


    renderInsight(
        "attentionAreas",
        data.attentionAreas
    );


    renderInsight(
        "predictiveBuildings",
        data.buildingPerformance
    );


    renderInsight(
        "trendAnalysis",
        data.historicalTrends
    );


    renderInsight(
        "improvementAreas",
        data.improvementAreas
    );


    renderInsight(
        "buildingRecommendations",
        data.buildingRecommendations
    );

}


function renderBuildingPerformance(buildings) {

    const metrics = [
        ["Energy_Consumption_kWh", "Energy Consumption (kWh / record)"],
        ["Water_Consumption_L", "Water Consumption (L / record)"],
        ["CO2_Level_ppm", "CO₂ Level (ppm)"],
        ["Temperature_C", "Temperature (°C)"],
        ["Humidity_Percent", "Humidity (%)"],
        ["Occupancy", "Occupancy (per record)"],
        ["Records", "Records"]
    ];

    return `
        <div class="performance-list">
            ${buildings.map(building => `
                <article class="performance-card">
                    <h4>${escapeHTML(
                        formatBuildingName(building.Building_ID)
                    )}</h4>
                    <p class="performance-score">
                        BSEI <strong>${escapeHTML(
                            formatNumber(building.BSEI)
                        )}</strong>
                    </p>
                    <dl class="performance-metrics">
                        ${metrics.map(([key, label]) => `
                            <div>
                                <dt>${escapeHTML(label)}</dt>
                                <dd>${escapeHTML(
                                    key === "Records"
                                        ? formatValue(building[key])
                                        : formatNumber(building[key])
                                )}</dd>
                            </div>
                        `).join("")}
                    </dl>
                </article>
            `).join("")}
        </div>
    `;

}


function renderBuildingRecommendations(buildings) {

    return `
        <div class="recommendation-list">
            ${buildings.map(building => `
                <article class="recommendation-card">
                    <h4>${escapeHTML(
                        formatBuildingName(building.Building_ID)
                    )}</h4>
                    <p class="recommendation-gap">
                        Largest weighted gap:
                        <strong>${escapeHTML(
                            building.Recommendation_Component
                                ? formatBuildingName(
                                    building.Recommendation_Component
                                )
                                : "Unavailable"
                        )}</strong>
                        ·
                        <strong>${escapeHTML(
                            building.Recommendation_Gap === null ||
                            building.Recommendation_Gap === undefined
                                ? "--"
                                : `${formatNumber(
                                    building.Recommendation_Gap
                                )} BSEI points`
                        )}</strong>
                    </p>
                    <p class="recommendation-gap-breakdown">
                        Component gaps (BSEI points):
                        ${building.Recommendation_Gaps
                            ? ["energy", "water", "environment"].map(key => `
                                <span>
                                    ${escapeHTML(
                                        formatBuildingName(key)
                                    )}
                                    ${escapeHTML(
                                        formatNumber(
                                            building.Recommendation_Gaps[key]
                                        )
                                    )}
                                </span>
                            `).join(" · ")
                            : "Unavailable"}
                    </p>
                    <p>${escapeHTML(
                        building.Recommendation ||
                        "Collect complete sensor readings to support a building-specific action."
                    )}</p>
                </article>
            `).join("")}
        </div>
    `;

}


function renderWeightDistribution(weights) {

    const labels = [
        ["energy", "Energy"],
        ["environment", "Environment"],
        ["water", "Water"]
    ];

    return `
        <div class="weight-list">
            ${labels.map(([key, label]) => `
                <div class="weight-item">
                    <span>${label}</span>
                    <strong>${escapeHTML(
                        formatNumber(weights[key], 0)
                    )}%</strong>
                </div>
            `).join("")}
        </div>
    `;

}


function renderAttentionAreas(alerts) {

    const alertItems = Array.isArray(alerts)
        ? alerts.filter(item => item && typeof item === "object")
        : [];

    if (!alertItems.length) {
        return `
            <div class="attention-empty" role="status">
                <span class="attention-empty-icon" aria-hidden="true">✓</span>
                <div>
                    <strong>No validated alerts at this time</strong>
                    <p>No building is below campus BSEI or component-efficiency comparisons.</p>
                </div>
            </div>
        `;
    }

    return `
        <div class="attention-panel">
            <div class="attention-alert-list">
                ${alertItems.map(item => {
                    const severityClass =
                        item.severity === "review"
                            ? "needs-review"
                            : "monitor";
                    const title = item.title || item.area || "Monitoring";
                    const status = item.status || "Monitor";
                    const value = item.value === null ||
                        item.value === undefined
                        ? "Not available"
                        : `${formatNumber(item.value)} ${item.unit || ""}`.trim();

                    return `
                        <article class="attention-alert-card">
                            <div class="attention-alert-topline">
                                <span class="attention-alert-icon" aria-hidden="true">
                                    ${escapeHTML(item.icon || "ℹ")}
                                </span>
                                <h4>${escapeHTML(title)}</h4>
                                <span class="attention-status ${severityClass}">
                                    ${escapeHTML(status)}
                                </span>
                            </div>
                            <p class="attention-alert-subject">
                                ${escapeHTML(item.affected || "Campus")}
                                ${item.metric ? ` · ${escapeHTML(item.metric)}` : ""}
                            </p>
                            <p class="attention-alert-value">
                                <strong>${escapeHTML(value)}</strong>
                                <span>
                                    BSEI ${escapeHTML(formatNumber(item.bsei))}
                                    ${item.weightedGap !== undefined
                                        ? ` · Weighted gap ${escapeHTML(
                                            formatNumber(item.weightedGap)
                                        )} points`
                                        : ""}
                                </span>
                            </p>
                            ${item.observedConsumption !== undefined ? `
                                <p class="attention-alert-subject">
                                        Mean water consumption:
                                        ${escapeHTML(
                                            Number(
                                                item.observedConsumption
                                            ).toLocaleString("en-US", {
                                                minimumFractionDigits: 2,
                                                maximumFractionDigits: 2
                                            })
                                        )} ${escapeHTML(item.consumptionUnit || "")}
                                </p>
                            ` : ""}
                            <p class="attention-alert-explanation">
                                ${escapeHTML(
                                    item.message || "Monitoring context only."
                                )}
                            </p>
                            ${item.recommendation ? `
                                <p class="attention-alert-action">
                                    <strong>Suggested action:</strong>
                                    ${escapeHTML(item.recommendation)}
                                </p>
                            ` : ""}
                        </article>
                    `;
                }).join("")}
            </div>
        </div>
    `;

}


/* =========================================================
   INSIGHT RENDERING
========================================================= */

function renderInsight(
    id,
    content
) {

    const element =
        getElement(id);


    if (!element) {

        return;

    }

    if (id === "attentionAreas") {
        element.innerHTML = renderAttentionAreas(content);
        return;
    }

    if (
        content === null ||
        content === undefined ||
        content === ""
    ) {

        element.textContent =
            "No analysis available.";

        return;

    }

    if (
        id === "predictiveBuildings" &&
        Array.isArray(content)
    ) {

        element.innerHTML = content.length
            ? renderBuildingPerformance(content)
            : "No building performance data available.";
        return;

    }

    if (
        id === "improvementAreas" &&
        content &&
        typeof content === "object" &&
        !Array.isArray(content)
    ) {

        element.innerHTML = renderWeightDistribution(content);
        return;

    }


    if (
        id === "buildingRecommendations" &&
        Array.isArray(content)
    ) {

        if (!content.length) {
            element.textContent = "No building recommendations available.";
            return;
        }

        if (content.some(item => item && typeof item === "object")) {
            element.innerHTML = renderBuildingRecommendations(content);
            return;
        }

        element.innerHTML = `
            <ul>
                ${content.map(item => `
                    <li>${escapeHTML(formatInsight(item))}</li>
                `).join("")}
            </ul>
        `;
        return;

    }


    if (Array.isArray(content)) {

        element.innerHTML = `

            <ul>

                ${
                    content
                        .map(
                            item =>
                                `<li>${escapeHTML(
                                    formatInsight(item)
                                )}</li>`
                        )
                        .join("")
                }

            </ul>

        `;

        return;

    }


    if (
        typeof content === "object"
    ) {

        element.innerHTML = `

            <ul>

                ${
                    Object.entries(content)
                        .map(
                            ([key, value]) => `

                                <li>

                                    <strong>
                                        ${escapeHTML(
                                            formatKey(key)
                                        )}
                                    </strong>

                                    :

                                    ${escapeHTML(
                                        formatValue(value)
                                    )}

                                </li>

                            `
                        )
                        .join("")
                }

            </ul>

        `;

        return;

    }


    element.textContent =
        String(content);

}


/* =========================================================
   INSIGHT FORMAT
========================================================= */

function formatInsight(item) {

    if (
        typeof item === "string" ||
        typeof item === "number"
    ) {

        return String(item);

    }


    if (
        item &&
        typeof item === "object"
    ) {

        return Object.entries(item)
            .map(
                ([key, value]) =>
                    `${formatKey(key)}: ${formatValue(value)}`
            )
            .join(" • ");

    }


    return "";

}


function formatKey(key) {

    const labels = {
        bsei: "BSEI",
        building_id: "Building",
        energy_consumption_kwh: "Energy Consumption (kWh)",
        water_consumption_l: "Water Consumption (L)",
        co2_level_ppm: "CO₂ Level (ppm)",
        temperature_c: "Temperature (°C)",
        humidity_percent: "Humidity (%)",
        occupancy: "Occupancy",
        records: "Records",
        recommendation: "Recommendation",
        area: "Area",
        unit: "Unit",
        value: "Value",
        message: "Reason"
    };

    const normalizedKey = String(key).toLowerCase();

    if (labels[normalizedKey]) {
        return labels[normalizedKey];
    }

    return String(key)

        .replace(
            /([a-z])([A-Z])/g,
            "$1 $2"
        )

        .replace(
            /_/g,
            " "
        )

        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
        );

}


function formatValue(value) {

    if (
        typeof value === "number"
    ) {

        return formatNumber(
            value
        );

    }


    if (
        Array.isArray(value)
    ) {

        return value.join(", ");

    }


    return String(
        value ?? "--"
    );

}


/* =========================================================
   FALLBACK INSIGHTS
========================================================= */

function generateFallbackInsights() {

    if (!buildingData.length) {

        return;

    }

    renderInsight(
        "attentionAreas",
        []
    );


    renderInsight(
        "predictiveBuildings",
        buildingData
    );


    renderInsight(
        "trendAnalysis",
        [
            "Historical energy and water consumption can be monitored through the resource analytics chart."
        ]
    );


    renderInsight(
        "improvementAreas",
        {
            energy: 45,
            environment: 20,
            water: 35
        }
    );


    renderInsight(
        "buildingRecommendations",
        buildingData
    );

}


/* =========================================================
   MACHINE LEARNING
========================================================= */

function setupPredictionForm() {

    const form =
        getElement(
            "predictionForm"
        );


    if (!form) {

        return;

    }


    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const values = {

                energy:
                    Number(
                        getElement(
                            "p_energy"
                        ).value
                    ),

                water:
                    Number(
                        getElement(
                            "p_water"
                        ).value
                    ),

                power:
                    Number(
                        getElement(
                            "p_power"
                        ).value
                    ),

                temperature:
                    Number(
                        getElement(
                            "p_temperature"
                        ).value
                    ),

                humidity:
                    Number(
                        getElement(
                            "p_humidity"
                        ).value
                    ),

                electricity_coverage:
                    Number(
                        getElement(
                            "p_electricity_coverage"
                        ).value
                    ),

                water_coverage:
                    Number(
                        getElement(
                            "p_water_coverage"
                        ).value
                    ),

                day_of_week:
                    Number(
                        getElement(
                            "p_day"
                        ).value
                    ),

                month:
                    Number(
                        getElement(
                            "p_month"
                        ).value
                    ),

                is_weekend:
                    Number(
                        getElement(
                            "p_weekend"
                        ).value
                    )

            };


            const resultElement =
                getElement(
                    "predictionResult"
                );


            resultElement.innerHTML = `
                <span>
                    Calculating...
                </span>
            `;


            try {

                const result =
                    await fetchJSON(
                        "/api/predict",
                        {

                            method: "POST",

                            body:
                                JSON.stringify(
                                    values
                                )

                        }
                    );


                const predicted =
                    Number(
                        result.predictedBSEI
                    );


                resultElement.innerHTML = `

                    <div class="prediction-main">

                        <span>
                            Predicted BSEI
                        </span>

                        <strong>
                            ${formatNumber(
                                predicted
                            )}
                        </strong>

                        <small>
                            / 100
                        </small>

                    </div>


                    <div class="prediction-components">

                        <div>

                            <span>
                                Energy Efficiency
                            </span>

                            <strong>
                                ${formatNumber(
                                    result.energyEfficiency
                                )}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Water Efficiency
                            </span>

                            <strong>
                                ${formatNumber(
                                    result.waterEfficiency
                                )}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Environmental Efficiency
                            </span>

                            <strong>
                                ${formatNumber(
                                    result.environmentalEfficiency
                                )}
                            </strong>

                        </div>

                    </div>

                `;

            } catch (error) {

                console.error(
                    "Prediction error:",
                    error
                );


                resultElement.innerHTML = `

                    <div class="prediction-error">

                        Prediction failed.

                        <br>

                        <small>
                            ${escapeHTML(
                                error.message
                            )}
                        </small>

                    </div>

                `;

            }

        }
    );

}