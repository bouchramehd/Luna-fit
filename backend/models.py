from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    cycles = relationship("MenstrualCycle", back_populates="user")
    symptoms = relationship("Symptom", back_populates="user")
    workout_plans = relationship("WorkoutPlan", back_populates="user")
    nutrition_plans = relationship("NutritionPlan", back_populates="user")
    progress_entries = relationship("Progress", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    first_name = Column(String(100))
    age = Column(Integer)
    height_cm = Column(Float)
    weight_kg = Column(Float)

    activity_level = Column(String(50))
    fitness_level = Column(String(50))
    fitness_goal = Column(String(100))

    training_location = Column(String(50))
    sessions_per_week = Column(Integer)

    morphology = Column(String(100))
    pregnancy_status = Column(String(50))
    postpartum_status = Column(String(50))

    user = relationship("User", back_populates="profile")


class MenstrualCycle(Base):
    __tablename__ = "menstrual_cycles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    last_period_date = Column(Date, nullable=False)
    average_cycle_length = Column(Integer, default=28)
    average_period_length = Column(Integer, default=5)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cycles")


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    recorded_date = Column(Date, default=date.today)

    pain_level = Column(Integer)
    energy_level = Column(Integer)
    stress_level = Column(Integer)
    mood = Column(String(50))
    sleep_hours = Column(Float)

    bloating = Column(Boolean, default=False)
    headache = Column(Boolean, default=False)
    fatigue = Column(Boolean, default=False)

    notes = Column(Text)

    user = relationship("User", back_populates="symptoms")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    description = Column(Text)

    category = Column(String(100))
    muscle_group = Column(String(100))
    difficulty = Column(String(50))

    location = Column(String(50))
    equipment = Column(String(150))

    suitable_for_home = Column(Boolean, default=True)
    suitable_for_pregnancy = Column(Boolean, default=False)
    suitable_for_postpartum = Column(Boolean, default=False)
    pelvic_floor = Column(Boolean, default=False)


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(150), nullable=False)
    goal = Column(String(100))

    duration_minutes = Column(Integer)
    intensity = Column(String(50))
    cycle_phase = Column(String(50))

    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workout_plans")


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    daily_calories = Column(Float)
    protein_g = Column(Float)
    carbohydrates_g = Column(Float)
    fats_g = Column(Float)

    recommendation = Column(Text)
    cycle_phase = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="nutrition_plans")


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    recorded_date = Column(Date, default=date.today)

    weight_kg = Column(Float)
    waist_cm = Column(Float)
    hip_cm = Column(Float)

    completed_workouts = Column(Integer, default=0)
    wellbeing_score = Column(Integer)

    notes = Column(Text)

    user = relationship("User", back_populates="progress_entries")