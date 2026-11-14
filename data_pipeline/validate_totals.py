from pathlib import Path

import pandas as pd
import pyreadstat

root = Path(__file__).resolve().parents[1]

totals, _ = pyreadstat.read_xport(
    str(root / "data/bronze/2015-2016/DR1TOT_I.xpt"),
    disable_datetime_conversion=True,
)
gold = pd.read_parquet(root / "data/gold/2015-2016/participants")

assert totals.SEQN.is_unique
joined = gold.merge(
    totals,
    on="SEQN",
    how="left",
    validate="one_to_one",
    suffixes=("", "_official"),
    indicator=True,
)

reliable = joined[
    joined.reliable_day1_recall
    & joined.DR1DRSTZ.eq(1)
    & joined["_merge"].eq("both")
]

assert len(reliable) == gold.reliable_day1_recall.sum(), (
    "Some reliable recalls lack matching reliable official totals"
)

pairs = {
    "energy_kcal": "DR1TKCAL",
    "protein_g": "DR1TPROT",
    "carbohydrate_g": "DR1TCARB",
    "fat_g": "DR1TTFAT",
    "iron_mg": "DR1TIRON",
}

print(f"Comparing {len(reliable)} reliable recalls")
for calculated, official in pairs.items():
    difference = (reliable[calculated] - reliable[official]).abs()
    missing = difference.isna().sum()
    # Small differences can result from food-level rounding.
    print(
        f"{calculated}: missing={missing}, "
        f"mean difference={difference.mean():.4f}, "
        f"max difference={difference.max():.4f}"
    )