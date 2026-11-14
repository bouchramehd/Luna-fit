from pathlib import Path
from html.parser import HTMLParser
import json
import re


class Narratives(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading = False
        self.title = []
        self.current = None
        self.sections = {}

    def handle_starttag(self, tag, attrs):
        if tag == "h2":
            self.heading = True
            self.title = []
            self.current = None

    def handle_endtag(self, tag):
        if tag == "h2":
            self.heading = False
            self.current = " ".join(self.title).strip()
            self.sections.setdefault(self.current, [])

    def handle_data(self, data):
        if self.heading:
            self.title.append(data)
        elif self.current:
            self.sections[self.current].append(data)


root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text()
)
report = []

for cycle in config["cycles"]:
    path = (
        root / "data/bronze" / cycle["label"] / "codebooks"
        / f"CBC_{cycle['suffix']}.htm"
    )
    parser = Narratives()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))

    report.append(f"\n=== {cycle['label']} ===")
    found = False

    for title, parts in parser.sections.items():
        if "method" in title.lower() or "analytic" in title.lower():
            text = re.sub(r"\s+", " ", " ".join(parts)).strip()
            report.append(f"\n{title}\n{text}")
            found = True

    if not found:
        report.append("Sections not detected; inspect the HTML manually.")

output = root / "lab_methods.txt"
output.write_text("\n".join(report), encoding="utf-8")
print(f"Saved: {output}")