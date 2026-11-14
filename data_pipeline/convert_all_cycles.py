from pathlib import Path
import json
import pandas as pd
import pyreadstat

root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

for cycle in config["cycles"]:
    for component in config["initial_components"]:
        name = f"{component}_{cycle['suffix']}"
        source = root / "data/bronze" / cycle["label"] / f"{name}.xpt"
        folder = root / "data/silver" / cycle["label"] / name
        target = folder / "data.parquet"
        metadata_path = folder / "metadata.json"

        if target.exists() and metadata_path.exists():
            saved = json.loads(metadata_path.read_text(encoding="utf-8"))
            rows = len(pd.read_parquet(target, columns=["SEQN"]))
            assert rows == saved["rows"], f"Row mismatch: {name}"
            print(f"KEEP: {cycle['label']}/{name}: {rows:,} rows")
            continue

        if target.exists() or metadata_path.exists():
            raise RuntimeError(f"Incomplete output: {folder}")

        frame, metadata = pyreadstat.read_xport(
            str(source),
            disable_datetime_conversion=True,
        )

        original_columns = list(frame.columns)
        assert "survey_cycle" not in original_columns
        assert frame.SEQN.notna().all(), f"Missing SEQN: {name}"

        if component != "DR1IFF":
            assert frame.SEQN.is_unique, f"Duplicate SEQN: {name}"

        frame["survey_cycle"] = cycle["label"]
        folder.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(target, index=False)

        metadata_path.write_text(
            json.dumps(
                {
                    "source": source.relative_to(root).as_posix(),
                    "survey_cycle": cycle["label"],
                    "rows": len(frame),
                    "original_columns": original_columns,
                    "column_labels": metadata.column_names_to_labels,
                    "original_variable_types": metadata.original_variable_types,
                    "note": (
                        "All records and columns preserved. "
                        "SAS dates/times retained numerically. "
                        "No cross-cycle harmonization applied."
                    ),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        print(f"SAVED: {cycle['label']}/{name}: {len(frame):,} rows")