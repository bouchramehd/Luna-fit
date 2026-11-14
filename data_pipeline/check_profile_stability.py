from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

root = Path(__file__).resolve().parents[1]
folder = root / "artifacts/nutrition_activity_profiles_v1"
output = root / "reports/profile_resampling_stability_v1.csv"

if output.exists():
    raise FileExistsError(f"Report already exists: {output}")

data = pd.read_parquet(
    root / "data/gold/nutrition_activity_profiles_v1/women"
)
data = data[data.eligible_for_profile_analysis].copy()

reference = joblib.load(folder / "kmeans_k4.joblib")

for column in reference["nutrient_sources"]:
    data[column + "_per_1000kcal"] = (
        data[column] * 1000 / data.energy_kcal
    )

features = reference["features"]
train = data[
    data.survey_cycle.isin(["2011-2012", "2013-2014"])
]
validation = data[data.survey_cycle.eq("2015-2016")]

X_train = np.log1p(train[features].astype(float))
X_validation = np.log1p(validation[features].astype(float))
results = []

for k in (2, 4):
    saved = joblib.load(folder / f"kmeans_k{k}.joblib")
    original_labels = saved["model"].predict(
        saved["scaler"].transform(
            saved["imputer"].transform(X_validation)
        )
    )

    for repeat in range(10):
        rng = np.random.default_rng(100 + repeat)
        indices = rng.integers(0, len(train), size=len(train))
        bootstrap = X_train.iloc[indices]

        # Refit every preprocessing step on the resampled training data.
        imputer = SimpleImputer(strategy="median")
        scaler = StandardScaler()
        transformed = scaler.fit_transform(
            imputer.fit_transform(bootstrap)
        )

        model = KMeans(
            n_clusters=k, n_init=20, random_state=42
        ).fit(transformed)

        labels = model.predict(
            scaler.transform(imputer.transform(X_validation))
        )

        results.append({
            "clusters": k,
            "repeat": repeat + 1,
            "ARI": adjusted_rand_score(original_labels, labels),
        })

    print(f"Completed k={k}", flush=True)

report = pd.DataFrame(results)
output.parent.mkdir(parents=True, exist_ok=True)
report.to_csv(output, index=False)

print(
    report.groupby("clusters").ARI.agg(
        ["mean", "min", "max"]
    ).round(4).to_string()
)
print(
    "\nExploratory participant-resampling stability, "
    "not survey-design uncertainty or evidence of health benefit."
)