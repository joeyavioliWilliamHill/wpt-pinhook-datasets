"""Normalize archived OBS 2020–2023 results .xls exports (March, Spring, June).

The historical workbook stores an RNA bid in Buyer and 'Not Sold' in Price.
Blank summary rows are excluded; raw workbooks remain unchanged.
Requires xlrd>=2.0.1.
"""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from .core import ENTRY_FIELDS, validate_entries, write_csv

SALES = {
    'march20': ('OBSMAR20', 'https://obssales.com/blog/2020/01/31/the-2020-march-sale/',
                [(1,340,'2020-03-17'),(341,681,'2020-03-18')]),
    'spring20': ('OBSSPR20', 'https://obssales.com/blog/2020/03/30/2020-spring-sale-of-two-year-olds-in-training/',
                 [(1,308,'2020-06-09'),(309,616,'2020-06-10'),(617,924,'2020-06-11'),(925,1231,'2020-06-12'),
                  (1233,1252,'2020-06-09'),(1253,1272,'2020-06-10'),(1273,1292,'2020-06-11'),(1293,1315,'2020-06-12')]),
    'july20': ('OBSJUL20', 'https://obssales.com/blog/2020/06/15/2020-july-two-year-olds-horses-of-racing-age/',
               [(1,360,'2020-07-14'),(361,720,'2020-07-15'),(721,1114,'2020-07-16')]),
    'march21': ('OBSMAR21', 'https://obssales.com/blog/2021/02/02/the-2021-march-sale/',
                [(1,282,'2021-03-16'),(283,563,'2021-03-17')]),
    'spring21': ('OBSSPR21', 'https://obssales.com/blog/2021/03/19/2021-spring-sale-of-two-year-olds-in-training/',
                 [(1,304,'2021-04-20'),(305,608,'2021-04-21'),(609,912,'2021-04-22'),(913,1217,'2021-04-23')]),
    'june21': ('OBSJUN21', 'https://obssales.com/blog/2021/04/27/2021-june-two-year-olds-horses-of-racing-age/',
               [(1,316,'2021-06-09'),(317,632,'2021-06-10'),(633,927,'2021-06-11')]),
    'march22': ('OBSMAR22', 'https://obssales.com/blog/2022/01/31/2022-march-sale/',
                [(1, 316, '2022-03-15'), (317, 635, '2022-03-16')]),
    'spring22': ('OBSSPR22', 'https://obssales.com/blog/2022/03/17/spring-sale-2022/',
                 [(1, 308, '2022-04-19'), (309, 616, '2022-04-20'),
                  (617, 924, '2022-04-21'), (925, 1231, '2022-04-22')]),
    'june22': ('OBSJUN22', 'https://obssales.com/blog/2022/04/29/2022-june-two-year-olds-horses-of-racing-age/',
               [(1, 374, '2022-06-07'), (375, 748, '2022-06-08'),
                (749, 1114, '2022-06-09')]),
    'march23': ('OBSMAR23', 'https://obscatalog.com/marresults/2023/',
                [(1, 278, '2023-03-20'), (279, 556, '2023-03-21'), (557, 833, '2023-03-22')]),
    'spring23': ('OBSSPR23', 'https://obscatalog.com/aprresults/2023/',
                 [(1, 306, '2023-04-25'), (307, 612, '2023-04-26'),
                  (613, 918, '2023-04-27'), (919, 1222, '2023-04-28')]),
    'june23': ('OBSJUN23', 'https://obscatalog.com/junresults/2023/',
               [(1, 360, '2023-06-13'), (361, 720, '2023-06-14'),
                (721, 1088, '2023-06-15')]),
}


