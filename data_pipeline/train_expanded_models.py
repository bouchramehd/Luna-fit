from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

root = Path(__file__).resolve().parents[1]
output = root / "artifacts/hemoglobin_expanded_v1"

if output.exists():
    raise FileExistsError(f"Experiment already exists: {output}")

data = pd.read_parquet(
    root / "data/gold/hemoglobin_development_v2/data.parquet"
)

train = data[
    data.survey_cycle.isin(["2011-2012", "2013-2014"])
].copy()
validation = data[data.survey_cycle.eq("2015-2016")].copy()

base = [
    "RIDAGEYR",
    "energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "iron_mg",
    "BMXBMI", "BMXWAIST",
    "vigorous_recreation_minutes_week",
]

feature_sets = {
    "base": base,
    "period": base + ["had_period_past_12_months"],
    "expanded": base + [
        "had_period_past_12_months",
        "had_hysterectomy",
        "both_ovaries_removed",
        "ever_birth_control_pills",
        "ever_female_hormones",
        "menarche_age_capped20",
        "menarche_not_started",
    ],
}

experiments = [("baseline", "base")]
experiments += [
    (kind, features)
    for kind in ("ridge", "boosting")
    for features in feature_sets
]

output.mkdir(parents=True)
results = []

for kind, feature_set in experiments:
    features = feature_sets[feature_set]

    if kind == "baseline":
        estimator = DummyRegressor(strategy="mean")
    elif kind == "ridge":
        estimator = Ridge(alpha=10.0)
    else:
        estimator = HistGradientBoostingRegressor(
            max_iter=150,
            max_depth=3,
            learning_rate=0.05,
            min_samples_leaf=30,
            early_stopping=False,
            random_state=42,
        )

    steps = [
        ("imputer", SimpleImputer(
            strategy="median", add_indicator=True
        )),
    ]
    if kind == "ridge":
        steps.append(("scale", StandardScaler()))
    steps.append(("model", estimator))

    model = Pipeline(steps)
    model.fit(
        train[features].astype(float),
        train.LBXHGB,
        model__sample_weight=(
            train.WTDRD1 / train.WTDRD1.mean()
        ).to_numpy(),
    )

    predictions = model.predict(validation[features].astype(float))
    name = f"{kind}_{feature_set}"
    row = {"model": name}

    for prefix, weights in [
        ("unweighted", None),
        ("weighted", validation.WTDRD1.to_numpy()),
    ]:
        row[f"{prefix}_MAE"] = mean_absolute_error(
            validation.LBXHGB, predictions, sample_weight=weights
        )
        row[f"{prefix}_RMSE"] = mean_squared_error(
            validation.LBXHGB, predictions, sample_weight=weights
        ) ** 0.5
        row[f"{prefix}_R2"] = r2_score(
            validation.LBXHGB, predictions, sample_weight=weights
        )

    results.append(row)
    joblib.dump(
        {
            "pipeline": model,
            "features": features,
            "target": "LBXHGB",
            "unit": "g/dL",
            "minimum_age": 20,
            "training_cycles": ["2011-2012", "2013-2014"],
            "purpose": "Exploratory research only",
        },
        output / f"{name}.joblib",
    )

report = pd.DataFrame(results)
report.to_csv(output / "validation_metrics.csv", index=False)

(output / "experiment.json").write_text(
    json.dumps({
        "train_rows": len(train),
        "validation_rows": len(validation),
        "validation_cycle": "2015-2016",
        "minimum_age": 20,
        "test_cycle_used": False,
        "note": (
            "Development comparison; 2015-2016 has been used previously. "
            "2017-2018 is not a fresh test for future redesigned models. "
            "Metrics do not include survey-design uncertainty."
        ),
    }, indent=2),
    encoding="utf-8",
)

print(report.round(4).to_string(index=False))
print("\nSaved:", output)