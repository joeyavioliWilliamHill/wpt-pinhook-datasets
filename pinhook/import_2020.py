"""Import the 2020 yearling sales and 2021 Midlantic juvenile results.

The planned 2021 OBS juvenile sales are not included. Outputs are always
marked partial, and lack of a match applies only to the covered sale.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .build_cohort_year import generate
from .core import ENTRY_FIELDS, write_csv
from .fasig_results import normalize as fasig
from .keeneland_results import normalize as keeneland


SOURCES = [
    ('kee_sep20_results.csv', 'kee_sep20_full.csv', 'KEESEP20', 'yearling', 'https://flex.keeneland.com/summaries/summaries.html', 'keeneland'),
    ('ft_ky_oct20_results.csv', 'ft_ky_oct20_full.csv', 'FTKYOCT20', 'yearling', 'https://www.fasigtipton.com/2020/Kentucky-October-Yearlings', 'fasig'),
    ('ft_showcase20_results.csv', 'ft_showcase20_full.csv', 'FTSHOW20', 'yearling', 'https://www.fasigtipton.com/2020/Selected-Yearlings-Showcase', 'fasig'),
    ('ft_midfall20_results.csv', 'ft_midfall20_full.csv', 'FTMIDFALL20', 'yearling', 'https://www.fasigtipton.com/2020/Midlantic-Fall-Yearlings', 'fasig'),
    ('ft_may21_results.csv', 'ft_may21_full.csv', 'FTMMAY21', 'juvenile', 'https://www.fasigtipton.com/2021/Midlantic-Two-Year-Olds-in-Training', 'fasig'),
]


def import_files(raw_dir='raw', work_dir='work'):
    raw_dir, work_dir = Path(raw_dir), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for filename, output, code, sale_type, url, parser in SOURCES:
        path = raw_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f'{path} required for {code}: {url}')
        rows = keeneland(path, sale_year=2020) if parser == 'keeneland' else fasig(path, code, sale_type, url)
        if not rows or {row['sale_code'] for row in rows} != {code}:
            raise ValueError(f'{filename}: unexpected or empty sale code')
        write_csv(work_dir / output, rows, ENTRY_FIELDS)
        manifest.append(dict(sale_code=code, raw_file=str(path), normalized_file=str(work_dir / output),
                             source_url=url, sha256=rows[0]['raw_sha256'], rows=len(rows),
                             statuses=dict(Counter(row['status'] for row in rows))))
    output = work_dir / 'cohort_2020_to_2021_partial'
    ys = [work_dir / o for _, o, _, kind, _, _ in SOURCES if kind == 'yearling']
    js = [work_dir / o for _, o, _, kind, _, _ in SOURCES if kind == 'juvenile']
    metrics, summary = generate(2020, ys, js, output)
    (output / 'coverage_manifest.json').write_text(json.dumps({
        'coverage': 'partial',
        'included_yearling_sales': [m['sale_code'] for m in manifest[:-1]],
        'included_juvenile_sales': ['FTMMAY21'],
        'excluded_juvenile_sales': ['OBS March 2021', 'OBS Spring 2021', 'OBS June 2021'],
        'identity_status': 'candidate_links_require_review',
    }, indent=2) + '\n')
    (work_dir / 'cohort_2020_source_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return metrics, summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-dir', default='raw')
    p.add_argument('--work-dir', default='work')
    a = p.parse_args()
    metrics, summary = import_files(a.raw_dir, a.work_dir)
    print(f"{metrics['yearling_entries_supplied']} yearling entries; {metrics['juvenile_entries_supplied']} juvenile entries; {metrics['candidate_pairs']} provisional pairs")
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
