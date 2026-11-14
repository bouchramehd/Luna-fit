from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

root = Path(__file__).resolve().parents[1]
output = root / "reports/hemoglobin_age_effect_v1.csv"

if output.exists():
    raise FileExistsError(f"Report already exists: {output}")

data = pd.read_parquet(
    root / "data/gold/hemoglobin_development_v2/data.parquet"
)

train = data[
    data.survey_cycle.isin(["2011-2012", "2013-2014"])
].copy()
validation = data[data.survey_cycle.eq("2015-2016")].copy()

base = [
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

results = []

for age_type in ("linear", "spline"):
    for name, other_features in feature_sets.items():
        age_steps = [
            ("imputer", SimpleImputer(strategy="median")),
        ]

        if age_type == "spline":
            age_steps.append((
                "spline",
                SplineTransformer(
                    n_knots=5,
                    degree=3,
                    knots="quantile",
                    include_bias=False,
                    extrapolation="linear",
                ),
            ))

        preprocessing = ColumnTransformer([
            ("age", Pipeline(age_steps), ["RIDAGEYR"]),
            (
                "other",
                SimpleImputer(strategy="median", add_indicator=True),
                other_features,
            ),
        ])

        model = Pipeline([
            ("preprocessing", preprocessing),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=10.0)),
        ])

        features = ["RIDAGEYR"] + other_features

        # Imputation, spline knots and scaling are learned on training only.
        model.fit(
            train[features].astype(float),
            train.LBXHGB,
            model__sample_weight=(
                train.WTDRD1 / train.WTDRD1.mean()
            ).to_numpy(),
        )

        predicted = model.predict(
            validation[features].astype(float)
        )
        row = {"age_model": age_type, "features": name}

        for prefix, weights in [
            ("unweighted", None),
            ("weighted", validation.WTDRD1.to_numpy()),
        ]:
            row[f"{prefix}_MAE"] = mean_absolute_error(
                validation.LBXHGB, predicted, sample_weight=weights
            )
            row[f"{prefix}_RMSE"] = mean_squared_error(
                validation.LBXHGB, predicted, sample_weight=weights
            ) ** 0.5
            row[f"{prefix}_R2"] = r2_score(
                validation.LBXHGB, predicted, sample_weight=weights
            )

        results.append(row)

report = pd.DataFrame(results)
output.parent.mkdir(parents=True, exist_ok=True)
report.to_csv(output, index=False)

print(report.round(4).to_string(index=False))
print("\nDevelopment comparison only; 2017-2018 was not used.")