from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)

research = pd.read_parquet(
    root / "data/gold/hemoglobin_research_v1/data.parquet",
    columns=["survey_cycle", "SEQN"],
)

candidates = {
    "DEMO": [
        "INDFMPIR",  # Family income-to-poverty ratio
        "DMDEDUC2",  # Adult education
        "RIDRETH3",  # Race/Hispanic origin
    ],
    "RHQ": [
        "RHQ010",   # Age at first period
        "RHQ060",   # Age at last period
        "RHQ200",   # Breastfeeding
        "RHD280",   # Hysterectomy
        "RHQ305",   # Both ovaries removed
        "RHQ420",   # Ever used birth-control pills
        "RHQ540",   # Ever used female hormones
    ],
}

for cycle in config["cycles"]:
    label = cycle["label"]
    if label == "2017-2018":
        continue

    ids = research.loc[research.survey_cycle.eq(label), ["SEQN"]]
    print(f"\n=== {label}: {len(ids)} research participants ===")

    for component, variables in candidates.items():
        folder = (
            root / "data/silver" / label
            / f"{component}_{cycle['suffix']}"
        )
        metadata = json.loads(
            (folder / "metadata.json").read_text(encoding="utf-8")
        )
        table = pd.read_parquet(folder / "data.parquet")

        for variable in variables:
            if variable not in table.columns:
                print(f"{variable}: unavailable")
                continue

            joined = ids.merge(
                table[["SEQN", variable]],
                on="SEQN",
                how="left",
                validate="one_to_one",
            )
            values = joined[variable]
            label_text = metadata["column_labels"].get(variable)

            print(
                f"{variable} | {label_text} | "
                f"nonmissing={values.notna().sum()}/{len(ids)}"
            )

print("\nCounts include special response codes; these are not yet cleaned.")
print("2017-2018 was excluded from this audit.")