
from fastapi import APIRouter, HTTPException

from backend.schemas.search import BoundingBoxRequest
from backend.schemas.fire import FireSearchResponse

from backend.utils.validation import validate_bbox

from backend.services.firms_api import fetch_firms_data
from backend.services.ingestion import insert_detections
from backend.services.spatial_service import get_fires_in_bbox


router = APIRouter(
    prefix="/api/fires",
    tags=["Fires"]
)


@router.post(
    "/search",
    response_model=FireSearchResponse
)
def search_fires(request: BoundingBoxRequest):

    try:

        # ======================================================
        # 1. Validate bounding box
        # ======================================================

        validate_bbox(
            request.west,
            request.south,
            request.east,
            request.north,
        )

        # ======================================================
        # 2. Fetch fresh NASA FIRMS data
        # ======================================================

        sources = [
            "VIIRS_NOAA21_NRT",
            "VIIRS_NOAA20_NRT",
            "VIIRS_SNPP_NRT"
        ]

        total_inserted = 0

        for source in sources:

            print("\n========================================")
            print("FIRE SEARCH")
            print("========================================")

            print("Source:", source)

            print(
                "Bounding Box:",
                request.west,
                request.south,
                request.east,
                request.north
            )

            # --------------------------------------------------
            # Fetch fresh FIRMS data for requested bbox
            # --------------------------------------------------

            df = fetch_firms_data(
                source,
                request.west,
                request.south,
                request.east,
                request.north
            )

            if df is None or df.empty:
                print("No FIRMS data returned for:", source)
                continue

            # ==================================================
            # 3. Store / deduplicate detections
            # ==================================================

            inserted = insert_detections(
                df,
                source
            )

            total_inserted += inserted

            print(
                f"{source}: {inserted} new detections inserted"
            )

        # ======================================================
        # 4. Read all detections inside requested bbox
        # ======================================================

        detections = get_fires_in_bbox(
            request.west,
            request.south,
            request.east,
            request.north,
        )

        # ======================================================
        # 5. Persistence analysis
        #
        # NOTE:
        # Persistence values are calculated dynamically.
        # No database/schema modification is required here.
        #
        # The actual persistence service can be connected here
        # once that file is ready.
        # ======================================================

        # Example future flow:
        #
        # detections = calculate_persistence(detections)

        # ======================================================
        # 6. ML classification
        #
        # ML will be connected here later.
        #
        # The ML model can produce:
        #   - detection_type
        #   - confidence
        #   - prediction_status
        #
        # ML probabilities remain in:
        #   probability_predictions
        #
        # No database alteration is required.
        # ======================================================

        # Example future flow:
        #
        # detections = run_classification(detections)

        # ======================================================
        # 7. Return response
        # ======================================================

        return {
            "count": len(detections),
            "detections": detections,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print("FIRE SEARCH ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Fire search failed: {str(e)}"
        )