def _read_sheet(raw, suffix):
    """Return first-sheet values and a workbook-specific Excel date converter."""
    if suffix.lower() == '.xlsx':
        from io import BytesIO
        from openpyxl import load_workbook
        from openpyxl.utils.datetime import from_excel
        book = load_workbook(BytesIO(raw), read_only=True, data_only=True)
        sheet = book.worksheets[0]
        values = [list(row) for row in sheet.values]
        def convert(value):
            if isinstance(value, datetime): return value.date().isoformat()
            if isinstance(value, date): return value.isoformat()
            if isinstance(value, (int, float)): return from_excel(value, book.epoch).date().isoformat()
            raise ValueError(f'Invalid Excel foaling date {value!r}')
        return values, convert
    if suffix.lower() == '.xls':
        import xlrd
        book = xlrd.open_workbook(file_contents=raw)
        sheet = book.sheet_by_index(0)
        return [sheet.row_values(i) for i in range(sheet.nrows)], lambda value: xlrd.xldate_as_datetime(value, book.datemode).date().isoformat()
    raise ValueError(f'Expected .xls or .xlsx workbook, got {suffix!r}')


def normalize(path, sale):
    code, url, sessions = SALES[sale]
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    values, convert_date = _read_sheet(raw, Path(path).suffix)
    # 2020-2022 workbooks label the same columns 'hip#' and 'Dam Sire'.
    label = lambda v: str(v).lower().replace(' ', '').rstrip('#')
    header = next((i for i in range(min(10, len(values))) if label(values[i][0]) == 'hip'), None)
    expected = ['hip', 'name', 'color', 'sex', 'foaldate', 'sire', 'dam', 'damsire']
    if header is None or [label(v) for v in values[header][:8]] != expected:
        raise ValueError('Unexpected archived OBS workbook layout')
    out, excluded = [], []
    for line in range(header + 1, len(values)):
        r = values[line]
        if not isinstance(r[0], (int, float)) or r[0] != int(r[0]) or r[0] < 1:
            continue
        hip = int(r[0])
        # Withdrawn hips may be placeholder rows of '.'.
        if not str(r[5] or '').strip('. ') or not str(r[6] or '').strip('. ') or (sale == 'june23' and (1018 <= hip <= 1029 or hip == 1084)) \
           or (sale == 'june22' and hip >= 1151) \
           or (sale == 'june21' and 860 <= hip <= 879) \
           or (sale == 'july20' and 991 <= hip <= 1005):
            excluded.append(hip)
            continue
        day = next((d for lo, hi, d in sessions if lo <= hip <= hi), None)
        if not day:
            raise ValueError(f'row {line + 1}: unexpected hip {hip}')
        if not isinstance(r[4], (int, float, date, datetime)):
            raise ValueError(f'row {line + 1}, hip {hip}: missing foaling date')
        dob = convert_date(r[4])
        expected_year = str(int(code[-2:]) + 2000 - 2)
        if dob[:4] != expected_year:
            raise ValueError(f'row {line + 1}, hip {hip}: not a {expected_year} foal ({dob})')
        buyer, amount = r[15], r[16]
        if amount == 'Out' and buyer == 'Withdrawn':
            status, price, bid, buyer = 'out', '', '', ''
        elif amount == 'Not Sold' and isinstance(buyer, (int, float)) and buyer >= 0:
            status, price, bid, buyer = 'rna', '', f'{buyer:.2f}', ''
        elif isinstance(amount, (int, float)) and amount > 0 and isinstance(buyer, str) and buyer.strip():
            status, price, bid, buyer = 'sold', f'{amount:.2f}', '', buyer.strip()
        else:
            raise ValueError(f'row {line + 1}, hip {hip}: unexpected result {buyer!r}, {amount!r}')
        out.append(dict(source='obs_legacy_results_excel', sale_code=code, sale_year=str(int(code[-2:]) + 2000), sale_type='juvenile',
            hip=str(hip), source_entry_id=f'{code}:{hip}', source_url=url, registry='', registration_number='',
            foaling_date=dob, foaling_year=dob[:4], sex=str(r[3]).strip(), name=str(r[1]).strip(),
            sire=str(r[5]).strip(), dam=str(r[6]).strip(), broodmare_sire=str(r[7]).strip(), breeder='',
            consignor=str(r[9]).strip(), sale_date=day, status=status, price_usd=price,
            reported_bid_usd=bid, buyer=buyer, raw_sha256=digest))
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
    print(f'{len(rows)} rows -> {a.output}; statuses: {dict(Counter(r["status"] for r in rows))}; excluded rows: {len(excluded)}')


if __name__ == '__main__':
    main()
