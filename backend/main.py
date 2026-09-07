from datetime import date

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext

import models
import schemas
from database import Base, engine, get_db


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Fit Pour Femme API",
    description="API de personnalisation sportive et nutritionnelle pour les femmes",
    version="1.0.0"
)


# =========================================================
# PASSWORD SECURITY
# =========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# =========================================================
# GENERAL
# =========================================================

@app.get("/", tags=["General"])
def home():
    return {
        "message": "Bienvenue sur l'API Fit Pour Femme 💗",
        "status": "API opérationnelle"
    }


@app.get("/health", tags=["General"])
def health():
    return {
        "status": "OK"
    }


@app.get("/database-test", tags=["General"])
def database_test():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database();")
        )

        database_name = result.scalar()

    return {
        "status": "connected",
        "database": database_name
    }


# =========================================================
# USERS
# =========================================================

@app.post(
    "/users",
    response_model=schemas.UserResponse,
    tags=["Users"]
)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Un compte existe déjà avec cette adresse email."
        )

    hashed_password = pwd_context.hash(user.password)

    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get(
    "/users/{user_id}",
    response_model=schemas.UserResponse,
    tags=["Users"]
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    return user


# =========================================================
# PROFILES
# =========================================================

@app.post(
    "/profiles",
    response_model=schemas.ProfileResponse,
    tags=["Profiles"]
)
def create_profile(
    profile: schemas.ProfileCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == profile.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    existing_profile = (
        db.query(models.Profile)
        .filter(models.Profile.user_id == profile.user_id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Cet utilisateur possède déjà un profil."
        )

    new_profile = models.Profile(
        **profile.model_dump()
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile


@app.get(
    "/profiles/{user_id}",
    response_model=schemas.ProfileResponse,
    tags=["Profiles"]
)
def get_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    profile = (
        db.query(models.Profile)
        .filter(models.Profile.user_id == user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profil introuvable."
        )

    return profile


# =========================================================
# MENSTRUAL CYCLES
# =========================================================

@app.post(
    "/cycles",
    response_model=schemas.MenstrualCycleResponse,
    tags=["Menstrual Cycles"]
)
def create_cycle(
    cycle: schemas.MenstrualCycleCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == cycle.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    new_cycle = models.MenstrualCycle(
        **cycle.model_dump()
    )

    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)

    return new_cycle


@app.get(
    "/cycles/{user_id}",
    response_model=list[schemas.MenstrualCycleResponse],
    tags=["Menstrual Cycles"]
)
def get_cycles(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    cycles = (
        db.query(models.MenstrualCycle)
        .filter(models.MenstrualCycle.user_id == user_id)
        .order_by(models.MenstrualCycle.last_period_date.desc())
        .all()
    )

    return cycles


# =========================================================
# CYCLE STATUS
# =========================================================

@app.get(
    "/cycle-status/{user_id}",
    tags=["Menstrual Cycles"]
)
def get_cycle_status(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    cycle = (
        db.query(models.MenstrualCycle)
        .filter(models.MenstrualCycle.user_id == user_id)
        .order_by(models.MenstrualCycle.last_period_date.desc())
        .first()
    )

    if not cycle:
        raise HTTPException(
            status_code=404,
            detail="Aucun cycle menstruel trouvé."
        )

    today = date.today()

    days_since_period = (
        today - cycle.last_period_date
    ).days

    if days_since_period < 0:
        raise HTTPException(
            status_code=400,
            detail="La date des dernières règles ne peut pas être dans le futur."
        )

    cycle_length = cycle.average_cycle_length
    period_length = cycle.average_period_length

    cycle_day = (
        days_since_period % cycle_length
    ) + 1

    ovulation_day = cycle_length - 14

    if cycle_day <= period_length:
        phase = "menstruelle"
        message = (
            "Phase menstruelle : adapter l'activité au niveau "
            "d'énergie et au confort."
        )

    elif cycle_day < ovulation_day - 2:
        phase = "folliculaire"
        message = (
            "Phase folliculaire : l'énergie peut progressivement augmenter."
        )

    elif cycle_day <= ovulation_day + 2:
        phase = "ovulatoire"
        message = "Phase ovulatoire estimée."

    else:
        phase = "lutéale"
        message = (
            "Phase lutéale : adapter l'intensité selon "
            "l'énergie et les symptômes ressentis."
        )

    return {
        "user_id": user_id,
        "date": today,
        "cycle_day": cycle_day,
        "cycle_length": cycle_length,
        "period_length": period_length,
        "estimated_ovulation_day": ovulation_day,
        "cycle_phase": phase,
        "message": message
    }


# =========================================================
# SYMPTOMS
# =========================================================

@app.post(
    "/symptoms",
    response_model=schemas.SymptomResponse,
    tags=["Symptoms"]
)
def create_symptom(
    symptom: schemas.SymptomCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == symptom.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    symptom_data = symptom.model_dump(
        exclude_none=True
    )

    new_symptom = models.Symptom(
        **symptom_data
    )

    db.add(new_symptom)
    db.commit()
    db.refresh(new_symptom)

    return new_symptom


@app.get(
    "/symptoms/{user_id}",
    response_model=list[schemas.SymptomResponse],
    tags=["Symptoms"]
)
def get_symptoms(
    user_id: int,
    db: Session = Depends(get_db)
):
    symptoms = (
        db.query(models.Symptom)
        .filter(models.Symptom.user_id == user_id)
        .order_by(models.Symptom.recorded_date.desc())
        .all()
    )

    return symptoms


# =========================================================
# PROGRESS
# =========================================================

@app.post(
    "/progress",
    response_model=schemas.ProgressResponse,
    tags=["Progress"]
)
def create_progress(
    progress: schemas.ProgressCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == progress.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    progress_data = progress.model_dump(
        exclude_none=True
    )

    new_progress = models.Progress(
        **progress_data
    )

    db.add(new_progress)
    db.commit()
    db.refresh(new_progress)

    return new_progress


@app.get(
    "/progress/{user_id}",
    response_model=list[schemas.ProgressResponse],
    tags=["Progress"]
)
def get_progress(
    user_id: int,
    db: Session = Depends(get_db)
):
    progress_entries = (
        db.query(models.Progress)
        .filter(models.Progress.user_id == user_id)
        .order_by(models.Progress.recorded_date.desc())
        .all()
    )

    return progress_entries


# =========================================================
# EXERCISES
# =========================================================

@app.post(
    "/exercises",
    response_model=schemas.ExerciseResponse,
    tags=["Exercises"]
)
def create_exercise(
    exercise: schemas.ExerciseCreate,
    db: Session = Depends(get_db)
):
    new_exercise = models.Exercise(
        **exercise.model_dump()
    )

    db.add(new_exercise)
    db.commit()
    db.refresh(new_exercise)

    return new_exercise


@app.get(
    "/exercises",
    response_model=list[schemas.ExerciseResponse],
    tags=["Exercises"]
)
def get_exercises(
    db: Session = Depends(get_db)
):
    exercises = (
        db.query(models.Exercise)
        .all()
    )

    return exercises


@app.get(
    "/exercises/{exercise_id}",
    response_model=schemas.ExerciseResponse,
    tags=["Exercises"]
)
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db)
):
    exercise = (
        db.query(models.Exercise)
        .filter(models.Exercise.id == exercise_id)
        .first()
    )

    if not exercise:
        raise HTTPException(
            status_code=404,
            detail="Exercice introuvable."
        )

    return exercise


# =========================================================
# WORKOUT PLANS
# =========================================================

@app.post(
    "/workout-plans",
    response_model=schemas.WorkoutPlanResponse,
    tags=["Workout Plans"]
)
def create_workout_plan(
    plan: schemas.WorkoutPlanCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == plan.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    new_plan = models.WorkoutPlan(
        **plan.model_dump()
    )

    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    return new_plan


@app.get(
    "/workout-plans/{user_id}",
    response_model=list[schemas.WorkoutPlanResponse],
    tags=["Workout Plans"]
)
def get_workout_plans(
    user_id: int,
    db: Session = Depends(get_db)
):
    plans = (
        db.query(models.WorkoutPlan)
        .filter(models.WorkoutPlan.user_id == user_id)
        .order_by(models.WorkoutPlan.created_at.desc())
        .all()
    )

    return plans


# =========================================================
# NUTRITION PLANS
# =========================================================

@app.post(
    "/nutrition-plans",
    response_model=schemas.NutritionPlanResponse,
    tags=["Nutrition Plans"]
)
def create_nutrition_plan(
    plan: schemas.NutritionPlanCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.id == plan.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable."
        )

    new_plan = models.NutritionPlan(
        **plan.model_dump()
    )

    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    return new_plan


@app.get(
    "/nutrition-plans/{user_id}",
    response_model=list[schemas.NutritionPlanResponse],
    tags=["Nutrition Plans"]
)
def get_nutrition_plans(
    user_id: int,
    db: Session = Depends(get_db)
):
    plans = (
        db.query(models.NutritionPlan)
        .filter(models.NutritionPlan.user_id == user_id)
        .order_by(models.NutritionPlan.created_at.desc())
        .all()
    )

    return plans