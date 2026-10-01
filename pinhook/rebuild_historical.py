"""Rebuild the three-year historical cohort from normalized sale-entry CSVs.

Run from the repository root: python -m pinhook.rebuild_historical --work-dir work
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .build_cohort_year import generate
from .core import MATCH_FIELDS, read_csv, write_csv
from .multi_sale_cohort import FIELDS


def rebuild(work):
    work = Path(work)
    combined, coverage = [], []
    for year in (2022, 2023, 2024):
        y2 = str(year)[-2:]
        j2 = str(year + 1)[-2:]
        yearlings = [work / f'{stem}{y2}_full.csv' for stem in
                     ('kee_sep', 'ft_ky_oct', 'ft_saratoga', 'ft_nybred', 'ft_july')]
        juveniles = [work / f'{stem}{j2}_full.csv' for stem in
                     ('obs_march', 'obs_spring', 'obs_june')]
        juveniles.append(work / (f'ft_may{j2}_results_full.csv' if year == 2024 else f'ft_may{j2}_full.csv'))
        output = work / f'_rebuild_{year}'
        metrics, summary = generate(year, yearlings, juveniles, output)
        pairs = read_csv(output / 'identity_candidates.csv')
        rows = read_csv(output / 'cohort_by_purchase.csv')
        shutil.copyfile(output / 'yearling_entries.csv', work / f'yearling_{year}_five_sales.csv')
        shutil.copyfile(output / 'juvenile_entries.csv', work / f'juvenile_{year+1}_four_sales.csv')
        prefix = f'five_yearling{y2}_four_juvenile{j2}' if year < 2024 else 'five_yearling_four_juvenile'
        write_csv(work / f'{prefix}_candidates.csv', pairs, MATCH_FIELDS)
        (work / f'{prefix}_metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
        write_csv(work / f'cohort_{year}_to_{year+1}_by_purchase.csv', rows, FIELDS)
        combined.extend(rows)
        for r in summary:
            r['basis'] = (f"pedigree_dob_sex:{r['exact_dob_pairs']}" if r['exact_dob_pairs']
                          else f"pedigree_year:{r['candidate_pairs']}")
        coverage.extend(summary)
        print(f'{year}: {len(rows):,} sold purchases; '
              f'{sum(int(r["candidate_event_count"]) > 0 for r in rows):,} with candidates')
    write_csv(work / 'cohort_2022_2024_yearlings_to_2023_2025_juveniles_by_purchase.csv', combined, FIELDS)
    fields = ['cohort', 'sale_code', 'entries', 'sold_purchases', 'purchases_with_candidate',
              'candidate_pairs', 'basis', 'sold_juvenile_candidates', 'rna_juvenile_candidates',
              'out_juvenile_candidates', 'no_entry_in_covered_sales', 'exact_dob_pairs']
    write_csv(work / 'coverage_summary_three_cohorts.csv', coverage, fields)
    print(f'Total: {len(combined):,} sold yearling purchases')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, default=Path('work'))
    args = parser.parse_args()
    rebuild(args.work_dir)


if __name__ == '__main__':
    main()
