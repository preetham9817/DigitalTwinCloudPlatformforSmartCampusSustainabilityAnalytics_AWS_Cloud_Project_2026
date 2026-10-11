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
let awsDataRefreshTimer = null;
let awsDataRefreshInProgress = false;
let awsLastRetrievedAt = null;
let awsTrendRecords = [];
let awsTrendCharts = {};
let awsTrendRefreshInProgress = false;


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

        const awsRefreshButton = getElement("awsDataRefresh");
        if (awsRefreshButton) {
            awsRefreshButton.addEventListener(
                "click",
                loadAwsSensorData
            );
        }
        const awsTrendRefreshButton = getElement("awsTrendRefresh");
        if (awsTrendRefreshButton) {
            awsTrendRefreshButton.addEventListener(
                "click",
                loadAwsSensorHistory
            );
        }
        const awsTrendBuildingFilter = getElement("awsTrendBuildingFilter");
        if (awsTrendBuildingFilter) {
            awsTrendBuildingFilter.addEventListener(
                "change",
                renderAwsSensorTrends
            );
        }
        startAwsDataAutoRefresh();
        window.addEventListener("pagehide", stopAwsDataAutoRefresh);
        window.addEventListener("pageshow", event => {
            if (event.persisted) {
                startAwsDataAutoRefresh();
                loadAwsSensorData();
            }
        });

    }
);


function startAwsDataAutoRefresh() {

    if (awsDataRefreshTimer !== null) {
        return;
    }

    awsDataRefreshTimer = window.setInterval(() => {
        if (!document.hidden) {
            loadAwsSensorData();
        }
    }, 30000);

}


function stopAwsDataAutoRefresh() {

    if (awsDataRefreshTimer === null) {
        return;
    }

    window.clearInterval(awsDataRefreshTimer);
    awsDataRefreshTimer = null;

}


