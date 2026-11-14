from pathlib import Path
import json

import pyreadstat

ROOT = Path(__file__).resolve().parents[1]
CYCLE = "2015-2016"

for name in ("DEMO_I", "DR1IFF_I"):
    source = ROOT / "data" / "bronze" / CYCLE / f"{name}.xpt"
    folder = ROOT / "data" / "silver" / CYCLE / name
    folder.mkdir(parents=True, exist_ok=True)

    target = folder / "data.parquet"
    metadata_path = folder / "metadata.json"

    if target.exists() or metadata_path.exists():
        raise FileExistsError(f"Output already exists in {folder}")

    # Keep SAS dates/times numeric for Spark 3.5 compatibility.
    frame, metadata = pyreadstat.read_xport(
        str(source),
        disable_datetime_conversion=True,
    )

    original_columns = list(frame.columns)

    if "survey_cycle" in frame.columns:
        raise ValueError("survey_cycle already exists")

    frame["survey_cycle"] = CYCLE
    frame.to_parquet(target, index=False)

    metadata_path.write_text(
        json.dumps(
            {
                "source": source.relative_to(ROOT).as_posix(),
                "survey_cycle": CYCLE,
                "rows": len(frame),
                "original_columns": original_columns,
                "column_labels": metadata.column_names_to_labels,
                "original_variable_types": metadata.original_variable_types,
                "note": (
                    "No filtering, aggregation, or harmonization applied. "
                    "SAS dates/times retained as numeric values; "
                    "original formats recorded in original_variable_types."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"{name}: saved {len(frame):,} rows to {target}")