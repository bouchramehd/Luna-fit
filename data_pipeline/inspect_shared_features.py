from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

for component in ("BMX", "PAQ", "RHQ"):
    records = []

    for cycle in config["cycles"]:
        name = f"{component}_{cycle['suffix']}"
        path = (
            root / "data/silver" / cycle["label"]
            / name / "metadata.json"
        )
        records.append((
            cycle["label"],
            json.loads(path.read_text(encoding="utf-8")),
        ))

    shared = set.intersection(*[
        set(metadata["original_columns"])
        for _, metadata in records
    ])

    print(f"\n=== {component}: shared variable labels ===")
    for column in sorted(shared - {"SEQN"}):
        print(column)
        for cycle, metadata in records:
            label = metadata["column_labels"].get(column)
            print(f"  {cycle}: {label}")