from pathlib import Path
import json
import subprocess
import os

root = Path(__file__).resolve().parents[1]

config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

# Full path avoids your terminal's PATH issue.
curl = str(
    Path(os.environ.get("SystemRoot", r"C:\Windows"))
    / "System32"
    / "curl.exe"
)

for cycle in config["cycles"]:
    folder = root / "data/bronze" / cycle["label"] / "codebooks"
    folder.mkdir(parents=True, exist_ok=True)

    for component in ("BMX", "PAQ", "RHQ", "CBC"):
        name = f"{component}_{cycle['suffix']}.htm"
        target = folder / name

        if target.exists():
            html = target.read_text(
                encoding="utf-8", errors="replace"
            )
            if "SEQN" not in html or "Target" not in html:
                raise ValueError(f"Invalid existing codebook: {target}")

            print(f"KEEP: {cycle['label']}/{name}")
            continue

        url = (
            "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/"
            f"{cycle['start_year']}/DataFiles/{name}"
        )
        temporary = target.with_suffix(".part")

        try:
            subprocess.run(
                [
                    curl,
                    "--fail",
                    "--location",
                    "--retry", "3",
                    "--connect-timeout", "30",
                    "--max-time", "180",
                    "--output", str(temporary),
                    url,
                ],
                check=True,
            )

            html = temporary.read_text(
                encoding="utf-8", errors="replace"
            )

            if "SEQN" not in html or "Target" not in html:
                raise ValueError(
                    f"Unexpected codebook content: {name}"
                )

            temporary.replace(target)
            print(f"SAVED: {cycle['label']}/{name}")

        finally:
            temporary.unlink(missing_ok=True)

print("Codebook downloads complete.")