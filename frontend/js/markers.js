/* =========================================
   MARKER STORAGE
========================================= */

let fireMarkers = [];


/* =========================================
   CLEAR EXISTING MARKERS
========================================= */

function clearFireMarkers() {

    fireMarkers.forEach(
        marker => map.removeLayer(marker)
    );

    fireMarkers = [];
}


/* =========================================
   CREATE FIRE MARKER
========================================= */

function createFireMarker(fire) {

    /*
        Persistence status comes directly
        from the backend.

        NEW
        RECENT
        INTERMITTENT
        PERSISTENT
    */

    const persistenceStatus =
        fire.persistence_status
            ? fire.persistence_status.toLowerCase()
            : "recent";


    const icon =
        L.divIcon({

            className: "",

            html: `
                <div class="
                    fire-icon
                    persistence-${persistenceStatus}
                ">
                    🔥
                </div>
            `,

            iconSize: [24, 24],

            iconAnchor: [12, 12],

            popupAnchor: [0, -12]

        });


    const marker =
        L.marker(
            [
                fire.latitude,
                fire.longitude
            ],
            {
                icon: icon
            }
        );


    marker.bindPopup(
        createFirePopup(fire)
    );


    return marker;
}


/* =========================================
   FIRE POPUP
========================================= */

function createFirePopup(fire) {

    /* =====================================
       BASIC INFORMATION
    ===================================== */

    const acquisitionTime =
        formatDateTime(
            fire.acquisition_time
        );


    /* =====================================
       CONFIDENCE
    ===================================== */

    let confidence = "Not available";


    if (
        fire.confidence !== null &&
        fire.confidence !== undefined
    ) {

        const confidenceValue =
            Number(fire.confidence);


        if (!isNaN(confidenceValue)) {

            /*
                ML convention:

                0.94 = 94%
                94   = 94%

                Confidence is displayed only as
                the model confidence value.
            */

            const percentage =
                confidenceValue <= 1
                    ? confidenceValue * 100
                    : confidenceValue;


            confidence =
                `${percentage.toFixed(1)}%`;

        }
    }


    /* =====================================
       ML CLASSIFICATION
    ===================================== */

    const classification =
        fire.detection_type ??
        "Not classified";


    const predictionStatus =
        fire.prediction_status ??
        "Pending";


    /* =====================================
       PERSISTENCE
    ===================================== */

    const persistenceStatus =
        fire.persistence_status ??
        "RECENT";


    const persistenceScore =
        fire.persistence_score !== null &&
        fire.persistence_score !== undefined
            ? Number(
                fire.persistence_score
              ).toFixed(3)
            : "N/A";


    const observationCount =
        fire.observation_count ?? 0;


    const activeDays =
        fire.active_days ?? 0;


    const firstSeen =
        formatDateTime(
            fire.first_seen
        );


    const lastSeen =
        formatDateTime(
            fire.last_seen
        );


    const persistenceReason =
        fire.persistence_reason ??
        "No persistence history available.";


    /* =====================================
       PERSISTENCE BADGE CLASS
    ===================================== */

    const persistenceBadgeClass =
        persistenceStatus.toLowerCase();


    /* =====================================
       RETURN POPUP
    ===================================== */

    return `
        <div class="fire-popup">

            <!-- ============================
                 TITLE
            ============================= -->

            <div class="fire-popup-title">
                🔥 Fire Detection #${fire.id}
            </div>


            <!-- ============================
                 LOCATION
            ============================= -->

            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Latitude
                </span>

                <span class="fire-popup-value">
                    ${Number(fire.latitude).toFixed(5)}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Longitude
                </span>

                <span class="fire-popup-value">
                    ${Number(fire.longitude).toFixed(5)}
                </span>
            </div>


            <!-- ============================
                 FIRMS DATA
            ============================= -->

            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    FRP
                </span>

                <span class="fire-popup-value">
                    ${fire.frp ?? "N/A"} MW
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Brightness
                </span>

                <span class="fire-popup-value">
                    ${fire.brightness ?? "N/A"} K
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Satellite
                </span>

                <span class="fire-popup-value">
                    ${fire.satellite ?? "N/A"}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Source
                </span>

                <span class="fire-popup-value">
                    ${fire.source ?? "N/A"}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Acquisition
                </span>

                <span class="fire-popup-value">
                    ${acquisitionTime}
                </span>
            </div>


            <!-- ============================
                 PERSISTENCE ANALYSIS
            ============================= -->

            <div class="fire-popup-section-title">
                🔥 Persistence Analysis
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Status
                </span>

                <span class="
                    fire-popup-badge
                    persistence-${persistenceBadgeClass}
                ">
                    ${persistenceStatus}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Persistence Score
                </span>

                <span class="fire-popup-value">
                    ${persistenceScore}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Observations
                </span>

                <span class="fire-popup-value">
                    ${observationCount}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Active Days
                </span>

                <span class="fire-popup-value">
                    ${activeDays} / 5
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    First Seen
                </span>

                <span class="fire-popup-value">
                    ${firstSeen}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Last Seen
                </span>

                <span class="fire-popup-value">
                    ${lastSeen}
                </span>
            </div>


            <div class="fire-popup-reason">
                ${persistenceReason}
            </div>


            <!-- ============================
                 ML ANALYSIS
            ============================= -->

            <div class="fire-popup-section-title">
                🤖 ML Analysis
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Classification
                </span>

                <span class="fire-popup-badge">
                    ${classification}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    Confidence
                </span>

                <span class="fire-popup-value">
                    ${confidence}
                </span>
            </div>


            <div class="fire-popup-row">
                <span class="fire-popup-label">
                    ML Status
                </span>

                <span class="fire-popup-value">
                    ${predictionStatus}
                </span>
            </div>

        </div>
    `;
}


/* =========================================
   FORMAT DATE
========================================= */

function formatDateTime(value) {

    if (!value) {

        return "N/A";

    }


    const date =
        new Date(value);


    if (isNaN(date.getTime())) {

        return value;

    }


    return date.toLocaleString();

}


/* =========================================
   DISPLAY FIRES
========================================= */

function displayFires(fires) {

    clearFireMarkers();


    if (!fires || fires.length === 0) {

        console.log(
            "No active fire detections found."
        );

        return;
    }


    fires.forEach(
        fire => {

            const marker =
                createFireMarker(fire);


            marker.addTo(map);


            fireMarkers.push(marker);

        }
    );


    console.log(
        `${fireMarkers.length} active fire markers displayed.`
    );
}