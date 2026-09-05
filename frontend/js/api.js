/* =========================================
   API CONFIGURATION
========================================= */

const API_BASE_URL = "http://127.0.0.1:8000";


/* =========================================
   SEARCH FIRES
========================================= */

async function searchFires(bounds) {

    const requestBody = {
        west: bounds.west,
        south: bounds.south,
        east: bounds.east,
        north: bounds.north
    };


    console.log("=================================");
    console.log("FIRE SEARCH REQUEST");
    console.log("=================================");

    console.log(requestBody);


    const response = await fetch(
        `${API_BASE_URL}/api/fires/search`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(requestBody)
        }
    );


    if (!response.ok) {

        const errorText =
            await response.text();

        throw new Error(
            `API Error ${response.status}: ${errorText}`
        );
    }


    const data =
        await response.json();


    /* =========================================
       NORMALIZE FIRE DATA
    ========================================= */

    const detections = (data.detections || []).map(fire => {

        return {

            ...fire,


            /* =====================================
               PERSISTENCE INFORMATION
            ===================================== */

            /*
             * Backend determines the persistence
             * status.
             *
             * Possible values:
             *
             * NEW
             * RECENT
             * INTERMITTENT
             * PERSISTENT
             */

            persistence_status:
                fire.persistence_status ?? null,


            persistence_score:
                fire.persistence_score ?? null,


            observation_count:
                fire.observation_count ?? null,


            active_days:
                fire.active_days ?? null,


            first_seen:
                fire.first_seen ?? null,


            last_seen:
                fire.last_seen ?? null,


            persistence_reason:
                fire.persistence_reason ?? null,


            /* =====================================
               ML FIELDS
            ===================================== */

            /*
             * Confidence remains available.
             *
             * ML classification is handled separately
             * from persistence analysis.
             */

            confidence:
                fire.confidence ?? null,


            detection_type:
                fire.detection_type ?? null,


            prediction_status:
                fire.prediction_status ?? null

        };

    });


    const normalizedData = {

        count: detections.length,

        detections: detections

    };


    /* =========================================
       LOG RESPONSE
    ========================================= */

    console.log("=================================");
    console.log("FIRE SEARCH RESPONSE");
    console.log("=================================");


    console.log(
        `Total active detections: ${normalizedData.count}`
    );


    /* =========================================
       PERSISTENCE SUMMARY
    ========================================= */

    const persistent =
        detections.filter(
            fire =>
                fire.persistence_status === "PERSISTENT"
        ).length;


    const intermittent =
        detections.filter(
            fire =>
                fire.persistence_status === "INTERMITTENT"
        ).length;


    const recent =
        detections.filter(
            fire =>
                fire.persistence_status === "RECENT"
        ).length;


    const newDetections =
        detections.filter(
            fire =>
                fire.persistence_status === "NEW"
        ).length;


    console.log(
        "Persistence summary:"
    );


    console.log(
        "Persistent:",
        persistent
    );


    console.log(
        "Intermittent:",
        intermittent
    );


    console.log(
        "Recent:",
        recent
    );


    console.log(
        "New:",
        newDetections
    );


    /* =========================================
       IMPORTANT
    ========================================= */

    /*
     * Historical detections are NOT returned by
     * the main fire search.
     *
     * Therefore:
     *
     * - No is_historical field
     * - No historical count
     * - No historical marker
     * - No historical persistence status
     *
     * Historical analysis will be handled by a
     * separate API feature later.
     */


    /* =========================================
       LOG DETECTIONS
    ========================================= */

    console.log(
        "Active detections:",
        detections
    );


    return normalizedData;
}


/* =========================================
   API HEALTH CHECK
========================================= */

async function checkAPI() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/api/health`
        );


        if (!response.ok) {

            return false;

        }


        const data =
            await response.json();


        return data.status === "healthy";


    } catch (error) {

        console.error(
            "API health check failed:",
            error
        );


        return false;
    }
}