async function initializeDashboard() {

    loadAwsSensorData();
    loadAwsSensorHistory();

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
   LIVE AWS SENSOR DATA
========================================================= */

async function loadAwsSensorData() {

    const refreshButton = getElement("awsDataRefresh");
    const status = getElement("awsDataStatus");
    const recordsElement = getElement("awsSensorRecords");
    const updatedElement = getElement("awsDataUpdated");

    if (!status || !recordsElement) {
        return;
    }

    if (awsDataRefreshInProgress) {
        return;
    }

    awsDataRefreshInProgress = true;

    if (refreshButton) {
        refreshButton.disabled = true;
        refreshButton.textContent = "Refreshing...";
    }
    status.textContent = "Loading AWS records...";
    status.className = "aws-data-status is-loading";

    try {
        const data = await fetchJSON("/api/aws-data");
        if (!data || !Array.isArray(data.records)) {
            throw new Error("AWS sensor data response has an invalid format.");
        }

        const latestByBuilding = new Map();
        for (const record of data.records) {
            if (!record || typeof record !== "object" || Array.isArray(record)) {
                continue;
            }

            const building = String(
                record.Building_ID || record.building_id || ""
            ).trim();
            const key = (building || "unknown").toLocaleLowerCase();
            if (!latestByBuilding.has(key)) {
                latestByBuilding.set(key, {
                    ...record,
                    Building_ID: building || "Unknown Building"
                });
            }
        }

        const latestRecords = Array.from(latestByBuilding.values());
        if (!latestRecords.length) {
            recordsElement.innerHTML = `
                <div class="aws-data-message">
                    No processed AWS sensor records are available in S3 yet.
                </div>
            `;
        } else {
            recordsElement.innerHTML = latestRecords.map(record => {
                const score = record.BSEI ?? record.Sustainability_Score ??
                    record.sustainability_score;
                const hasBsei = record.BSEI !== undefined &&
                    record.BSEI !== null;
                const timestamp = record.timestamp || record.Timestamp ||
                    record.timestamp_utc || record.s3LastModified;
                const metricRows = [
                    ["Energy", record.Energy_Consumption_kWh, "kWh"],
                    ["Water", record.Water_Consumption_L, "L"],
                    ["Occupancy", record.Occupancy, ""],
                    ["Temperature", record.Temperature_C, "°C"],
                    ["Humidity", record.Humidity_Percent, "%"],
                    ["CO₂", record.CO2_Level_ppm, "ppm"],
                    [
                        score === undefined || score === null
                            ? null
                            : (hasBsei
                                ? "BSEI"
                                : "Sustainability Score"),
                        score,
                        score === undefined || score === null ? "" : "/100"
                    ]
                ].filter(([label]) => label);

                const metrics = metricRows.map(([label, value, unit]) => `
                    <div class="aws-sensor-metric">
                        <span>${escapeHTML(label)}</span>
                        <strong>${escapeHTML(
                            value === null || value === undefined ||
                            value === "" || !Number.isFinite(Number(value))
                                ? "--"
                                : `${formatNumber(value)} ${unit}`.trim()
                        )}</strong>
                    </div>
                `).join("");

                return `
                    <article class="aws-sensor-card">
                        <div class="aws-sensor-card-header">
                            <h3>${escapeHTML(record.Building_ID)}</h3>
                            <span class="aws-source-badge">S3 processed</span>
                        </div>
                        <p class="aws-sensor-timestamp">
                            ${escapeHTML(timestamp || "Timestamp unavailable")}
                        </p>
                        <div class="aws-sensor-metrics">${metrics}</div>
                    </article>
                `;
            }).join("");
        }

        const malformedCount = Number(data.malformedRecords) || 0;
        status.textContent = malformedCount
            ? `Connected · ${malformedCount} malformed record(s) skipped`
            : "Connected to S3";
        status.className = "aws-data-status is-connected";
        awsLastRetrievedAt = data.retrievedAt || new Date().toISOString();
        if (updatedElement) {
            updatedElement.textContent =
                `Retrieved ${awsLastRetrievedAt} · Showing latest reading per building`;
        }
    } catch (error) {
        console.error("AWS sensor data error:", error);
        status.textContent = "AWS data unavailable";
        status.className = "aws-data-status is-error";
        recordsElement.innerHTML = `
            <div class="aws-data-message is-error" role="alert">
                ${escapeHTML(error.message || "Unable to retrieve AWS sensor data.")}
                Check Flask AWS access and refresh to try again.
            </div>
        `;
        if (updatedElement) {
            updatedElement.textContent = awsLastRetrievedAt
                ? `Last successful retrieval: ${awsLastRetrievedAt}`
                : "No successful retrieval yet.";
        }
    } finally {
        awsDataRefreshInProgress = false;
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.textContent = "Refresh";
        }
    }

}


/* =========================================================
   AWS SENSOR TRENDS
========================================================= */

const awsTrendBuildingNames = [
    "Academic",
    "Hostel",
    "Main",
    "Placement"
];

const awsTrendDefinitions = [
    {
        key: "energy",
        label: "Energy Consumption",
        unit: "kWh",
        canvas: "awsTrendEnergy",
        empty: "awsTrendEnergyEmpty",
        card: "awsTrendEnergyCard",
        color: "#1f6fe5",
        fields: ["Energy_Consumption_kWh", "energy_consumption_kWh"],
        required: true
    },
    {
        key: "water",
        label: "Water Consumption",
        unit: "L",
        canvas: "awsTrendWater",
        empty: "awsTrendWaterEmpty",
        card: "awsTrendWaterCard",
        color: "#20b879",
        fields: ["Water_Consumption_L", "water_consumption_L"],
        required: true
    },
    {
        key: "bsei",
        label: "BSEI Sustainability Score",
        unit: "BSEI",
        canvas: "awsTrendBsei",
        empty: "awsTrendBseiEmpty",
        card: "awsTrendBseiCard",
        color: "#7257c5",
        fields: ["BSEI", "Sustainability_Score", "sustainability_score"],
        required: true,
        max: 100
    },
    {
        key: "temperature",
        label: "Temperature",
        unit: "°C",
        canvas: "awsTrendTemperature",
        empty: "awsTrendTemperatureEmpty",
        card: "awsTrendTemperatureCard",
        color: "#e98a35",
        fields: ["Temperature_C", "temperature_C"],
        required: false
    },
    {
        key: "co2",
        label: "CO₂ Level",
        unit: "ppm",
        canvas: "awsTrendCo2",
        empty: "awsTrendCo2Empty",
        card: "awsTrendCo2Card",
        color: "#298a88",
        fields: ["CO2_Level_ppm", "co2_level_ppm"],
        required: false
    }
];


