from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

output = root / "data/gold/hemoglobin_research_v1"
if output.exists():
    raise FileExistsError(f"Output already exists: {output}")

women = pd.read_parquet(root / "data/gold/multicycle_v3/women")
labs = []

for cycle in config["cycles"]:
    name = f"CBC_{cycle['suffix']}"
    table = pd.read_parquet(
        root / "data/silver" / cycle["label"] / name / "data.parquet",
        columns=["survey_cycle", "SEQN", "LBXHGB"],
    )
    labs.append(table)

labs = pd.concat(labs, ignore_index=True)
keys = ["survey_cycle", "SEQN"]

assert not labs.duplicated(keys).any()

linked = women.merge(
    labs,
    on=keys,
    how="left",
    validate="one_to_one",
)
assert len(linked) == len(women)

# Derived research subset; existing full Gold tables remain unchanged.
sample = linked.loc[
    linked.RIDAGEYR.ge(18)
    & linked.reliable_day1_recall
    & linked.LBXHGB.notna()
].copy()

assert len(sample) == 10211
assert not sample.duplicated(keys).any()

output.mkdir(parents=True)
sample.to_parquet(output / "data.parquet", index=False)

print(
    sample.groupby("survey_cycle").agg(
        participants=("SEQN", "size"),
        period_history_known=("had_period_past_12_months", "count"),
    ).to_string()
)
print("\nPASS: research table saved; target is LBXHGB in g/dL.")