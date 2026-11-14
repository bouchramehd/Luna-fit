from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

root = Path(__file__).resolve().parents[1]
output = root / "artifacts/hemoglobin_final_v1"

if output.exists():
    raise FileExistsError(f"Results already exist: {output}")

data = pd.read_parquet(
    root / "data/gold/hemoglobin_research_v1/data.parquet"
)

train_cycles = ["2011-2012", "2013-2014", "2015-2016"]
train = data[data.survey_cycle.isin(train_cycles)].copy()
test = data[data.survey_cycle.eq("2017-2018")].copy()

assert len(train) == 7744
assert len(test) == 2467

base = [
    "RIDAGEYR",
    "energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "iron_mg",
    "BMXBMI", "BMXWAIST",
    "vigorous_recreation_minutes_week",
]

output.mkdir(parents=True)
results = []
predictions = test[["survey_cycle", "SEQN", "LBXHGB", "WTDRD1"]].copy()

for name in ["baseline", "ridge_base", "ridge_period"]:
    features = base + (
        ["had_period_past_12_months"]
        if name == "ridge_period" else []
    )

    if name == "baseline":
        model = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", DummyRegressor(strategy="mean")),
        ])
    else:
        model = Pipeline([
            ("imputer", SimpleImputer(
                strategy="median", add_indicator=True
            )),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=10.0)),
        ])

    model.fit(
        train[features].astype(float),
        train.LBXHGB,
        model__sample_weight=(
            train.WTDRD1 / train.WTDRD1.mean()
        ).to_numpy(),
    )

    predicted = model.predict(test[features].astype(float))
    predictions[name] = predicted
    row = {"model": name}

    for prefix, weights in [
        ("unweighted", None),
        ("weighted", test.WTDRD1.to_numpy()),
    ]:
        row[f"{prefix}_MAE"] = mean_absolute_error(
            test.LBXHGB, predicted, sample_weight=weights
        )
        row[f"{prefix}_RMSE"] = mean_squared_error(
            test.LBXHGB, predicted, sample_weight=weights
        ) ** 0.5
        row[f"{prefix}_R2"] = r2_score(
            test.LBXHGB, predicted, sample_weight=weights
        )

    results.append(row)

    joblib.dump(
        {
            "pipeline": model,
            "features": features,
            "target": "LBXHGB",
            "unit": "g/dL",
            "training_cycles": train_cycles,
            "purpose": "Research only; not a diagnosis",
        },
        output / f"{name}.joblib",
    )

report = pd.DataFrame(results)
report.to_csv(output / "test_metrics.csv", index=False)
predictions.to_parquet(output / "test_predictions.parquet", index=False)

(output / "experiment.json").write_text(
    json.dumps({
        "training_cycles": train_cycles,
        "test_cycle": "2017-2018",
        "training_rows": len(train),
        "test_rows": len(test),
        "ridge_alpha": 10.0,
        "note": (
            "Frozen temporal test comparison. Dietary weights used; "
            "no design-based confidence intervals or item-nonresponse "
            "adjustment. Do not tune models against these test results."
        ),
    }, indent=2),
    encoding="utf-8",
)

print(report.round(4).to_string(index=False))
print("\nSaved:", output)