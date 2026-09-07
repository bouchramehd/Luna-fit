from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# =========================
# USER
# =========================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# PROFILE
# =========================

class ProfileCreate(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=13, le=100)
    height_cm: Optional[float] = Field(default=None, gt=0)
    weight_kg: Optional[float] = Field(default=None, gt=0)

    activity_level: Optional[str] = None
    fitness_level: Optional[str] = None
    fitness_goal: Optional[str] = None

    training_location: Optional[str] = None
    sessions_per_week: Optional[int] = Field(default=None, ge=1, le=7)

    morphology: Optional[str] = None
    pregnancy_status: Optional[str] = None
    postpartum_status: Optional[str] = None


class ProfileResponse(ProfileCreate):
    id: int

    class Config:
        from_attributes = True


# =========================
# MENSTRUAL CYCLE
# =========================

class MenstrualCycleCreate(BaseModel):
    user_id: int
    last_period_date: date
    average_cycle_length: int = Field(default=28, ge=20, le=45)
    average_period_length: int = Field(default=5, ge=1, le=10)
    notes: Optional[str] = None


class MenstrualCycleResponse(MenstrualCycleCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# SYMPTOMS
# =========================

class SymptomCreate(BaseModel):
    user_id: int
    recorded_date: Optional[date] = None

    pain_level: Optional[int] = Field(default=None, ge=0, le=10)
    energy_level: Optional[int] = Field(default=None, ge=0, le=10)
    stress_level: Optional[int] = Field(default=None, ge=0, le=10)

    mood: Optional[str] = None
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)

    bloating: bool = False
    headache: bool = False
    fatigue: bool = False

    notes: Optional[str] = None


class SymptomResponse(SymptomCreate):
    id: int

    class Config:
        from_attributes = True


# =========================
# EXERCISE
# =========================

class ExerciseCreate(BaseModel):
    name: str
    description: Optional[str] = None

    category: Optional[str] = None
    muscle_group: Optional[str] = None
    difficulty: Optional[str] = None

    location: Optional[str] = None
    equipment: Optional[str] = None

    suitable_for_home: bool = True
    suitable_for_pregnancy: bool = False
    suitable_for_postpartum: bool = False
    pelvic_floor: bool = False


class ExerciseResponse(ExerciseCreate):
    id: int

    class Config:
        from_attributes = True


# =========================
# WORKOUT PLAN
# =========================

class WorkoutPlanCreate(BaseModel):
    user_id: int
    title: str
    goal: Optional[str] = None

    duration_minutes: Optional[int] = Field(default=None, gt=0)
    intensity: Optional[str] = None
    cycle_phase: Optional[str] = None

    description: Optional[str] = None


class WorkoutPlanResponse(WorkoutPlanCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# NUTRITION PLAN
# =========================

class NutritionPlanCreate(BaseModel):
    user_id: int

    daily_calories: Optional[float] = Field(default=None, gt=0)
    protein_g: Optional[float] = Field(default=None, ge=0)
    carbohydrates_g: Optional[float] = Field(default=None, ge=0)
    fats_g: Optional[float] = Field(default=None, ge=0)

    recommendation: Optional[str] = None
    cycle_phase: Optional[str] = None


class NutritionPlanResponse(NutritionPlanCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# PROGRESS
# =========================

class ProgressCreate(BaseModel):
    user_id: int
    recorded_date: Optional[date] = None

    weight_kg: Optional[float] = Field(default=None, gt=0)
    waist_cm: Optional[float] = Field(default=None, gt=0)
    hip_cm: Optional[float] = Field(default=None, gt=0)

    completed_workouts: int = Field(default=0, ge=0)
    wellbeing_score: Optional[int] = Field(default=None, ge=0, le=10)

    notes: Optional[str] = None


class ProgressResponse(ProgressCreate):
    id: int

    class Config:
        from_attributes = True