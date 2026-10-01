"""Normalize Keeneland Sale Summaries CSV for September 2024.

The official export has sale status encoded in Purchaser/Price. DOB is blank
in this export, so exact DOB remains empty until catalog enrichment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter
from pathlib import Path

from .core import ENTRY_FIELDS, write_csv, validate_entries

SOURCE_URL = 'https://flex.keeneland.com/summaries/summaries.html'
SESSION_DATES = dict(enumerate((
    '2024-09-09','2024-09-10','2024-09-11','2024-09-12',
    '2024-09-14','2024-09-15','2024-09-16','2024-09-17',
    '2024-09-18','2024-09-19','2024-09-20','2024-09-21'),1))
SESSION_DATES_2023 = dict(enumerate((
    '2023-09-11','2023-09-12','2023-09-13','2023-09-14',
    '2023-09-16','2023-09-17','2023-09-18','2023-09-19',
    '2023-09-20','2023-09-21','2023-09-22','2023-09-23'),1))
SESSION_DATES_2022 = dict(enumerate((
    '2022-09-12','2022-09-13','2022-09-14','2022-09-15',
    '2022-09-17','2022-09-18','2022-09-19','2022-09-20',
    '2022-09-21','2022-09-22','2022-09-23','2022-09-24'),1))
SESSION_DATES_2021 = dict(enumerate((
    '2021-09-13','2021-09-14','2021-09-15','2021-09-16',
    '2021-09-18','2021-09-19','2021-09-20','2021-09-21',
    '2021-09-22','2021-09-23','2021-09-24'),1))
SESSION_DATES_2020 = dict(enumerate((
    '2020-09-13','2020-09-14','2020-09-16','2020-09-17',
    '2020-09-18','2020-09-19','2020-09-20','2020-09-21',
    '2020-09-22','2020-09-23','2020-09-24','2020-09-25'),1))
SESSION_DATES_2019 = dict(enumerate((
    '2019-09-09','2019-09-10','2019-09-11','2019-09-13',
    '2019-09-14','2019-09-15','2019-09-16','2019-09-17',
    '2019-09-18','2019-09-19','2019-09-20','2019-09-21',
    '2019-09-22'),1))


def normalize(path, sale_year=2024):
    if sale_year not in (2019,2020,2021,2022,2023,2024): raise ValueError('Unsupported Keeneland September year')
    sessions = {2019:SESSION_DATES_2019,2020:SESSION_DATES_2020,2021:SESSION_DATES_2021,2022:SESSION_DATES_2022,2023:SESSION_DATES_2023,2024:SESSION_DATES}[sale_year]
    code = f'KEESEP{str(sale_year)[2:]}'
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    with open(path,encoding='utf-8-sig',newline='') as file:
        source = list(csv.DictReader(file))
    expected = {'Session','Hip','Horse Name','Sire','Dam','Sex','Purchaser','Price'}
    if not source or not expected.issubset(source[0]):
        raise ValueError(f'Not a Keeneland Sale Summaries CSV: missing {sorted(expected-set(source[0] if source else []))}')
    out=[]
    for line,raw in enumerate(source,2):
        hip = raw['Hip'].strip().lstrip('0') or '0'
        session = int(raw['Session'])
        if session not in sessions: raise ValueError(f'line {line}: unknown session {session}')
        purchaser = raw['Purchaser'].strip()
        amount = raw['Price'].strip()
        if purchaser.casefold() == 'out' and amount == '0':
            state,price,bid,buyer = 'out','','',''
        elif re.fullmatch(r'R\.N\.A\.\s*\([\d,]+\)',purchaser,re.I) and amount == '---':
            state,price,bid,buyer = 'rna','',re.search(r'\(([\d,]+)\)',purchaser).group(1).replace(',',''),''
        elif amount.isdecimal() and int(amount)>0 and purchaser:
            state,price,bid,buyer = 'sold',f'{int(amount):.2f}','','' if purchaser=='---' else purchaser
        else:
            raise ValueError(f'line {line}, hip {hip}: unrecognized status encoding: {purchaser!r}, {amount!r}')
        out.append(dict(source='keeneland_sale_summaries_csv',sale_code=code,sale_year=str(sale_year),sale_type='yearling',
            hip=hip,source_entry_id=f'{code}:{hip}',source_url=SOURCE_URL,
            registry='',registration_number='',foaling_date='',foaling_year=str(sale_year-1),
            sex=raw['Sex'].strip(),name=raw['Horse Name'].strip(),sire=raw['Sire'].strip(),dam=raw['Dam'].strip(),
            broodmare_sire='',breeder='',consignor=' '.join(x.strip() for x in (raw.get('PropertyLine1',''),raw.get('PropertyLine2','')) if x.strip()),
            sale_date=sessions[session],status=state,price_usd=price,reported_bid_usd=bid,buyer=buyer,raw_sha256=digest))
    validate_entries(out)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input');p.add_argument('output');p.add_argument('--sale-year',type=int,choices=[2019,2020,2021,2022,2023,2024],default=2024)
    a=p.parse_args()
    rows=normalize(a.input,a.sale_year)
    write_csv(a.output,rows,ENTRY_FIELDS)
    print(f'{len(rows)} rows -> {a.output}; statuses: {dict(Counter(x["status"] for x in rows))}')
    print('Hip 1956:',next((r for r in rows if r['hip']=='1956'),None))


if __name__=='__main__': main()
