from pathlib import Path
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

root = Path(__file__).resolve().parents[1]
output = root / "reports/hemoglobin_sensitivity_v1.csv"

if output.exists():
    raise FileExistsError(f"Report already exists: {output}")

data = pd.read_parquet(
    root / "data/gold/hemoglobin_research_v1/data.parquet"
)

base = [
    "RIDAGEYR",
    "energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "iron_mg",
    "BMXBMI", "BMXWAIST",
    "vigorous_recreation_minutes_week",
]

results = []

for scope, cycles in [
    ("2011-2014", ["2011-2012", "2013-2014"]),
    ("2013-2014_only", ["2013-2014"]),
]:
    for sample in ["all", "known_period_history"]:
        train = data[data.survey_cycle.isin(cycles)].copy()
        validation = data[data.survey_cycle.eq("2015-2016")].copy()

        if sample == "known_period_history":
            train = train[train.had_period_past_12_months.notna()]
            validation = validation[
                validation.had_period_past_12_months.notna()
            ]

        for include_period in [False, True]:
            features = base + (
                ["had_period_past_12_months"] if include_period else []
            )

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

            predictions = model.predict(
                validation[features].astype(float)
            )
            weights = validation.WTDRD1.to_numpy()

            results.append({
                "training_cycles": scope,
                "sample": sample,
                "period_feature": include_period,
                "train_rows": len(train),
                "validation_rows": len(validation),
                "weighted_MAE": mean_absolute_error(
                    validation.LBXHGB, predictions,
                    sample_weight=weights,
                ),
                "weighted_RMSE": mean_squared_error(
                    validation.LBXHGB, predictions,
                    sample_weight=weights,
                ) ** 0.5,
                "weighted_R2": r2_score(
                    validation.LBXHGB, predictions,
                    sample_weight=weights,
                ),
            })

report = pd.DataFrame(results)
output.parent.mkdir(parents=True, exist_ok=True)
report.to_csv(output, index=False)

print(report.round(4).to_string(index=False))
print("\n2017-2018 remains untouched.")