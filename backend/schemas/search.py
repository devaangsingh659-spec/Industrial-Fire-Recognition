from pydantic import BaseModel, Field


class BoundingBoxRequest(BaseModel):

    west: float = Field(
        ...,
        ge=-180,
        le=180
    )

    south: float = Field(
        ...,
        ge=-90,
        le=90
    )

    east: float = Field(
        ...,
        ge=-180,
        le=180
    )

    north: float = Field(
        ...,
        ge=-90,
        le=90
    )