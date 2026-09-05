// ============================================================
// UI.JS
// Industrial Fire Detection Dashboard
// ============================================================


// ============================================================
// UPDATE BOUNDING BOX UI
// ============================================================

function updateBoundingBoxUI(bounds) {

    const westElement = document.getElementById("west");
    const southElement = document.getElementById("south");
    const eastElement = document.getElementById("east");
    const northElement = document.getElementById("north");

    if (westElement) {
        westElement.textContent = bounds.west.toFixed(4);
    }

    if (southElement) {
        southElement.textContent = bounds.south.toFixed(4);
    }

    if (eastElement) {
        eastElement.textContent = bounds.east.toFixed(4);
    }

    if (northElement) {
        northElement.textContent = bounds.north.toFixed(4);
    }
}


// ============================================================
// UPDATE DETECTION COUNT
// ============================================================

function updateDetectionCount(count) {

    const element =
        document.getElementById("detectionCount");

    if (element) {
        element.textContent = count;
    }
}


// ============================================================
// UPDATE CLASSIFICATION + PERSISTENCE COUNTS
// ============================================================

function updateClassificationCounts(fires) {

    // --------------------------------------------------------
    // ML CLASSIFICATION COUNTS
    // --------------------------------------------------------

    let industrial = 0;
    let agriculture = 0;
    let forest = 0;


    // --------------------------------------------------------
    // PERSISTENCE COUNTS
    // --------------------------------------------------------

    let persistent = 0;
    let intermittent = 0;
    let recent = 0;
    let newDetections = 0;


    fires.forEach(fire => {

        // ====================================================
        // ML CLASSIFICATION
        // ====================================================

        const detectionType =
            (fire.detection_type || "").toUpperCase();


        if (detectionType === "INDUSTRIAL") {

            industrial++;

        }

        else if (
            detectionType === "AGRICULTURAL" ||
            detectionType === "AGRICULTURE"
        ) {

            agriculture++;

        }

        else if (
            detectionType === "FOREST" ||
            detectionType === "FOREST_FIRE"
        ) {

            forest++;

        }


        // ====================================================
        // ACTIVE PERSISTENCE CLASSIFICATION
        // ====================================================

        /*
         * The main fire-search API returns ONLY today's
         * active detections.
         *
         * Historical detections are therefore not processed
         * here and do not affect dashboard counters.
         */

        const persistence =
            (fire.persistence_status || "").toUpperCase();


        if (persistence === "PERSISTENT") {

            persistent++;

        }

        else if (persistence === "INTERMITTENT") {

            intermittent++;

        }

        else if (persistence === "RECENT") {

            recent++;

        }

        else if (persistence === "NEW") {

            newDetections++;

        }

    });


    // ========================================================
    // UPDATE ML CLASSIFICATION UI
    // ========================================================

    const industrialElement =
        document.getElementById("industrialCount");

    const agricultureElement =
        document.getElementById("agricultureCount");

    const forestElement =
        document.getElementById("forestCount");


    if (industrialElement) {
        industrialElement.textContent = industrial;
    }

    if (agricultureElement) {
        agricultureElement.textContent = agriculture;
    }

    if (forestElement) {
        forestElement.textContent = forest;
    }


    // ========================================================
    // UPDATE PERSISTENCE UI
    // ========================================================

    const persistentElement =
        document.getElementById("persistentCount");

    const intermittentElement =
        document.getElementById("intermittentCount");

    const recentElement =
        document.getElementById("recentCount");

    const newElement =
        document.getElementById("newCount");


    if (persistentElement) {
        persistentElement.textContent = persistent;
    }

    if (intermittentElement) {
        intermittentElement.textContent = intermittent;
    }

    if (recentElement) {
        recentElement.textContent = recent;
    }

    if (newElement) {
        newElement.textContent = newDetections;
    }


    // ========================================================
    // DEBUG LOG
    // ========================================================

    console.log(
        "Classification Summary:",
        {
            industrial: industrial,
            agriculture: agriculture,
            forest: forest
        }
    );


    console.log(
        "Persistence Summary:",
        {
            persistent: persistent,
            intermittent: intermittent,
            recent: recent,
            new: newDetections
        }
    );

}


// ============================================================
// LOADING STATE
// ============================================================

function setLoading(isLoading) {

    const searchButton =
        document.getElementById("searchButton");

    const loadingMessage =
        document.getElementById("loadingMessage");


    if (isLoading) {

        if (searchButton) {

            searchButton.disabled = true;

            searchButton.textContent =
                "Searching...";

        }

        if (loadingMessage) {

            loadingMessage.style.display =
                "block";

        }

    }

    else {

        if (searchButton) {

            searchButton.disabled = false;

            searchButton.textContent =
                "Search Fires";

        }

        if (loadingMessage) {

            loadingMessage.style.display =
                "none";

        }

    }
}


// ============================================================
// API STATUS
// ============================================================

function updateAPIStatus(isOnline) {

    const statusElement =
        document.getElementById("apiStatus");


    if (!statusElement) {
        return;
    }


    if (isOnline) {

        statusElement.textContent =
            "Online";

        statusElement.classList.remove(
            "offline"
        );

        statusElement.classList.add(
            "online"
        );

    }

    else {

        statusElement.textContent =
            "Offline";

        statusElement.classList.remove(
            "online"
        );

        statusElement.classList.add(
            "offline"
        );

    }
}


// ============================================================
// MAP MESSAGE
// ============================================================

function showMapMessage(message) {

    const messageElement =
        document.getElementById("mapMessage");


    if (!messageElement) {

        console.warn(
            "Map message:",
            message
        );

        return;
    }


    messageElement.textContent =
        message;

    messageElement.style.display =
        "block";


    // Automatically hide after 4 seconds

    setTimeout(() => {

        if (messageElement) {

            messageElement.style.display =
                "none";

        }

    }, 4000);
}