function readAwsTrendMetric(record, fields) {

    for (const field of fields) {
        const value = Number(record[field]);
        if (
            record[field] !== null &&
            record[field] !== undefined &&
            record[field] !== "" &&
            Number.isFinite(value)
        ) {
            return value;
        }
    }

    return null;

}


function parseAwsTrendTimestamp(record) {

    const value = record.timestamp || record.Timestamp ||
        record.timestamp_utc || record.timestampUtc;
    if (!value) {
        return null;
    }

    const timestamp = new Date(value);
    return Number.isNaN(timestamp.getTime())
        ? null
        : timestamp;

}


function formatAwsTrendTimestamp(timestamp) {

    return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "medium"
    }).format(timestamp);

}


async function loadAwsSensorHistory() {

    const status = getElement("awsTrendStatus");
    const updated = getElement("awsTrendUpdated");
    const refreshButton = getElement("awsTrendRefresh");

    if (!status || awsTrendRefreshInProgress) {
        return;
    }

    awsTrendRefreshInProgress = true;
    status.textContent = "Loading S3 history...";
    status.className = "aws-data-status is-loading";
    if (refreshButton) {
        refreshButton.disabled = true;
        refreshButton.textContent = "Loading...";
    }

    try {
        const data = await fetchJSON("/api/aws-data/history?limit=500");
        if (!data || !Array.isArray(data.records)) {
            throw new Error("AWS history response has an invalid format.");
        }

        const buildingNames = new Map(
            awsTrendBuildingNames.map(name => [name.toLocaleLowerCase(), name])
        );
        let recordsWithoutTimestamp = 0;
        let recordsForOtherBuildings = 0;

        awsTrendRecords = data.records.reduce((parsed, record) => {
            if (
                !record ||
                typeof record !== "object" ||
                Array.isArray(record)
            ) {
                return parsed;
            }

            const rawBuilding = String(
                record.Building_ID || record.building_id || ""
            ).trim();
            const building = buildingNames.get(rawBuilding.toLocaleLowerCase());
            if (!building) {
                recordsForOtherBuildings += 1;
                return parsed;
            }

            const timestamp = parseAwsTrendTimestamp(record);
            if (!timestamp) {
                recordsWithoutTimestamp += 1;
                return parsed;
            }

            const values = {};
            for (const definition of awsTrendDefinitions) {
                values[definition.key] = readAwsTrendMetric(
                    record,
                    definition.fields
                );
            }

            parsed.push({
                building,
                timestamp: timestamp.toISOString(),
                timestampMs: timestamp.getTime(),
                values
            });
            return parsed;
        }, []);

        awsTrendRecords.sort(
            (left, right) => left.timestampMs - right.timestampMs
        );
        renderAwsSensorTrends();

        const malformedCount = Number(data.malformedRecords) || 0;
        const skippedCount = malformedCount +
            recordsWithoutTimestamp +
            recordsForOtherBuildings;
        status.textContent = awsTrendRecords.length
            ? `Loaded ${awsTrendRecords.length} timestamped record(s)${
                skippedCount ? ` · ${skippedCount} skipped` : ""
            }`
            : "No timestamped AWS history available";
        status.className = awsTrendRecords.length
            ? "aws-data-status is-connected"
            : "aws-data-status";

        if (updated) {
            const limitNote = data.hasMore
                ? ` · Showing the newest ${data.limit} records`
                : "";
            updated.textContent = data.retrievedAt
                ? `Retrieved ${formatAwsTrendTimestamp(
                    new Date(data.retrievedAt)
                )}${limitNote}`
                : limitNote.trim();
        }
    } catch (error) {
        console.error("AWS sensor trends error:", error);
        status.textContent = "AWS trends unavailable";
        status.className = "aws-data-status is-error";
        for (const definition of awsTrendDefinitions) {
            const canvas = getElement(definition.canvas);
            const empty = getElement(definition.empty);
            const card = getElement(definition.card);
            if (awsTrendCharts[definition.key]) {
                awsTrendCharts[definition.key].destroy();
                delete awsTrendCharts[definition.key];
            }
            if (card) {
                card.hidden = !definition.required;
            }
            if (canvas) {
                canvas.hidden = true;
            }
            if (empty) {
                empty.hidden = false;
                empty.textContent = error.message
                    ? `${error.message} Refresh to retry.`
                    : "Unable to load S3 history. Check AWS access and refresh to retry.";
                empty.classList.add("is-error");
            }
        }
        if (updated) {
            updated.textContent = "";
        }
    } finally {
        awsTrendRefreshInProgress = false;
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.textContent = "Refresh Trends";
        }
    }

}


