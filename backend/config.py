import os
from dotenv import load_dotenv

load_dotenv()

FIRMS_MAP_KEY = os.getenv("662b654655d35e0ec62380681a7483fa")
DATABASE_URL = os.getenv("postgresql://postgres:Debrup@localhost:5432/industrial_fire_db")

FIRMS_SOURCE = os.getenv(
    "FIRMS_SOURCE",
    "VIIRS_NOAA21_NRT"
)

FIRMS_DAY_RANGE = int(
    os.getenv("FIRMS_DAY_RANGE", "1")
)


if not FIRMS_MAP_KEY:
    raise RuntimeError(
        "FIRMS_MAP_KEY is missing from .env"
    )

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing from .env"
    )