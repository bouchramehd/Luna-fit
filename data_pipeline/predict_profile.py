from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    ROOT / "artifacts/nutrition_activity_profiles_v1"
    / "kmeans_k4.joblib"
)


def predict_profile(user):
    saved = joblib.load(MODEL_PATH)

    required = [
        "energy_kcal",
        *saved["nutrient_sources"],
        "vigorous_recreation_minutes_week",
        "moderate_recreation_minutes_week",
        "active_transport_minutes_week",
        "sedentary_minutes_day",
    ]

    values = {}
    for field in required:
        value = float(user[field])
        if not np.isfinite(value) or value < 0:
            raise ValueError(f"{field} must be finite and nonnegative")
        values[field] = value

    if values["energy_kcal"] <= 0:
        raise ValueError("Energy intake must be greater than zero")

    for field in required:
        if field.endswith("_minutes_week") and values[field] >= 10080:
            raise ValueError(f"{field} must be below 10,080")
    if values["sedentary_minutes_day"] >= 1440:
        raise ValueError("Sedentary minutes must be below 1,440")

    for nutrient in saved["nutrient_sources"]:
        values[nutrient + "_per_1000kcal"] = (
            values[nutrient] * 1000 / values["energy_kcal"]
        )

    frame = pd.DataFrame([values])[saved["features"]]
    transformed = saved["scaler"].transform(
        saved["imputer"].transform(np.log1p(frame))
    )
    profile = int(saved["model"].predict(transformed)[0])

    return {
        "profile_id": profile,
        "model": "nutrition_activity_kmeans_v1",
        "note": (
            "Similarity to an exploratory nutrition/activity group. "
            "Not a health score or an optimal diet/workout prescription."
        ),
    }


if __name__ == "__main__":
    # Synthetic example only—not your personal measurements.
    example = {
        "energy_kcal": 2000,
        "protein_g": 80,
        "carbohydrate_g": 250,
        "fat_g": 75,
        "iron_mg": 14,
        "vigorous_recreation_minutes_week": 90,
        "moderate_recreation_minutes_week": 150,
        "active_transport_minutes_week": 60,
        "sedentary_minutes_day": 420,
    }

    print("Synthetic example:")
    print(json.dumps(predict_profile(example), indent=2))