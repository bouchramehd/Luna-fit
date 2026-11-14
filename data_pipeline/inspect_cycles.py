from pathlib import Path
import json
import pyreadstat

root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

for component in config["initial_components"]:
    columns_by_cycle = {}

    for cycle in config["cycles"]:
        name = f"{component}_{cycle['suffix']}.xpt"
        path = root / "data/bronze" / cycle["label"] / name
        _, metadata = pyreadstat.read_xport(
            str(path), metadataonly=True
        )
        columns_by_cycle[cycle["label"]] = set(metadata.column_names)

    common = set.intersection(*columns_by_cycle.values())
    all_columns = set.union(*columns_by_cycle.values())

    print(f"\n{component}: {len(common)} shared columns")
    for cycle, columns in columns_by_cycle.items():
        missing = sorted(all_columns - columns)
        print(
            f"  {cycle}: {len(columns)} columns; "
            f"absent: {', '.join(missing) or 'none'}"
        )