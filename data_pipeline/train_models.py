from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

root = Path(__file__).resolve().parents[1]
output = root / "artifacts/hemoglobin_experiment_v1"

if output.exists():
    raise FileExistsError(f"Experiment already exists: {output}")

data = pd.read_parquet(
    root / "data/gold/hemoglobin_research_v1/data.parquet"
)

base_features = [
    "RIDAGEYR",
    "energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "iron_mg",
    "BMXBMI", "BMXWAIST",
    "vigorous_recreation_minutes_week",
]
extended_features = base_features + ["had_period_past_12_months"]

train = data[data.survey_cycle.isin(["2011-2012", "2013-2014"])].copy()
validation = data[data.survey_cycle.eq("2015-2016")].copy()

assert len(train) == 5151
assert len(validation) == 2593

def inputs(frame, columns):
    # True/False become 1/0; unknown responses remain missing.
    return frame[columns].astype(float).replace(
        [np.inf, -np.inf], np.nan
    )

def make_model(kind):
    if kind == "baseline":
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", DummyRegressor(strategy="mean")),
        ])

    if kind == "ridge":
        return Pipeline([
            ("imputer", SimpleImputer(
                strategy="median", add_indicator=True
            )),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=10.0)),
        ])

    return Pipeline([
        ("imputer", SimpleImputer(
            strategy="median", add_indicator=True
        )),
        ("model", HistGradientBoostingRegressor(
            max_iter=150,
            max_depth=3,
            learning_rate=0.05,
            min_samples_leaf=30,
            early_stopping=False,
            random_state=42,
        )),
    ])

experiments = [
    ("baseline", "baseline", base_features),
    ("ridge_base", "ridge", base_features),
    ("ridge_period", "ridge", extended_features),
    ("boosting_base", "boosting", base_features),
    ("boosting_period", "boosting", extended_features),
]

output.mkdir(parents=True)
results = []

# Relative dietary weights for this dietary-linked exploratory sample.
# These do not provide design-based uncertainty or correct item nonresponse.
training_weights = train.WTDRD1 / train.WTDRD1.mean()

for name, kind, features in experiments:
    model = make_model(kind)
    model.fit(
        inputs(train, features),
        train.LBXHGB,
        model__sample_weight=training_weights.to_numpy(),
    )

    predictions = model.predict(inputs(validation, features))

    row = {"model": name}
    for prefix, weights in [
        ("unweighted", None),
        ("weighted", validation.WTDRD1.to_numpy()),
    ]:
        row[f"{prefix}_MAE"] = mean_absolute_error(
            validation.LBXHGB, predictions, sample_weight=weights
        )
        row[f"{prefix}_RMSE"] = np.sqrt(mean_squared_error(
            validation.LBXHGB, predictions, sample_weight=weights
        ))
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
            "training_cycles": ["2011-2012", "2013-2014"],
            "purpose": "Exploratory research; not a diagnosis",
        },
        output / f"{name}.joblib",
    )

report = pd.DataFrame(results)
report.to_csv(output / "validation_metrics.csv", index=False)

(output / "experiment.json").write_text(
    json.dumps({
        "training_rows": len(train),
        "validation_rows": len(validation),
        "validation_cycle": "2015-2016",
        "reserved_test_cycle": "2017-2018",
        "test_evaluated": False,
        "note": (
            "Exploratory dietary-weighted comparisons. "
            "No survey-design confidence intervals or "
            "item-nonresponse adjustments applied."
        ),
    }, indent=2),
    encoding="utf-8",
)

print(report.round(4).to_string(index=False))
print("\nSaved:", output)
print("2017-2018 test cycle was not used for fitting or evaluation.")