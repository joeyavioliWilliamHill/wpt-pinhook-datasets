"""Normalize official 2025 Fasig-Tipton Midlantic May Results Excel/CSV export.

The site's 'Excel File' currently downloads CSV with three extra unnamed columns.
YEAR OF BIRTH is an exact foaling date. NOT SOLD's PRICE is a bid, not sale proceeds.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from datetime import datetime
from pathlib import Path

from .core import ENTRY_FIELDS, validate_entries, write_csv

SOURCE_URL='https://fasigtipton.com/index.php/2025/Midlantic-2YO-Sale?section=7757'


def normalize(path, sale_code='FTMMAY25', sale_type='juvenile', source_url=SOURCE_URL):
    digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    with open(path,encoding='utf-8-sig',newline='') as f:
        data=list(csv.DictReader(f))
    required={'SESSION','HIP','SEX','SIRE','DAM','YEAR OF BIRTH','PURCHASER','PRICE'}
    if not data or not required.issubset(data[0]):
        raise ValueError(f'Not the Fasig-Tipton results export; missing {sorted(required-set(data[0] if data else []))}')
    out=[]
    for line,r in enumerate(data,2):
        hip=str(int(r['HIP']))
        dob=datetime.strptime(r['YEAR OF BIRTH'],'%m/%d/%Y').date().isoformat()
        purchaser=r['PURCHASER'].strip()
        amount=r['PRICE'].strip().replace(',','')
        if not amount.isdecimal(): raise ValueError(f'line {line}, hip {hip}: invalid PRICE {amount!r}')
        if purchaser=='OUT' and amount=='0': state,price,bid,buyer='out','','',''
        elif purchaser=='NOT SOLD' and int(amount)>0: state,price,bid,buyer='rna','',amount,''
        elif purchaser not in ('OUT','NOT SOLD') and int(amount)>0: state,price,bid,buyer='sold',f'{int(amount):.2f}','','' if purchaser=='---' else purchaser
        else: raise ValueError(f'line {line}, hip {hip}: unknown result {purchaser!r}, {amount!r}')
        out.append(dict(source='fasig_tipton_results_csv',sale_code=sale_code,sale_year=r['SESSION'][:4],sale_type=sale_type,
            hip=hip,source_entry_id=f'{sale_code}:{hip}',source_url=source_url+'#/details/'+hip,
            registry='',registration_number='',foaling_date=dob,foaling_year=dob[:4],sex=r['SEX'].strip(),
            name='',sire=r['SIRE'].strip(),dam=r['DAM'].strip(),broodmare_sire=r.get('SIRE OF DAM','').strip(),
            breeder='',consignor=r.get('PROPERTY LINE','').strip(),sale_date=r['SESSION'].strip(),
            status=state,price_usd=price,reported_bid_usd=bid,buyer=buyer,raw_sha256=digest))
    validate_entries(out)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input');p.add_argument('output')
    p.add_argument('--sale-code',default='FTMMAY25')
    p.add_argument('--sale-type',choices=['yearling','juvenile'],default='juvenile')
    p.add_argument('--source-url',default=SOURCE_URL)
    a=p.parse_args()
    rows=normalize(a.input,a.sale_code,a.sale_type,a.source_url)
    write_csv(a.output,rows,ENTRY_FIELDS)
    print(f'{len(rows)} rows -> {a.output}; statuses: {dict(Counter(x["status"] for x in rows))}')
    print('Hip 64:',next((r for r in rows if r['hip']=='64'),None))


if __name__=='__main__':main()
