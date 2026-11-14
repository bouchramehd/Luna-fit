from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)
data = pd.read_parquet(
    root / "data/gold/hemoglobin_research_v1/data.parquet"
)

features = [
    "RIDAGEYR",
    "energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "iron_mg",
    "BMXBMI", "BMXWAIST",
    "vigorous_recreation_minutes_week",
    "had_period_past_12_months",
    "self_reported_pregnant",
]

print("Missing feature values:")
print(data[features].isna().sum().to_string())

print("\nDietary weights by cycle:")
for cycle, group in data.groupby("survey_cycle"):
    valid = group.WTDRD1.notna() & group.WTDRD1.gt(0)
    print(f"{cycle}: {valid.sum()}/{len(group)} positive, nonmissing")

print("\nHemoglobin detection flags in source CBC:")
for cycle in config["cycles"]:
    name = f"CBC_{cycle['suffix']}"
    labs = pd.read_parquet(
        root / "data/silver" / cycle["label"] / name / "data.parquet"
    )

    if "LBDHGBLC" not in labs.columns:
        print(f"{cycle['label']}: flag not provided")
        continue

    ids = data.loc[
        data.survey_cycle.eq(cycle["label"]), ["SEQN"]
    ]
    matched = ids.merge(
        labs[["SEQN", "LBDHGBLC"]],
        on="SEQN",
        how="left",
        validate="one_to_one",
    )
    print(
        cycle["label"],
        matched.LBDHGBLC.value_counts(dropna=False).to_dict(),
    )

assert not data.duplicated(["survey_cycle", "SEQN"]).any()
assert data.LBXHGB.notna().all()
print("\nPASS: research participant keys and target completeness")