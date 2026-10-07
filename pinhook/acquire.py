"""Download every raw input from the official sale companies, then normalize the 2022-2025 sales.

Run: python -m pinhook.acquire [--catalogs]
Existing raw files are never refetched or overwritten. Fasig-Tipton and 2024-2025 OBS results
are saved as the JSON feeds behind the sites' browser-generated CSV exports (same records, not the
same bytes); a hand-downloaded CSV with the original name takes precedence. Each download's URL,
hash and row count go to raw/fetch_log.json and are compared with SOURCE_MANIFEST.json.
The 2019-2021 cohorts are then built by import_2019/2020/2021 and expand_obs_history.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import fasig_results, keeneland_results, obs_legacy_excel, obs_results
from .core import ENTRY_FIELDS, sha, write_csv

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'SOURCE_MANIFEST.json').read_text())
KNOWN_URL = {s['sale_code']: s['source_url'] for s in MANIFEST['sources']}
KNOWN_ROWS = {Path(s['raw_file']).name: s['raw_rows'] for s in MANIFEST['sources'] if s.get('raw_rows')}
KNOWN_SHA = {Path(k).name: v['sha256'] for k, v in MANIFEST['files'].items()} | {
    Path(s['raw_file']).name: s['raw_sha256'] for s in json.loads((ROOT / 'SOURCE_MANIFEST_20261002.json').read_text())}

FT_FEED = 'https://www.fasigtipton.com/django/api/horses/?sale={}'
KEE_CSV = ('https://flex.keeneland.com/report/Run.do?xml=WebSummaryPagesCSV.do&xsl=WebSummaryPagesCSVMixed.xsl'
           '&mimeType=TXT&contentType=text/csv&fileName=WebSummaryPagesCSV.csv&saleId={}&sortOrder=hip&csvFlag=true'
           '&session=0&buyerFilter=&sireFilter=&nameFilter=&damFilter=&consignorFilter=&rnaFilter=&outFilter='
           '&hipFilter=&sexFilter=&priceFilter=&filterType=C&sortDirection=A&reportName=WebSummaryPagesCSV')
OBS_XLS = 'https://www.obscatalog.com/OBSPAGES/{}'
OBS_FEED = 'https://obssales.com/wp-json/obs-catalog-wp-plugin/v1/horse-sales/{}'
KEE_BOOKS = 'https://secure.keeneland.com/sales/{}/pdfs/Book{}.pdf'

# Fasig-Tipton feed sale ids, checked against each record's `sale` field.
FT_SALES = {
    'FTMMAY20': ('ft_may20', 170), 'FTMMAY21': ('ft_may21', 181), 'FTMMAY22': ('ft_may22', 198),
    'FTMMAY23': ('ft_may23', 216), 'FTMMAY24': ('ft_may24', 249), 'FTMMAY25': ('ft_may25', 274),
    'FTKYOCT20': ('ft_ky_oct20', 175), 'FTKYOCT21': ('ft_ky_oct21', 193), 'FTKYOCT22': ('ft_ky_oct22', 196),
    'FTKYOCT23': ('ft_ky_oct23', 239), 'FTKYOCT24': ('ft_ky_oct24', 263),
    'FTSHOW20': ('ft_showcase20', 172), 'FTMIDFALL20': ('ft_midfall20', 173),
    'FTJUL21': ('ft_july21', 183), 'FTJUL22': ('ft_july22', 200), 'FTJUL23': ('ft_july23', 218), 'FTJUL24': ('ft_july24', 251),
    'FTSAR21': ('ft_saratoga21', 186), 'FTSAR22': ('ft_saratoga22', 203), 'FTSAR23': ('ft_saratoga23', 231),
    'FTSAR24': ('ft_saratoga24', 256),
    'FTNYB21': ('ft_nybred21', 187), 'FTNYB22': ('ft_nybred22', 204), 'FTNYB23': ('ft_nybred23', 232),
    'FTNYB24': ('ft_nybred24', 257),
}
FT_GULFSTREAM = {'ft_gulfstream2021_horses.json': 180, 'ft_gulfstream2022_horses.json': 197}
KEE_SALES = {2019: 202002, 2020: 202102, 2021: 202202, 2022: 202302, 2023: 202402, 2024: 202502}
OBS_WORKBOOKS = {'march20': 'Mar20_Excel.xls', 'spring20': 'Apr20_Excel.xls', 'july20': 'Jul20_Excel.xls',
                 'march21': 'Mar21_Excel.xls', 'spring21': 'Apr21_Excel.xls', 'june21': 'Jun21_Excel.xls',
                 'march22': 'Mar22_Excel.xls', 'spring22': 'Apr22_Excel.xlsx', 'june22': 'Jun22_Excel.xls',
                 'march23': 'Mar23_Excel.xls', 'spring23': 'Apr23_Excel.xls', 'june23': 'Jun23_Excel.xls'}
OBS_FEEDS = {'march24': 'obs_march24', 'spring24': 'obs_spring24', 'june24': 'obs_june24',
             'march': 'obs_march25', 'spring': 'obs_spring25', 'june': 'obs_june25'}
KEE_BOOK_COUNTS = {2019: ('Sep19', 6), 2020: ('Sep20', 6), 2021: ('Sep21', 5),
                   2022: ('Sep22', 6), 2023: ('k223', 6), 2024: ('k224', 6)}
FT_CATALOG = ('ft_may_2025.pdf', 'https://www.fasigtipton.com/catalogs/2025/0520/web.pdf')


@dataclass(frozen=True)
class Source:
    raw: str  # filename under raw/
    url: str
    kind: str  # ft_feed, obs_feed, kee_csv, workbook, pdf
    sale_id: int | None = None
    sale_code: str = ''
    output: str = ''  # work/ file written by `normalize`; '' when another importer builds it
    parse: Callable[[Path], list[dict]] | None = None


def _sources() -> list[Source]:
    out = []
    for code, (stem, sale_id) in FT_SALES.items():
        year = int('20' + stem[-2:])
        kind = 'juvenile' if code.startswith('FTMMAY') else 'yearling'
        modern = year - (kind == 'juvenile') >= 2022
        url = KNOWN_URL.get(code, fasig_results.SOURCE_URL)
        out.append(Source(f'{stem}_results.json', FT_FEED.format(sale_id), 'ft_feed', sale_id, code,
                          (f'{stem}_results_full.csv' if code == 'FTMMAY25' else f'{stem}_full.csv') if modern else '',
                          lambda p, c=code, k=kind, u=url: fasig_results.normalize(p, c, k, u)))
    out += [Source(raw, FT_FEED.format(i), 'ft_feed', i) for raw, i in FT_GULFSTREAM.items()]
    for year, sale_id in KEE_SALES.items():
        yy = str(year)[-2:]
        out.append(Source(f'kee_sep{yy}_results.csv', KEE_CSV.format(sale_id), 'kee_csv', sale_id, f'KEESEP{yy}',
                          f'kee_sep{yy}_full.csv' if year >= 2022 else '',
                          lambda p, y=year: keeneland_results.normalize(p, sale_year=y)))
    for sale, filename in OBS_WORKBOOKS.items():
        out.append(Source(f'obs_{sale}_results{Path(filename).suffix}', OBS_XLS.format(filename), 'workbook', None,
                          obs_legacy_excel.SALES[sale][0], f'obs_{sale}_full.csv' if sale.endswith('23') else '',
                          lambda p, s=sale: obs_legacy_excel.normalize(p, s)[0]))
    for sale, stem in OBS_FEEDS.items():
        code, sale_id, _ = obs_results.SALES[sale]
        out.append(Source(f'{stem}_results.json', OBS_FEED.format(sale_id), 'obs_feed', sale_id, code,
                          f'{stem}_full.csv', lambda p, s=sale: obs_results.normalize(p, s)[0]))
    return out


SOURCES = _sources()
CATALOGS = [Source(f'keeneland_catalogs/{folder}/Book{n}.pdf', KEE_BOOKS.format(folder, n), 'pdf')
            for folder, books in KEE_BOOK_COUNTS.values() for n in range(1, books + 1)] + \
           [Source(FT_CATALOG[0], FT_CATALOG[1], 'pdf')]


def check(source: Source, data: bytes) -> int | None:
    """Reject responses that are not the expected file; return the record count when it has one."""
    if source.kind == 'ft_feed':
        rows = json.loads(data)
        if not rows or {r['sale'] for r in rows} != {source.sale_id}:
            raise ValueError(f'expected nonempty feed for sale {source.sale_id}')
        for r in rows: fasig_results.from_feed(r)  # a missing field raises before the file is kept
        return len(rows)
    if source.kind == 'obs_feed':
        feed = json.loads(data); rows = feed['sale_hip']
        if not rows or {feed['sale_id'], *(r['sale_id'] for r in rows)} != {str(source.sale_id)}:
            raise ValueError(f'expected nonempty sale_hip for sale {source.sale_id}')
        for r in rows: obs_results.from_feed(r)
        return len(rows)
    if source.kind == 'kee_csv':
        lines = data.decode('utf-8-sig').strip().splitlines()
        if not lines or not lines[0].startswith('Session,Hip,'): raise ValueError('not a Keeneland results CSV')
        return len(lines) - 1
    magic = {'workbook': (b'\xd0\xcf\x11\xe0', b'PK'), 'pdf': (b'%PDF',)}[source.kind]
    if not data.startswith(magic): raise ValueError(f'response is not a {source.kind}')
    return None


def download(url: str, attempts: int = 4) -> bytes:
    # The Fasig-Tipton feed drops large uncompressed responses mid-transfer; gzip avoids that.
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                data = response.read()
                return gzip.decompress(data) if response.headers.get('Content-Encoding') == 'gzip' else data
        except OSError:
            if attempt == attempts - 1: raise
            time.sleep(2 ** attempt)
    raise AssertionError


def local(raw_dir: Path, source: Source) -> Path:
    """A hand-downloaded original CSV export wins over the fetched feed."""
    path = raw_dir / source.raw
    original = path.with_suffix('.csv')
    return original if path.suffix == '.json' and original.exists() else path


def fetch(raw_dir: Path, sources: list[Source]) -> list[str]:
    log_path = raw_dir / 'fetch_log.json'
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    failures = []
    for source in sources:
        path = local(raw_dir, source)
        if path.exists(): continue
        try:
            data = download(source.url)
            rows = check(source, data)
        except Exception as e:
            failures.append(f'{source.raw}: {e}')
            print(f'FAILED {source.raw}: {e}')
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_name(path.name + '.part')
        part.write_bytes(data)
        part.replace(path)
        digest = hashlib.sha256(data).hexdigest()
        # Feeds stand in for CSV exports, so their row counts are compared with the CSV's.
        export = path.with_suffix('.csv').name if source.kind in ('ft_feed', 'obs_feed') else path.name
        notes = []
        if path.name in KNOWN_SHA:
            notes.append('sha256 matches manifest' if KNOWN_SHA[path.name] == digest else 'sha256 DIFFERS from manifest')
        if export in KNOWN_ROWS:
            notes.append('rows match manifest' if KNOWN_ROWS[export] == rows else f'rows DIFFER: manifest {KNOWN_ROWS[export]}')
        log[source.raw] = dict(url=source.url, sha256=digest, bytes=len(data), rows=rows, notes=notes,
                               fetched_at=datetime.now(timezone.utc).isoformat(timespec='seconds'))
        print(f'{source.raw}: {len(data)} bytes, {rows} rows {"; ".join(notes)}')
        log_path.write_text(json.dumps(log, indent=2) + '\n')
        time.sleep(0.5)
    return failures


def normalize(raw_dir: Path, work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        if not source.output: continue
        path = local(raw_dir, source)
        if not path.exists():
            print(f'skip {source.output}: missing {path}')
            continue
        rows = source.parse(path)
        if not rows or {r['sale_code'] for r in rows} != {source.sale_code}:
            raise ValueError(f'{path}: invalid/empty sale {source.sale_code}')
        dest = work_dir / source.output
        write_csv(dest, rows, ENTRY_FIELDS)
        expected = MANIFEST['files'].get(f'work/{source.output}', {}).get('sha256')
        same = 'identical to manifest' if expected == sha(dest) else 'differs from manifest' if expected else 'no manifest hash'
        print(f'{source.sale_code}: {len(rows)} entries -> {dest} ({same})')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--raw-dir', type=Path, default=Path('raw'))
    p.add_argument('--work-dir', type=Path, default=Path('work'))
    p.add_argument('--catalogs', action='store_true', help='Also download Keeneland books and the 2025 F-T catalog (~300 MB)')
    p.add_argument('--no-normalize', action='store_true')
    a = p.parse_args()
    failures = fetch(a.raw_dir, SOURCES + (CATALOGS if a.catalogs else []))
    if not a.no_normalize: normalize(a.raw_dir, a.work_dir)
    if failures: raise SystemExit('Failed downloads:\n' + '\n'.join(failures))


if __name__ == '__main__':
    main()
