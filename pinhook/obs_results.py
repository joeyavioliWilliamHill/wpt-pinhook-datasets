"""Normalize official OBS results CSV exports for the 2024-2025 juvenile sales.

A .json path is read as the site's feed
https://obssales.com/wp-json/obs-catalog-wp-plugin/v1/horse-sales/<id>, from which the
browser builds that CSV; records are mapped to the CSV columns.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .core import ENTRY_FIELDS, validate_entries, write_csv

SALES = {
    'march24': ('OBSMAR24', 135, [(1, 284, '2024-03-12'), (285, 568, '2024-03-13'), (569, 853, '2024-03-14')]),
    'spring24': ('OBSSPR24', 136, [(1, 302, '2024-04-16'), (303, 604, '2024-04-17'),
                                   (605, 906, '2024-04-18'), (907, 1208, '2024-04-19')]),
    'june24': ('OBSJUN24', 137, [(1, 350, '2024-06-12'), (351, 700, '2024-06-13'),
                                 (701, 1027, '2024-06-14')]),
    'march': ('OBSMAR25', 142, [(1, 814, '2025-03-11')]),
    'spring': ('OBSSPR25', 144, [(1, 302, '2025-04-15'), (303, 604, '2025-04-16'),
                                  (605, 906, '2025-04-17'), (907, 1207, '2025-04-18')]),
    'june': ('OBSJUN25', 145, [(1, 430, '2025-06-17'), (451, 903, '2025-06-18')]),
}


FEED_COLUMNS = {'Hip Number': 'hip_number', 'Foaling Year': 'foaling_year', 'Foaling Date': 'foaling_date',
                'Sex': 'sex', 'Sire Name': 'sire_name', 'Dam Name': 'dam_name', 'IN Out Status': 'in_out_status',
                'Buyer Name': 'buyer_name', 'Horse Name': 'horse_name', 'Dam Sire': 'dam_sire',
                'Property Line 1': 'property_line_1'}


def from_feed(r: dict) -> dict[str, str]:
    row = {column: r[key] or '' for column, key in FEED_COLUMNS.items()}
    price = r['hammer_price']
    row['Hammer Price'] = '' if price is None else format(Decimal(str(price)).normalize(), 'f')
    return row


def normalize(path, sale):
    code, sale_id, sessions = SALES[sale]
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if Path(path).suffix == '.json':
        data, source = [from_feed(r) for r in json.loads(raw)['sale_hip']], 'obs_results_json'
    else:
        with open(path, encoding='utf-8-sig', newline='') as f:
            data, source = list(csv.DictReader(f)), 'obs_results_csv'
    required = {'Hip Number', 'Foaling Year', 'Foaling Date', 'Sex', 'Sire Name',
                'Dam Name', 'IN Out Status', 'Buyer Name', 'Hammer Price'}
    if not data or not required.issubset(data[0]):
        raise ValueError(f'Missing OBS columns: {sorted(required - set(data[0] if data else []))}')
    out = []
    excluded = []
    for line, r in enumerate(data, 2):
        hip = int(r['Hip Number'])
        if (sale == 'june' and (hip >= 901 or r['Sire Name'].startswith('zz blank page'))) or \
           (sale == 'june24' and (hip >= 1101 or r['Sire Name'].startswith('zz blank page'))):
            excluded.append(hip)  # Racing-age entries and catalog placeholder, not 2YOs.
            continue
        dob = datetime.strptime(r['Foaling Date'], '%m/%d/%Y').date().isoformat()
        if dob[:4] != r['Foaling Year']:
            raise ValueError(f'line {line}: inconsistent foaling year')
        raw_price = r['Hammer Price'].strip().replace(',', '')
        buyer = r['Buyer Name'].strip()
        if r['IN Out Status'] == 'O' and buyer == 'OUT' and not raw_price:
            state, price, bid, buyer = 'out', '', '', ''
        elif r['IN Out Status'] == 'I' and buyer == 'RNA' and raw_price.startswith('-'):
            state, price, bid, buyer = 'rna', '', f'{abs(int(raw_price)):.2f}', ''
        elif r['IN Out Status'] == 'I' and buyer not in ('OUT', 'RNA') and raw_price.isdecimal() and int(raw_price) > 0:
            state, price, bid = 'sold', f'{int(raw_price):.2f}', ''
        else:
            raise ValueError(f'line {line}, hip {hip}: unexpected result {r["IN Out Status"]!r}, {buyer!r}, {raw_price!r}')
        day = next((date for lo, hi, date in sessions if lo <= hip <= hi), '')
        # March has three sessions; handled separately below.
        if sale == 'march':
            day = ['2025-03-11', '2025-03-12', '2025-03-13'][(hip - 1) // 272]
        if not day:
            raise ValueError(f'line {line}, hip {hip}: no sale session')
        out.append(dict(source=source, sale_code=code, sale_year=day[:4], sale_type='juvenile',
            hip=str(hip), source_entry_id=f'{code}:{hip}',
            source_url=f'https://obssales.com/catalog/#/{sale_id}/results',
            registry='', registration_number='', foaling_date=dob, foaling_year=r['Foaling Year'],
            sex=r['Sex'].strip(), name=r['Horse Name'].strip(), sire=r['Sire Name'].strip(),
            dam=r['Dam Name'].strip(), broodmare_sire=r['Dam Sire'].strip(), breeder='',
            consignor=r['Property Line 1'].strip(), sale_date=day, status=state,
            price_usd=price, reported_bid_usd=bid, buyer=buyer, raw_sha256=digest))
    validate_entries(out)
    return out, excluded


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('sale', choices=SALES)
    p.add_argument('input')
    p.add_argument('output')
    a = p.parse_args()
    rows, excluded = normalize(a.input, a.sale)
    write_csv(a.output, rows, ENTRY_FIELDS)
    print(f'{len(rows)} rows -> {a.output}; statuses: {dict(Counter(r["status"] for r in rows))}; excluded hips: {excluded}')


if __name__ == '__main__':
    main()
