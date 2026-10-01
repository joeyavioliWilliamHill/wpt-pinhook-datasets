"""Provisional cohort with every juvenile event in the supplied sales.

All pedigree links remain review candidates because Keeneland results lack DOB.
Repeated juvenile entries sharing exact DOB are kept as an event sequence.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date

from .core import read_csv, write_csv

FIELDS = ['yearling_sale_code', 'yearling_hip', 'yearling_name', 'yearling_sale_date',
          'yearling_price_usd', 'candidate_event_count', 'candidate_juvenile_sale_count',
          'candidate_foaling_date', 'multiple_juvenile_events', 'competing_yearling_candidates',
          'conflicting_candidate_foaling_dates', 'juvenile_events_json', 'identity_decision',
          'first_juvenile_sale_code', 'first_juvenile_hip', 'first_juvenile_status',
          'first_sold_juvenile_sale_code', 'first_sold_juvenile_hip', 'first_sold_juvenile_date',
          'first_sold_juvenile_price_usd', 'outcome_in_covered_sales',
          'appreciation_usd', 'gross_return_pct', 'days_to_first_sold', 'coverage']


def build(yearlings, juveniles, pairs):
    coverage = '_'.join(sorted({j['sale_code'] for j in juveniles})) + '_results'
    js = {(x['sale_code'], x['hip']): x for x in juveniles}
    by_y = defaultdict(list)
    by_j = Counter((p['juvenile_sale_code'], p['juvenile_hip']) for p in pairs)
    for p in pairs:
        jk = (p['juvenile_sale_code'], p['juvenile_hip'])
        if jk not in js:
            raise ValueError(f'Candidate missing juvenile entry: {jk}')
        by_y[(p['yearling_sale_code'], p['yearling_hip'])].append((p, js[jk]))
    out = []
    for y in yearlings:
        if y['status'] != 'sold':
            continue
        events = sorted(by_y[(y['sale_code'], y['hip'])], key=lambda pj: (pj[1]['sale_date'], pj[1]['sale_code'], int(pj[1]['hip'])))
        dobs = {j['foaling_date'] for _, j in events}
        competing = any(by_j[(j['sale_code'], j['hip'])] > 1 for _, j in events)
        conflicting_dobs = len(dobs) > 1
        ambiguous = conflicting_dobs or competing
        first = events[0][1] if events else None
        first_sold = next((j for _, j in events if j['status'] == 'sold'), None)
        price = float(y['price_usd'])
        resale = float(first_sold['price_usd']) if first_sold else None
        days = (date.fromisoformat(first_sold['sale_date']) - date.fromisoformat(y['sale_date'])).days if first_sold and y.get('sale_date') else None
        if not events:
            outcome = 'no_entry_identified_in_covered_sales'
        elif ambiguous:
            outcome = 'ambiguous_identity_review'
        elif first_sold:
            outcome = 'sold_at_2yo'
        elif any(j['status'] == 'rna' for _, j in events):
            outcome = 'rna_at_2yo'
        elif any(j['status'] == 'out' for _, j in events):
            outcome = 'out_at_2yo'
        else:
            outcome = 'entered_not_sold'
        event_rows = [dict(sale_code=j['sale_code'], hip=j['hip'], date=j['sale_date'],
                           status=j['status'], price_usd=j['price_usd'],
                           reported_bid_usd=j['reported_bid_usd'], foaling_date=j['foaling_date'],
                           source_url=j['source_url']) for _, j in events]
        out.append(dict(yearling_sale_code=y['sale_code'], yearling_hip=y['hip'],
            yearling_name=y.get('name', ''), yearling_sale_date=y['sale_date'],
            yearling_price_usd=y['price_usd'], candidate_event_count=len(events),
            candidate_juvenile_sale_count=len({j['sale_code'] for _, j in events}),
            candidate_foaling_date=next(iter(dobs)) if len(dobs) == 1 else '',
            multiple_juvenile_events='true' if len(events)>1 else 'false',
            competing_yearling_candidates='true' if competing else 'false',
            conflicting_candidate_foaling_dates='true' if conflicting_dobs else 'false',
            juvenile_events_json=json.dumps(event_rows, ensure_ascii=False),
            identity_decision='ambiguous_review' if ambiguous else 'review' if events else '',
            first_juvenile_sale_code=first['sale_code'] if first else '',
            first_juvenile_hip=first['hip'] if first else '',
            first_juvenile_status=first['status'] if first else '',
            first_sold_juvenile_sale_code=first_sold['sale_code'] if first_sold else '',
            first_sold_juvenile_hip=first_sold['hip'] if first_sold else '',
            first_sold_juvenile_date=first_sold['sale_date'] if first_sold else '',
            first_sold_juvenile_price_usd=first_sold['price_usd'] if first_sold else '',
            outcome_in_covered_sales=outcome,
            appreciation_usd=f'{resale-price:.2f}' if resale is not None and not ambiguous else '',
            gross_return_pct=f'{100*(resale/price-1):.4f}' if resale is not None and not ambiguous else '',
            days_to_first_sold=days if days is not None and not ambiguous else '',
            coverage=coverage))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('yearlings', 'juveniles', 'candidate_pairs', 'output'):
        p.add_argument(name)
    a = p.parse_args()
    rows = build(read_csv(a.yearlings), read_csv(a.juveniles), read_csv(a.candidate_pairs))
    write_csv(a.output, rows, FIELDS)
    print(f'{len(rows)} sold-yearling rows -> {a.output}')
    print('Outcomes:', dict(Counter(r['outcome_in_covered_sales'] for r in rows)))


if __name__ == '__main__':
    main()