function renderAwsSensorTrends() {

    const filter = getElement("awsTrendBuildingFilter");
    const selectedBuilding = filter ? filter.value : "all";
    const visibleRecords = awsTrendRecords.filter(record =>
        selectedBuilding === "all" ||
        record.building === selectedBuilding
    );

    for (const definition of awsTrendDefinitions) {
        const canvas = getElement(definition.canvas);
        const empty = getElement(definition.empty);
        const card = getElement(definition.card);
        if (!canvas || !empty || !card) {
            continue;
        }

        const hasAnyMetric = awsTrendRecords.some(
            record => record.values[definition.key] !== null
        );
        card.hidden = !definition.required && !hasAnyMetric;

        const metricRecords = visibleRecords.filter(
            record => record.values[definition.key] !== null
        );
        if (
            !metricRecords.length ||
            typeof Chart === "undefined"
        ) {
            if (awsTrendCharts[definition.key]) {
                awsTrendCharts[definition.key].destroy();
                delete awsTrendCharts[definition.key];
            }
            canvas.hidden = true;
            empty.hidden = false;
            empty.classList.remove("is-error");
            empty.textContent = typeof Chart === "undefined"
                ? "Chart library is unavailable."
                : `No ${definition.label.toLowerCase()} readings are available for this selection.`;
            continue;
        }

        canvas.hidden = false;
        empty.hidden = true;
        empty.classList.remove("is-error");
        if (awsTrendCharts[definition.key]) {
            awsTrendCharts[definition.key].destroy();
        }

        const timestamps = Array.from(new Set(
            metricRecords.map(record => record.timestamp)
        )).sort(
            (left, right) => new Date(left) - new Date(right)
        );
        const labels = timestamps.map(timestamp =>
            formatAwsTrendTimestamp(new Date(timestamp))
        );
        const datasets = awsTrendBuildingNames
            .filter(building =>
                selectedBuilding === "all" ||
                selectedBuilding === building
            )
            .map((building, index) => {
                const valuesByTimestamp = new Map(
                    metricRecords
                        .filter(record => record.building === building)
                        .map(record => [
                            record.timestamp,
                            record.values[definition.key]
                        ])
                );
                const colors = [
                    "#1f6fe5",
                    "#20b879",
                    "#7257c5",
                    "#e98a35"
                ];

                return {
                    label: building,
                    data: timestamps.map(timestamp =>
                        valuesByTimestamp.has(timestamp)
                            ? valuesByTimestamp.get(timestamp)
                            : null
                    ),
                    borderColor: colors[index],
                    backgroundColor: colors[index],
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 4,
                    tension: 0.2,
                    spanGaps: false
                };
            })
            .filter(dataset => dataset.data.some(value => value !== null));

        awsTrendCharts[definition.key] = new Chart(canvas, {
            type: "line",
            data: { labels, datasets },
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
                            color: "#526b89",
                            font: {
                                family: "Inter",
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            title: items => items.length
                                ? items[0].label
                                : ""
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: "#7890ac",
                            maxTicksLimit: 8,
                            maxRotation: 0,
                            autoSkip: true,
                            font: {
                                family: "Inter",
                                size: 10
                            }
                        },
                        grid: {
                            color: "#e9eef5"
                        }
                    },
                    y: {
                        beginAtZero: definition.key !== "temperature",
                        suggestedMax: definition.max,
                        title: {
                            display: true,
                            text: definition.unit,
                            color: "#526b89"
                        },
                        ticks: {
                            color: "#7890ac",
                            font: {
                                family: "Inter",
                                size: 10
                            }
                        },
                        grid: {
                            color: "#e9eef5"
                        }
                    }
                }
            }
        });
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