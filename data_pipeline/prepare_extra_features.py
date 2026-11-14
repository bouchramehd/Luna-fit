from pathlib import Path
import json
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
output = root / "data/gold/hemoglobin_development_v2"

if output.exists():
    raise FileExistsError(f"Output already exists: {output}")

config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)
research = pd.read_parquet(
    root / "data/gold/hemoglobin_research_v1/data.parquet"
)

parts = []

for cycle in config["cycles"]:
    label = cycle["label"]
    if label == "2017-2018":
        continue

    sample = research[
        research.survey_cycle.eq(label)
        & research.RIDAGEYR.ge(20)
    ].copy()

    folder = (
        root / "data/silver" / label
        / f"RHQ_{cycle['suffix']}"
    )
    columns = ["RHQ010", "RHD280", "RHQ305", "RHQ420", "RHQ540"]
    rhq = pd.read_parquet(
        folder / "data.parquet",
        columns=["survey_cycle", "SEQN"] + columns,
    )

    sample = sample.merge(
        rhq,
        on=["survey_cycle", "SEQN"],
        how="left",
        validate="one_to_one",
    )

    mappings = {
        "RHD280": "had_hysterectomy",
        "RHQ305": "both_ovaries_removed",
        "RHQ420": "ever_birth_control_pills",
        "RHQ540": "ever_female_hormones",
    }

    for source, feature in mappings.items():
        sample[feature] = sample[source].map({1: 1.0, 2: 0.0})

    age = sample.RHQ010
    valid_age = (
        age.gt(0)
        & age.le(120)
        & age.le(sample.RIDAGEYR)
        & age.eq(age.round())
    )

    sample["menarche_age_capped20"] = (
        age.where(valid_age).clip(upper=20)
    )
    sample["menarche_not_started"] = np.where(
        age.eq(0), 1.0,
        np.where(valid_age, 0.0, np.nan),
    )

    parts.append(sample)

development = pd.concat(parts, ignore_index=True)
assert not development.duplicated(["survey_cycle", "SEQN"]).any()
assert development.RIDAGEYR.ge(20).all()

output.mkdir(parents=True)
development.to_parquet(output / "data.parquet", index=False)

(output / "notes.json").write_text(
    json.dumps({
        "minimum_age": 20,
        "cycles": ["2011-2012", "2013-2014", "2015-2016"],
        "menarche": (
            "Positive ages capped at 20 across cycles; "
            "zero represented separately as not started; "
            "refused, unknown and invalid ages remain missing."
        ),
        "binary_features": "1=yes, 0=no; all other responses missing",
        "hysterectomy_caveat": (
            "2011-2012 explicitly mentions partial hysterectomy; "
            "later wording omits that phrase."
        ),
        "hormone_caveat": "Ever-use responses do not establish current use",
        "test_cycle_used": False,
    }, indent=2),
    encoding="utf-8",
)

features = list(mappings.values()) + [
    "menarche_age_capped20", "menarche_not_started"
]

print("Participants by cycle:")
print(development.groupby("survey_cycle").size().to_string())
print("\nMissing derived features:")
print(development[features].isna().sum().to_string())
print("\nPASS: development features saved; 2017-2018 excluded.")