"""Explore the historical pinhook CSVs with Python's standard library.

Run from the repository root:
    python explore_dataset.py
    python explore_dataset.py --year 2024 --limit 10
    python explore_dataset.py --sale KEESEP24 --hip 1956

Point --data-dir at a different extracted archive if needed.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


COHORT_FILE = "cohort_2022_2024_yearlings_to_2023_2025_juveniles_by_purchase.csv"
SUMMARY_FILE = "coverage_summary_three_cohorts.csv"


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def money(value):
    return f"${float(value):,.0f}" if value else "—"


def find_data_dir(explicit):
    if explicit:
        return explicit
    here = Path(__file__).resolve().parent
    for candidate in (here / "work", here / "expanded_dataset" / "work"):
        if (candidate / COHORT_FILE).is_file():
            return candidate
    return here / "work"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, help="Directory containing the extracted work CSVs")
    parser.add_argument("--year", type=int, choices=(2022, 2023, 2024), help="Yearling sale year")
    parser.add_argument("--sale", help="Yearling sale code, for example KEESEP24")
    parser.add_argument("--hip", help="Yearling hip number; use with --sale")
    parser.add_argument("--limit", type=int, default=5, help="Number of sample purchases (default: 5)")
    args = parser.parse_args()
    if args.hip and not args.sale:
        parser.error("--hip requires --sale")
    if args.limit < 0:
        parser.error("--limit must be zero or greater")

    data_dir = find_data_dir(args.data_dir)
    cohort_path = data_dir / COHORT_FILE
    summary_path = data_dir / SUMMARY_FILE
    if not cohort_path.is_file() or not summary_path.is_file():
        parser.error(f"Missing dataset in {data_dir}. Unzip the dataset into the repo, or pass --data-dir PATH/to/work")

    cohort = read_rows(cohort_path)
    coverage = read_rows(summary_path)
    if args.year:
        cohort = [r for r in cohort if r["yearling_sale_code"].endswith(str(args.year)[-2:])]
        coverage = [r for r in coverage if r["cohort"].startswith(str(args.year) + "_")]
    if args.sale:
        code = args.sale.upper()
        cohort = [r for r in cohort if r["yearling_sale_code"] == code]
        coverage = [r for r in coverage if r["sale_code"] == code]
    if args.hip:
        cohort = [r for r in cohort if r["yearling_hip"] == args.hip]

    if not cohort:
        print("No sold yearling purchase rows found for these filters.")
        return

    print(f"Data: {data_dir.resolve()}")
    print(f"Sold yearling purchases: {len(cohort):,}")
    print(f"Purchases with juvenile candidates: {sum(int(r['candidate_event_count'] or 0) > 0 for r in cohort):,}")
    print("Outcomes in covered sales:")
    for outcome, count in Counter(r["outcome_in_covered_sales"] for r in cohort).most_common():
        print(f"  {outcome}: {count:,}")

    if coverage:
        print("\nSale coverage (entries / sold purchases / purchases with candidate):")
        for row in coverage:
            print(f"  {row['cohort']} {row['sale_code']}: {row['entries']} / {row['sold_purchases']} / {row['purchases_with_candidate']}")

    print(f"\nPurchase rows (showing up to {args.limit}):")
    for row in cohort[: args.limit]:
        print(f"  {row['yearling_sale_code']} hip {row['yearling_hip']}: {money(row['yearling_price_usd'])} yearling; "
              f"{row['outcome_in_covered_sales']}; {row['candidate_event_count']} candidate event(s)")
        if "multiple_juvenile_events" in row:
            print(f"    multiple juvenile events={row['multiple_juvenile_events']}; "
                  f"competing yearling candidates={row['competing_yearling_candidates']}; "
                  f"conflicting birth dates={row['conflicting_candidate_foaling_dates']}")
        events = json.loads(row["juvenile_events_json"] or "[]")
        for event in events:
            print("    juvenile event: " + json.dumps(event, ensure_ascii=False, sort_keys=True))
        if row["first_sold_juvenile_price_usd"]:
            print(f"    first sold juvenile: {money(row['first_sold_juvenile_price_usd'])}; "
                  f"gross appreciation {money(row['appreciation_usd'])}")

    if args.hip:
        print("\nIdentity candidate evidence:")
        found = []
        for path in sorted(data_dir.glob("*candidates.csv")):
            # Some archives include old pilot audits; de-duplicate by the sale/hip pair.
            if "five_yearling" not in path.name:
                continue
            for row in read_rows(path):
                if row["yearling_sale_code"] == args.sale.upper() and row["yearling_hip"] == args.hip:
                    found.append(row)
        seen = set()
        for row in found:
            key = (row["juvenile_sale_code"], row["juvenile_hip"])
            if key in seen:
                continue
            seen.add(key)
            flags = (f"multiple events={row['multiple_juvenile_events']}, "
                     f"competing yearlings={row['competing_yearling_candidates']}") if "multiple_juvenile_events" in row else f"legacy collision={row['collision']}"
            print(f"  {key[0]} hip {key[1]}: {row['basis']}, decision={row['decision']}, {flags}")
            print("    " + json.dumps(json.loads(row["evidence_json"]), ensure_ascii=False))
        if not seen:
            print("  None in the supplied candidate files")

    print("\nCandidate identities are unconfirmed; no entry identified means only no match in the covered juvenile sales.")


if __name__ == "__main__":
    main()
