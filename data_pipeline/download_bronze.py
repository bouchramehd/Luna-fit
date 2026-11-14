from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
config = json.loads(
    (ROOT / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

HEADER = b"HEADER RECORD*******LIBRARY HEADER RECORD!!!!!!!"

for cycle in config["cycles"]:
    folder = ROOT / "data/bronze" / cycle["label"]
    folder.mkdir(parents=True, exist_ok=True)

    for component in config["initial_components"]:
        name = f"{component}_{cycle['suffix']}.xpt"
        path = folder / name
        sidecar = path.with_suffix(".metadata.json")

        url = (
            "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/"
            f"{cycle['start_year']}/DataFiles/{name}"
        )
        downloaded = False

        if not path.exists():
            temporary = path.with_suffix(".part")
            print(
                f"Downloading {cycle['label']}/{name}",
                flush=True,
            )

            try:
                subprocess.run(
                    [
                        "curl.exe",
                        "--fail",
                        "--location",
                        "--retry", "3",
                        "--connect-timeout", "30",
                        "--max-time", "600",
                        "--output", str(temporary),
                        url,
                    ],
                    check=True,
                )

                with temporary.open("rb") as stream:
                    if stream.read(len(HEADER)) != HEADER:
                        raise ValueError(
                            f"Response is not a SAS XPT file: {url}"
                        )

                temporary.replace(path)
                downloaded = True

            finally:
                temporary.unlink(missing_ok=True)

        checksum = hashlib.sha256()

        with path.open("rb") as stream:
            if stream.read(len(HEADER)) != HEADER:
                raise ValueError(f"Invalid XPT file: {path}")

            stream.seek(0)

            for block in iter(
                lambda: stream.read(1024 * 1024), b""
            ):
                checksum.update(block)

        sha256 = checksum.hexdigest()

        if sidecar.exists():
            previous = json.loads(
                sidecar.read_text(encoding="utf-8")
            )

            if previous["sha256"] != sha256:
                raise ValueError(f"Checksum changed: {path}")

        else:
            metadata = {
                "survey_cycle": cycle["label"],
                "file": name,
                "expected_source_url": url,
                "sha256": sha256,
                "bytes": path.stat().st_size,
                "recorded_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "origin": (
                    "downloaded_by_script"
                    if downloaded
                    else "existing_local_file"
                ),
            }

            sidecar.write_text(
                json.dumps(metadata, indent=2),
                encoding="utf-8",
            )

        print(
            f"OK: {cycle['label']}/{name}",
            flush=True,
        )

print("Bronze downloads and checksum checks complete.")