"""Normalize a locally downloaded 2021 yearling -> 2022 juvenile cohort.

Place the nine official exports under raw/ with the filenames in README_2021.md.
Run: python -m pinhook.import_2021 --raw-dir raw --work-dir work
Missing files are reported; a cohort is built only when all nine are present.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .build_cohort_year import generate
from .core import ENTRY_FIELDS, raw_or_json, write_csv
from .fasig_results import normalize as fasig
from .keeneland_results import normalize as keeneland
from .obs_legacy_excel import normalize as obs


SOURCES = [
    ('kee_sep21_results.csv', 'kee_sep21_full.csv', 'KEESEP21', 'yearling', 'https://flex.keeneland.com/summaries/summaries.html', 'keeneland'),
    ('ft_ky_oct21_results.csv', 'ft_ky_oct21_full.csv', 'FTKYOCT21', 'yearling', 'https://www.fasigtipton.com/2021/Kentucky-October-Yearlings', 'fasig'),
    ('ft_saratoga21_results.csv', 'ft_saratoga21_full.csv', 'FTSAR21', 'yearling', 'https://www.fasigtipton.com/2021/The-Saratoga-Sale', 'fasig'),
    ('ft_nybred21_results.csv', 'ft_nybred21_full.csv', 'FTNYB21', 'yearling', 'https://www.fasigtipton.com/2021/New-York-Bred-Yearlings', 'fasig'),
    ('ft_july21_results.csv', 'ft_july21_full.csv', 'FTJUL21', 'yearling', 'https://www.fasigtipton.com/2021/The-July-Sale', 'fasig'),
    ('obs_march22_results.xls', 'obs_march22_full.csv', 'OBSMAR22', 'juvenile', 'https://obssales.com/blog/2022/01/31/2022-march-sale/', 'march22'),
    ('obs_spring22_results.xlsx', 'obs_spring22_full.csv', 'OBSSPR22', 'juvenile', 'https://obssales.com/blog/2022/03/17/spring-sale-2022/', 'spring22'),
    ('obs_june22_results.xls', 'obs_june22_full.csv', 'OBSJUN22', 'juvenile', 'https://obssales.com/blog/2022/04/29/2022-june-two-year-olds-horses-of-racing-age/', 'june22'),
    ('ft_may22_results.csv', 'ft_may22_full.csv', 'FTMMAY22', 'juvenile', 'https://www.fasigtipton.com/2022/Midlantic-Two-Year-Olds-in-Training', 'fasig'),
]


def import_files(raw_dir, work_dir, allow_partial=False):
    raw_dir, work_dir = Path(raw_dir), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    missing = []
    manifest = []
    for filename, output, code, sale_type, url, parser in SOURCES:
        path = raw_or_json(raw_dir / filename)
        if not path.is_file():
            missing.append(dict(filename=filename, url=url))
            continue
        if parser == 'keeneland': rows = keeneland(path, sale_year=2021)
        elif parser == 'fasig': rows = fasig(path, code, sale_type, url)
        else: rows, _ = obs(path, parser)
        if not rows or {r['sale_code'] for r in rows} != {code}:
            raise ValueError(f'{filename}: invalid/empty sale {code}')
        write_csv(work_dir / output, rows, ENTRY_FIELDS)
        manifest.append(dict(sale_code=code, raw_file=str(path), normalized_file=str(work_dir / output),
                             source_url=url, sha256=rows[0]['raw_sha256'], rows=len(rows),
                             statuses=dict(Counter(r['status'] for r in rows))))
        print(f'{code}: {len(rows)} entries -> {work_dir / output}')
    (work_dir / 'cohort_2021_source_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    if missing:
        print('\nStill needed (run python -m pinhook.acquire, or download from the official page and rename exactly):')
        for item in missing: print(f"  {item['filename']} <- {item['url']}")
        if not allow_partial:
            print('No partial cohort was built.')
            return False
    ys = [work_dir / output for filename, output, _, kind, _, _ in SOURCES
          if kind == 'yearling' and raw_or_json(raw_dir / filename).is_file()]
    js = [work_dir / output for filename, output, _, kind, _, _ in SOURCES
          if kind == 'juvenile' and raw_or_json(raw_dir / filename).is_file()]
    if not ys or not js:
        print('Both sale sides are required to build a cohort.')
        return False
    output = work_dir / ('cohort_2021_to_2022_partial' if missing else 'cohort_2021_to_2022')
    metrics, summary = generate(2021, ys, js, output)
    (output / 'coverage_manifest.json').write_text(json.dumps({
        'coverage': 'partial' if missing else 'complete_for_planned_sales',
        'included_yearling_sales': [m['sale_code'] for m in manifest if m['sale_code'] in {r[2] for r in SOURCES if r[3] == 'yearling'}],
        'included_juvenile_sales': [m['sale_code'] for m in manifest if m['sale_code'] in {r[2] for r in SOURCES if r[3] == 'juvenile'}],
        'missing_sources': missing,
        'identity_status': 'candidate_links_require_review',
    }, indent=2) + '\n')
    print(f"\n{'Partial' if missing else 'Planned-sales'} 2021 -> 2022 cohort: {metrics['candidate_pairs']} candidate links")
    print(json.dumps(summary, indent=2))
    return not missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', default='raw')
    parser.add_argument('--work-dir', default='work')
    parser.add_argument('--allow-partial', action='store_true', help='Build an explicitly labeled cohort from available sales')
    args = parser.parse_args()
    import_files(args.raw_dir, args.work_dir, allow_partial=args.allow_partial)


if __name__ == '__main__':
    main()
