"""Join a Keeneland catalog identity extract to official sale results by hip.

Accepted catalog rows require matching sire, dam, sex, and foaling year.
Conflicts are quarantined; the official result status and price remain intact.
The evidence sidecar traces each inserted birth date to its catalog page.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from datetime import date as calendar_date

from .core import ENTRY_FIELDS, norm, read_csv, sex, validate_entries, write_csv

EVIDENCE_FIELDS = ['sale_code','hip','decision','reason','foaling_date','catalog_source_url',
                   'catalog_source_page','catalog_raw_pdf_sha256','result_raw_sha256']


def enrich(results, catalog):
    validate_entries(results)
    by_hip = {}
    duplicates = set()
    for row in catalog:
        hip = (row.get('hip') or '').strip().lstrip('0') or '0'
        if hip in by_hip: duplicates.add(hip)
        by_hip[hip] = row
    enriched, evidence = [], []
    for original in results:
        row = original.copy()
        hip = row['hip']
        c = by_hip.get(hip)
        if not c:
            enriched.append(row)
            continue
        reason = []
        date = (c.get('foaling_date') or '').strip()
        if hip in duplicates: reason.append('duplicate_catalog_hip')
        try:
            if len(date) != 10:
                raise ValueError('Expected ISO date')
            calendar_date.fromisoformat(date)
        except ValueError:
            reason.append('invalid_or_missing_birth_date')
        if date and row['foaling_year'] and date[:4] != row['foaling_year']: reason.append('birth_year_conflict')
        for field in ('sire','dam'):
            if not norm(c.get(field)) or norm(c[field]) != norm(row.get(field)):
                reason.append(field + '_conflict')
        if not sex(c.get('sex')) or sex(c.get('sex')) != sex(row.get('sex')):
            reason.append('sex_conflict')
        if row.get('foaling_date') and row['foaling_date'] != date: reason.append('existing_birth_date_conflict')
        if not c.get('source_url') or not c.get('raw_pdf_sha256'):
            reason.append('missing_catalog_provenance')
        if not reason:
            row['foaling_date'] = date
        evidence.append(dict(sale_code=row['sale_code'],hip=hip,
                             decision='enriched' if not reason else 'review',reason='|'.join(reason),
                             foaling_date=date,catalog_source_url=c.get('source_url',''),
                             catalog_source_page=c.get('source_page',''),
                             catalog_raw_pdf_sha256=c.get('raw_pdf_sha256',''),
                             result_raw_sha256=row.get('raw_sha256','')))
        enriched.append(row)
    validate_entries(enriched)
    return enriched, evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('results'); p.add_argument('catalog'); p.add_argument('output')
    p.add_argument('--evidence', help='Default: <output>.evidence.csv')
    a = p.parse_args()
    rows, evidence = enrich(read_csv(a.results), read_csv(a.catalog))
    write_csv(a.output, rows, ENTRY_FIELDS)
    write_csv(a.evidence or a.output + '.evidence.csv', evidence, EVIDENCE_FIELDS)
    print(json.dumps(dict(result_rows=len(rows), catalog_hips=len(read_csv(a.catalog)),
                          evidence_rows=len(evidence),decisions=dict(Counter(x['decision'] for x in evidence))), indent=2))


if __name__ == '__main__': main()
