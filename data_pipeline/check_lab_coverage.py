from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)
women = pd.read_parquet(root / "data/gold/multicycle_v3/women")

for cycle in config["cycles"]:
    label = cycle["label"]
    name = f"CBC_{cycle['suffix']}"

    labs = pd.read_parquet(
        root / "data/silver" / label / name / "data.parquet",
        columns=["SEQN", "LBXHGB"],
    )

    sample = women[
        women.survey_cycle.eq(label)
        & women.RIDAGEYR.ge(18)
        & women.reliable_day1_recall
    ].merge(labs, on="SEQN", how="left", validate="one_to_one")

    print(
        f"{label}: eligible={len(sample)}, "
        f"hemoglobin known={sample.LBXHGB.notna().sum()}, "
        f"period history also known="
        f"{(sample.LBXHGB.notna() & sample.had_period_past_12_months.notna()).sum()}"
    )