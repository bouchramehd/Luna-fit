from pathlib import Path
import gc
import time

import numpy as np
import pandas as pd
import torch

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from tabpfn import TabPFNRegressor

root = Path(__file__).resolve().parents[1]
output = root / "reports/tabpfn_ensemble_tuning_v1.csv"

if output.exists():
    raise FileExistsError(f"Report already exists: {output}")

data = pd.read_parquet(
    root / "data/gold/hemoglobin_development_v2/data.parquet"
)

features = [
    "RIDAGEYR",
    "energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "iron_mg",
    "BMXBMI", "BMXWAIST",
    "vigorous_recreation_minutes_week",
    "had_period_past_12_months",
    "had_hysterectomy", "both_ovaries_removed",
    "ever_birth_control_pills", "ever_female_hormones",
    "menarche_age_capped20", "menarche_not_started",
]

train = data[data.survey_cycle.eq("2011-2012")].copy()
tuning = data[data.survey_cycle.eq("2013-2014")].copy()

X_train = train[features].astype(float)
X_tuning = tuning[features].astype(float)
results = []

for estimators in (1, 4):
    print(f"\nTesting {estimators} estimator(s)...", flush=True)
    started = time.perf_counter()

    model = TabPFNRegressor(
        device="cuda",
        n_estimators=estimators,
        auto_scale_n_estimators=False,
        fit_mode="low_memory",
        memory_saving_mode=True,
        keep_cache_on_device=False,
        random_state=42,
    )
    model.fit(X_train, train.LBXHGB)

    batches = []
    for start in range(0, len(tuning), 32):
        batch = X_tuning.iloc[start:start + 32]
        batches.append(
            np.asarray(model.predict(batch)).reshape(-1)
        )

        if (start // 32 + 1) % 20 == 0:
            print(
                f"  Predicted {min(start + 32, len(tuning))}"
                f"/{len(tuning)}",
                flush=True,
            )

    predictions = np.concatenate(batches)
    assert np.isfinite(predictions).all()

    row = {
        "estimators": estimators,
        "seconds": time.perf_counter() - started,
    }

    for prefix, weights in [
        ("unweighted", None),
        ("weighted", tuning.WTDRD1.to_numpy()),
    ]:
        row[f"{prefix}_MAE"] = mean_absolute_error(
            tuning.LBXHGB, predictions, sample_weight=weights
        )
        row[f"{prefix}_RMSE"] = mean_squared_error(
            tuning.LBXHGB, predictions, sample_weight=weights
        ) ** 0.5
        row[f"{prefix}_R2"] = r2_score(
            tuning.LBXHGB, predictions, sample_weight=weights
        )

    results.append(row)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(output, index=False)

    del model
    gc.collect()
    torch.cuda.empty_cache()

print(pd.DataFrame(results).round(4).to_string(index=False))
print("\nTuning experiment only; 2015-2018 excluded.")