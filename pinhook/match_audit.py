"""Audit cross-sale identity coverage without treating a sample as a cohort rate.

Usage:
  python -m pinhook.match_audit work/kee24.csv work/ftmay25_catalog.csv work/ft_match_audit
Inputs are normalized sale-entry CSVs. The audit never approves candidate matches.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import MATCH_FIELDS, candidates, read_csv, write_csv


def audit(yearlings, juveniles):
    pairs = candidates(yearlings, juveniles)
    by_y = Counter((p['yearling_sale_code'], p['yearling_hip']) for p in pairs)
    by_j = Counter((p['juvenile_sale_code'], p['juvenile_hip']) for p in pairs)
    yearling_lookup = {(r['sale_code'],r['hip']):r for r in yearlings}
    matched_status = Counter(yearling_lookup[k].get('status','unknown') for k in by_y)
    sold_yearlings = sum(r.get('status')=='sold' for r in yearlings)
    unique_pairs = [p for p in pairs if by_y[(p['yearling_sale_code'], p['yearling_hip'])] == 1
                    and by_j[(p['juvenile_sale_code'], p['juvenile_hip'])] == 1]
    y_codes = Counter(r['sale_code'] for r in yearlings)
    j_codes = Counter(r['sale_code'] for r in juveniles)
    metrics = {
        'yearling_entries_supplied': len(yearlings),
        'juvenile_entries_supplied': len(juveniles),
        'yearling_sale_counts': dict(y_codes),
        'juvenile_sale_counts': dict(j_codes),
        'yearling_entries_with_sire_dam_year': sum(bool(r.get('sire') and r.get('dam') and r.get('foaling_year')) for r in yearlings),
        'juvenile_entries_with_sire_dam_year': sum(bool(r.get('sire') and r.get('dam') and r.get('foaling_year')) for r in juveniles),
        'yearling_entries_with_exact_dob': sum(bool(r.get('foaling_date')) for r in yearlings),
        'juvenile_entries_with_exact_dob': sum(bool(r.get('foaling_date')) for r in juveniles),
        'candidate_pairs': len(pairs),
        'yearling_entries_with_candidate': len(by_y),
        'juvenile_entries_with_candidate': len(by_j),
        'one_to_one_candidates': len(unique_pairs),
        'yearling_entries_with_multiple_candidates': sum(n > 1 for n in by_y.values()),
        'juvenile_entries_with_multiple_candidates': sum(n > 1 for n in by_j.values()),
        'yearling_entries_with_multiple_juvenile_events': sum(n > 1 for n in by_y.values()),
        'juvenile_entries_with_competing_yearling_candidates': sum(n > 1 for n in by_j.values()),
        'candidate_basis_counts': dict(Counter(p['basis'] for p in pairs)),
        'yearling_candidate_status_counts': dict(matched_status),
        'sold_yearling_entries_supplied': sold_yearlings,
        'sold_yearling_entries_with_candidate': matched_status['sold'],
        'candidate_coverage_of_sold_yearlings_pct': round(100 * matched_status['sold'] / sold_yearlings,2) if sold_yearlings else None,
        'candidate_coverage_of_supplied_yearlings_pct': round(100 * len(by_y) / len(yearlings), 2) if yearlings else None,
        'candidate_coverage_of_supplied_juveniles_pct': round(100 * len(by_j) / len(juveniles), 2) if juveniles else None,
        'interpretation': 'Unreviewed identity candidates among supplied entries only. Catalog-only juvenile coverage and incomplete sale coverage are not a true pinhook outcome rate.',
    }
    return pairs, metrics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('yearlings', help='Normalized yearling sale entries CSV')
    p.add_argument('juveniles', help='Normalized juvenile sale entries CSV')
    p.add_argument('output_prefix', help='Writes _candidates.csv and _metrics.json')
    a = p.parse_args()
    pairs, metrics = audit(read_csv(a.yearlings), read_csv(a.juveniles))
    prefix = Path(a.output_prefix)
    write_csv(str(prefix) + '_candidates.csv', pairs, MATCH_FIELDS)
    Path(str(prefix) + '_metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
