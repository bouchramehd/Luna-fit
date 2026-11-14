import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from data_pipeline.predict_profile import predict_profile

router = APIRouter(prefix="/ai", tags=["Nutrition/activity profiles"])
logger = logging.getLogger(__name__)

PROFILES = {
    0: {
        "name": "Recreational activity pattern",
        "description": (
            "This group showed more reported vigorous and moderate "
            "recreational activity than the other groups."
        ),
    },
    1: {
        "name": "Active transport pattern",
        "description": (
            "This group showed more reported walking or cycling "
            "for transport than the other groups."
        ),
    },
    2: {
        "name": "Higher fat-density pattern",
        "description": (
            "This group had higher median fat intake per 1,000 kcal. "
            "Median reported recreational and transport activity was zero."
        ),
    },
    3: {
        "name": "Higher carbohydrate-density pattern",
        "description": (
            "This group had higher median carbohydrate and iron intake "
            "per 1,000 kcal. Median reported recreational and transport "
            "activity was zero."
        ),
    },
}


class ProfileRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )

    age: int = Field(ge=18, le=120)
    energy_kcal: float = Field(gt=0)
    protein_g: float = Field(ge=0)
    carbohydrate_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    iron_mg: float = Field(ge=0)
    vigorous_recreation_minutes_week: float = Field(ge=0, lt=10080)
    moderate_recreation_minutes_week: float = Field(ge=0, lt=10080)
    active_transport_minutes_week: float = Field(ge=0, lt=10080)
    sedentary_minutes_day: float = Field(ge=0, lt=1440)


class ProfileResponse(BaseModel):
    profile_id: int
    profile_name: str
    description: str
    model: str
    note: str
    interpretation: str


@router.post("/profile", response_model=ProfileResponse)
def assign_profile(request: ProfileRequest):
    """Assign reported habits to an exploratory profile; no data saved."""
    try:
        result = predict_profile(
            request.model_dump(exclude={"age"})
        )
    except FileNotFoundError:
        logger.exception("Profile model artifact is missing")
        raise HTTPException(
            status_code=503,
            detail="The profile model is currently unavailable.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    details = PROFILES[result["profile_id"]]

    return {
        **result,
        "profile_name": details["name"],
        "description": details["description"],
        "interpretation": (
            "Descriptions summarize observed group medians in the "
            "2015–2016 validation sample, not every member. "
            "Profiles are not ranked. Occupational activity is not "
            "included. Age establishes adult eligibility but does "
            "not affect assignment."
        ),
    }