"""Build one yearling-to-next-year juvenile cohort from normalized sale CSVs.

Example:
  python -m pinhook.build_cohort_year --year 2023 --yearlings work/kee_sep23_full.csv work/ft_ky_oct23_full.csv --juveniles work/obs_march24_full.csv work/obs_spring24_full.csv work/obs_june24_full.csv work/ft_may24_full.csv --output-dir work/cohort_2023
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import ENTRY_FIELDS, MATCH_FIELDS, read_csv, validate_entries, write_csv
from .match_audit import audit
from .multi_sale_cohort import FIELDS, build


def generate(year, yearling_files, juvenile_files, output_dir):
    ys = sum((read_csv(p) for p in yearling_files), [])
    js = sum((read_csv(p) for p in juvenile_files), [])
    if not ys or not js:
        raise ValueError('Both sale sides must have entries')
    validate_entries(ys)
    validate_entries(js)
    if any(r['sale_year'] != str(year) or r['sale_type'] != 'yearling' for r in ys):
        raise ValueError('Yearling sale year/type does not match --year')
    if any(r['sale_year'] != str(year + 1) or r['sale_type'] != 'juvenile' for r in js):
        raise ValueError('Juvenile sale year/type does not match --year + 1')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pairs, metrics = audit(ys, js)
    cohort = []
    summary = []
    for sale in sorted({r['sale_code'] for r in ys}):
        subset = [r for r in ys if r['sale_code'] == sale]
        sale_pairs = [p for p in pairs if p['yearling_sale_code'] == sale]
        rows = build(subset, js, sale_pairs)
        cohort.extend(rows)
        counts = Counter(r['outcome_in_covered_sales'] for r in rows)
        summary.append(dict(cohort=f'{year}_to_{year+1}', sale_code=sale, entries=len(subset),
            sold_purchases=len(rows), purchases_with_candidate=sum(int(r['candidate_event_count']) > 0 for r in rows),
            candidate_pairs=len(sale_pairs), exact_dob_pairs=sum(p['basis'] == 'pedigree_dob_sex' for p in sale_pairs),
            sold_juvenile_candidates=counts['sold_at_2yo'], rna_juvenile_candidates=counts['rna_at_2yo'],
            out_juvenile_candidates=counts['out_at_2yo'], no_entry_in_covered_sales=counts['no_entry_identified_in_covered_sales']))
    write_csv(output_dir / 'yearling_entries.csv', ys, ENTRY_FIELDS)
    write_csv(output_dir / 'juvenile_entries.csv', js, ENTRY_FIELDS)
    write_csv(output_dir / 'identity_candidates.csv', pairs, MATCH_FIELDS)
    write_csv(output_dir / 'cohort_by_purchase.csv', cohort, FIELDS)
    write_csv(output_dir / 'coverage_summary.csv', summary, list(summary[0]))
    (output_dir / 'audit_metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    return metrics, summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--year', type=int, required=True)
    p.add_argument('--yearlings', nargs='+', required=True)
    p.add_argument('--juveniles', nargs='+', required=True)
    p.add_argument('--output-dir', required=True)
    a = p.parse_args()
    metrics, summary = generate(a.year, a.yearlings, a.juveniles, a.output_dir)
    print(f'{metrics["yearling_entries_supplied"]} yearling and {metrics["juvenile_entries_supplied"]} juvenile entries; {metrics["candidate_pairs"]} review candidates')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
