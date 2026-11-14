from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

root = Path(__file__).resolve().parents[1]
output = root / "artifacts/nutrition_activity_profiles_v1"

if output.exists():
    raise FileExistsError(f"Experiment already exists: {output}")

data = pd.read_parquet(
    root / "data/gold/nutrition_activity_profiles_v1/women"
)
data = data[data.eligible_for_profile_analysis].copy()

nutrients = ["protein_g", "carbohydrate_g", "fat_g", "iron_mg"]
nutrition_features = []

for column in nutrients:
    feature = column + "_per_1000kcal"
    data[feature] = data[column] * 1000 / data.energy_kcal
    nutrition_features.append(feature)

activity_features = [
    "vigorous_recreation_minutes_week",
    "moderate_recreation_minutes_week",
    "active_transport_minutes_week",
    "sedentary_minutes_day",
]
features = nutrition_features + activity_features

train = data[
    data.survey_cycle.isin(["2011-2012", "2013-2014"])
].copy()
validation = data[data.survey_cycle.eq("2015-2016")].copy()

def prepare(frame):
    values = frame[features].astype(float)
    assert not np.isinf(values.to_numpy()).any()
    assert not values.lt(0).any().any()
    return np.log1p(values)

# Fit preprocessing only on training participants.
imputer = SimpleImputer(strategy="median")
scaler = StandardScaler()

X_train = scaler.fit_transform(
    imputer.fit_transform(prepare(train))
)
X_validation = scaler.transform(
    imputer.transform(prepare(validation))
)

output.mkdir(parents=True)
results = []

for k in range(2, 6):
    model = KMeans(n_clusters=k, n_init=20, random_state=42)
    model.fit(X_train)
    labels = model.predict(X_validation)

    # Check sensitivity to another initialization.
    alternative = KMeans(
        n_clusters=k, n_init=20, random_state=7
    ).fit(X_train)
    alternate_labels = alternative.predict(X_validation)

    counts = pd.Series(labels).value_counts()
    unique = len(counts)

    silhouette = (
        silhouette_score(
            X_validation,
            labels,
            sample_size=min(2000, len(validation)),
            random_state=42,
        )
        if 1 < unique < len(validation)
        else np.nan
    )

    results.append({
        "clusters": k,
        "validation_silhouette": silhouette,
        "initialization_agreement_ARI": adjusted_rand_score(
            labels, alternate_labels
        ),
        "smallest_validation_cluster": int(counts.min()),
        "validation_clusters_present": unique,
    })

    joblib.dump(
        {
            "model": model,
            "imputer": imputer,
            "scaler": scaler,
            "features": features,
            "nutrient_sources": nutrients,
            "transformation": "nutrients per 1000 kcal, then log1p all features",
            "training_cycles": ["2011-2012", "2013-2014"],
            "minimum_age": 18,
            "purpose": "Exploratory nutrition/activity profiles",
        },
        output / f"kmeans_k{k}.joblib",
    )

report = pd.DataFrame(results)
report.to_csv(output / "candidate_metrics.csv", index=False)

(output / "notes.json").write_text(
    json.dumps({
        "training_rows": len(train),
        "validation_rows": len(validation),
        "validation_cycle": "2015-2016",
        "survey_weighting": "Unweighted exploratory clustering",
        "limitations": [
            "One dietary recall day does not establish usual intake",
            "Activity is self-reported",
            "Initialization agreement is not full resampling stability",
            "Cluster separation does not establish health benefit",
        ],
    }, indent=2),
    encoding="utf-8",
)

print(report.round(4).to_string(index=False))
print("\nCandidates saved; no final profile count selected yet.")