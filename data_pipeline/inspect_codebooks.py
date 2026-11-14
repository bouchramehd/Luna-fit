from pathlib import Path
from html.parser import HTMLParser
import json
import re


class Sections(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = {}
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "h3":
            self.current = dict(attrs).get("id")
            if self.current:
                self.sections.setdefault(self.current, [])

    def handle_data(self, data):
        if self.current:
            self.sections[self.current].append(data)


root = Path(__file__).resolve().parents[1]

config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

variables = [
    ("PAQ", "PAQ665"),
    ("PAQ", "PAQ670"),
    ("PAQ", "PAD675"),
    ("PAQ", "PAQ635"),
    ("PAQ", "PAQ640"),
    ("PAQ", "PAD645"),
    ("PAQ", "PAD680"),
   
]

report = []

for component, variable in variables:
    for cycle in config["cycles"]:
        if cycle["label"] == "2017-2018":
            continue

        path = (
            root
            / "data/bronze"
            / cycle["label"]
            / "codebooks"
            / f"{component}_{cycle['suffix']}.htm"
        )

        parser = Sections()
        parser.feed(
            path.read_text(encoding="utf-8", errors="replace")
        )

        if variable not in parser.sections:
            raise ValueError(
                f"Section not found: {cycle['label']}/{variable}"
            )

        text = re.sub(
            r"\s+",
            " ",
            " ".join(parser.sections[variable]),
        ).strip()

        report.append(
            f"\n{cycle['label']} — {variable}\n{text}\n"
        )

output = root / "codebook_check.txt"
output.write_text("\n".join(report), encoding="utf-8")

print(f"Report saved: {output}")
print("2017-2018 excluded.")