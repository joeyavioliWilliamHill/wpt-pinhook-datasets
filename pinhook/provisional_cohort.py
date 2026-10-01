"""Make a scoped outcome table from one-to-one, unreviewed identity candidates.

This table is a review artifact. Missing matches mean no match in supplied
juvenile sales, not that the horse never entered a juvenile sale elsewhere.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date
from .core import read_csv,write_csv

FIELDS=['yearling_sale_code','yearling_hip','yearling_name','yearling_status','yearling_price_usd',
        'juvenile_sale_code','juvenile_hip','juvenile_status','juvenile_price_usd','juvenile_reported_bid_usd',
        'candidate_basis','identity_decision','outcome_in_covered_sales','appreciation_usd',
        'gross_return_pct','days_between_sales','yearling_source_url','juvenile_source_url','coverage']


def build(yearlings,juveniles,pairs):
    ys={(r['sale_code'],r['hip']):r for r in yearlings}
    js={(r['sale_code'],r['hip']):r for r in juveniles}
    unique_y=Counter((p['yearling_sale_code'],p['yearling_hip']) for p in pairs)
    unique_j=Counter((p['juvenile_sale_code'],p['juvenile_hip']) for p in pairs)
    links={}
    for p in pairs:
        yk=(p['yearling_sale_code'],p['yearling_hip'])
        jk=(p['juvenile_sale_code'],p['juvenile_hip'])
        if unique_y[yk]!=1 or unique_j[jk]!=1: continue
        if yk not in ys or jk not in js: raise ValueError(f'Candidate missing source row: {yk} -> {jk}')
        links[yk]=(p,js[jk])
    out=[]
    for y in yearlings:
        if y['status']!='sold': continue
        link=links.get((y['sale_code'],y['hip']))
        p,j=link if link else ({},None)
        yp=float(y['price_usd'])
        jp=float(j['price_usd']) if j and j['status']=='sold' else None
        days=(date.fromisoformat(j['sale_date'])-date.fromisoformat(y['sale_date'])).days if j and y.get('sale_date') and j.get('sale_date') else None
        out.append(dict(yearling_sale_code=y['sale_code'],yearling_hip=y['hip'],yearling_name=y.get('name',''),yearling_status='sold',
            yearling_price_usd=y['price_usd'],juvenile_sale_code=j['sale_code'] if j else '',juvenile_hip=j['hip'] if j else '',
            juvenile_status=j['status'] if j else '',juvenile_price_usd=j['price_usd'] if j else '',
            juvenile_reported_bid_usd=j['reported_bid_usd'] if j else '',candidate_basis=p.get('basis',''),
            identity_decision='review' if j else '',
            outcome_in_covered_sales={'sold':'sold_at_2yo','rna':'rna_at_2yo','out':'out_at_2yo'}.get(j['status']) if j else 'no_entry_identified_in_covered_sales',
            appreciation_usd=f'{jp-yp:.2f}' if jp is not None else '',gross_return_pct=f'{100*(jp/yp-1):.4f}' if jp is not None else '',
            days_between_sales=days if days is not None else '',yearling_source_url=y['source_url'],
            juvenile_source_url=j['source_url'] if j else '',coverage='FTMMAY25_results_only'))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('yearlings','juveniles','candidate_pairs','output'):p.add_argument(name)
    a=p.parse_args()
    rows=build(read_csv(a.yearlings),read_csv(a.juveniles),read_csv(a.candidate_pairs))
    write_csv(a.output,rows,FIELDS)
    print(f'{len(rows)} sold-yearling rows -> {a.output}')
    print('Outcomes:',dict(Counter(r['outcome_in_covered_sales'] for r in rows)))
    print('Hip 1956:',next((r for r in rows if r['yearling_hip']=='1956'),None))

if __name__=='__main__':main()
