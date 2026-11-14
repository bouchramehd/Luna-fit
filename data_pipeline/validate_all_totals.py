from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[1]
config = json.loads(
    (root / "data_pipeline/configs/cycles.json").read_text(
        encoding="utf-8"
    )
)

pairs = {
    "DR1IKCAL": "DR1TKCAL",
    "DR1IPROT": "DR1TPROT",
    "DR1ICARB": "DR1TCARB",
    "DR1ITFAT": "DR1TTFAT",
    "DR1IIRON": "DR1TIRON",
}

for cycle in config["cycles"]:
    label = cycle["label"]
    folder = root / "data/silver" / label
    suffix = cycle["suffix"]

    food = pd.read_parquet(
        folder / f"DR1IFF_{suffix}/data.parquet"
    )
    totals = pd.read_parquet(
        folder / f"DR1TOT_{suffix}/data.parquet"
    )

    reliable_food = food[food.DR1DRSTZ.eq(1)]
    official = totals[totals.DR1DRSTZ.eq(1)]

    assert reliable_food.SEQN.notna().all()
    assert official.SEQN.notna().all()
    assert official.SEQN.is_unique

    food_ids = set(reliable_food.SEQN)
    official_ids = set(official.SEQN)

    assert food_ids <= official_ids, (
        f"Reliable food recalls missing from official totals: {label}"
    )

    # Official zero-intake recalls may have no food records.
    extra = official[~official.SEQN.isin(food_ids)]
    extra_values = extra[list(pairs.values())]

    assert extra_values.notna().all().all()
    assert extra_values.eq(0).all().all(), (
        f"Nonzero official totals without reliable food rows: {label}"
    )

    print(
        f"\n{label}: {len(extra)} zero-total recalls "
        "without reliable food rows"
    )
    if not extra.empty:
        print("  Participant IDs:", extra.SEQN.astype(int).tolist())

    columns = list(pairs)
    assert not reliable_food[columns].isna().any().any(), (
        f"Missing nutrients in reliable food records: {label}"
    )

    calculated = reliable_food.groupby("SEQN")[columns].sum()
    comparison = calculated.join(
        official.set_index("SEQN")[list(pairs.values())],
        how="inner",
        validate="one_to_one",
    )

    assert len(comparison) == len(food_ids)
    assert len(comparison) > 0

    print(f"  Comparing {len(comparison):,} food-based recalls")

    for food_column, total_column in pairs.items():
        difference = (
            comparison[food_column] - comparison[total_column]
        ).abs()

        assert difference.notna().all(), (
            f"Missing comparison values: {label}/{total_column}"
        )

        maximum = difference.max()
        print(f"  {total_column}: max difference = {maximum:.6f}")

        assert maximum <= 0.01, (
            f"Totals differ: {label}/{total_column}"
        )

print(
    "\nPASS: all four cycles match within 0.01 "
    "in each nutrient's unit."
)