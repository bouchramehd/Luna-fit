from pathlib import Path
import time

import numpy as np
import pandas as pd
import torch

from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from tabpfn import TabPFNRegressor

root = Path(__file__).resolve().parents[1]
output = root / "reports/tabpfn_full_development_v1.csv"

if output.exists():
    raise FileExistsError(f"Report already exists: {output}")

data = pd.read_parquet(
    root / "data/gold/hemoglobin_development_v2/data.parquet"
)

features = [
    "RIDAGEYR",
    "energy_kcal",
    "protein_g",
    "carbohydrate_g",
    "fat_g",
    "iron_mg",
    "BMXBMI",
    "BMXWAIST",
    "vigorous_recreation_minutes_week",
    "had_period_past_12_months",
    "had_hysterectomy",
    "both_ovaries_removed",
    "ever_birth_control_pills",
    "ever_female_hormones",
    "menarche_age_capped20",
    "menarche_not_started",
]

train = data[
    data.survey_cycle.isin(["2011-2012", "2013-2014"])
].copy()

validation = data[
    data.survey_cycle.eq("2015-2016")
].copy()

assert len(train) == 4880
assert len(validation) == 2484
assert not data.duplicated(["survey_cycle", "SEQN"]).any()

X_train = train[features].astype(float)
X_validation = validation[features].astype(float)

models = {
    "baseline": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", DummyRegressor(strategy="mean")),
    ]),
    "ridge": Pipeline([
        ("imputer", SimpleImputer(
            strategy="median",
            add_indicator=True,
        )),
        ("scale", StandardScaler()),
        ("model", Ridge(alpha=10.0)),
    ]),
    "tabpfn": TabPFNRegressor(
        device="cuda",
        n_estimators=1,
        auto_scale_n_estimators=False,
        fit_mode="low_memory",
        memory_saving_mode=True,
        keep_cache_on_device=False,
        random_state=42,
    ),
}

results = []

print(
    f"Training rows: {len(train)}; "
    f"validation rows: {len(validation)}",
    flush=True,
)

for name, model in models.items():
    print(f"Running {name}...", flush=True)
    started = time.perf_counter()

    # Identical unweighted training protocol for all models.
    model.fit(X_train, train.LBXHGB)

    batches = []

    for start in range(0, len(validation), 32):
        batch = X_validation.iloc[start:start + 32]
        batches.append(
            np.asarray(model.predict(batch)).reshape(-1)
        )

        if name == "tabpfn" and (
            start == 0 or (start // 32 + 1) % 10 == 0
        ):
            print(
                f"  Predicted {min(start + 32, len(validation))}"
                f"/{len(validation)} rows",
                flush=True,
            )

    predictions = np.concatenate(batches)

    assert len(predictions) == len(validation)
    assert np.isfinite(predictions).all()

    row = {
        "model": name,
        "seconds": time.perf_counter() - started,
    }

    for prefix, weights in [
        ("unweighted", None),
        ("weighted", validation.WTDRD1.to_numpy()),
    ]:
        row[f"{prefix}_MAE"] = mean_absolute_error(
            validation.LBXHGB,
            predictions,
            sample_weight=weights,
        )
        row[f"{prefix}_RMSE"] = mean_squared_error(
            validation.LBXHGB,
            predictions,
            sample_weight=weights,
        ) ** 0.5
        row[f"{prefix}_R2"] = r2_score(
            validation.LBXHGB,
            predictions,
            sample_weight=weights,
        )

    results.append(row)

    # Save completed results even if a later model fails.
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(output, index=False)

report = pd.DataFrame(results)
print(report.round(4).to_string(index=False))

print(
    "\nPeak GPU memory:",
    round(torch.cuda.max_memory_allocated() / 1024**3, 2),
    "GB",
)
print("\nSaved:", output)
print("Development comparison only; 2017-2018 was not used.")