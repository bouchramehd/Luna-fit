from pathlib import Path

import joblib
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
folder = root / "artifacts/nutrition_activity_profiles_v1"

data = pd.read_parquet(
    root / "data/gold/nutrition_activity_profiles_v1/women"
)
data = data[
    data.eligible_for_profile_analysis
    & data.survey_cycle.eq("2015-2016")
].copy()

for k in (2, 4):
    saved = joblib.load(folder / f"kmeans_k{k}.joblib")
    sample = data.copy()

    for column in saved["nutrient_sources"]:
        sample[column + "_per_1000kcal"] = (
            sample[column] * 1000 / sample.energy_kcal
        )

    features = saved["features"]
    values = np.log1p(sample[features].astype(float))
    transformed = saved["scaler"].transform(
        saved["imputer"].transform(values)
    )
    sample["profile"] = saved["model"].predict(transformed)

    print(f"\n=== {k} profiles: validation participants ===")
    print(sample.groupby("profile").size().rename("participants").to_string())

    # Summaries use original units and observed values, not imputed values.
    columns = [
        "RIDAGEYR", "BMXBMI", "energy_kcal",
    ] + features

    summary = sample.groupby("profile")[columns].median().round(2)
    print("\nObserved medians:")
    print(summary.T.to_string())

    print("\nMissing activity values by profile:")
    activity = [
        "vigorous_recreation_minutes_week",
        "moderate_recreation_minutes_week",
        "active_transport_minutes_week",
        "sedentary_minutes_day",
    ]
    print(
        sample.groupby("profile")[activity]
        .agg(lambda values: values.isna().sum())
        .T.to_string()
    )

print("\nExploratory, unweighted summaries; profile IDs have no ranking.")