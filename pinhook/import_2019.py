"""Rebuild the partial 2019 Keeneland to 2020 Midlantic cohort."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .build_cohort_year import generate
from .core import ENTRY_FIELDS, raw_or_json, write_csv
from .fasig_results import normalize as fasig
from .keeneland_results import normalize as keeneland

SOURCES = [
    ('kee_sep19_results.csv','kee_sep19_full.csv','KEESEP19','yearling','https://flex.keeneland.com/summaries/summaries.html'),
    ('ft_may20_results.csv','ft_may20_full.csv','FTMMAY20','juvenile','https://www.fasigtipton.com/2020/Midlantic-Two-Year-Olds-in-Training'),
]


def import_files(raw_dir='raw',work_dir='work'):
    raw_dir,work_dir=Path(raw_dir),Path(work_dir)
    work_dir.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for filename,output,code,kind,url in SOURCES:
        path=raw_or_json(raw_dir/filename)
        if not path.is_file(): raise FileNotFoundError(path)
        rows=keeneland(path,sale_year=2019) if code=='KEESEP19' else fasig(path,code,kind,url)
        write_csv(work_dir/output,rows,ENTRY_FIELDS)
        manifest.append(dict(sale_code=code,source_url=url,raw_file=str(path),sha256=rows[0]['raw_sha256'],
                             rows=len(rows),statuses=dict(Counter(r['status'] for r in rows))))
    output=work_dir/'cohort_2019_to_2020_partial'
    metrics,summary=generate(2019,[work_dir/SOURCES[0][1]],[work_dir/SOURCES[1][1]],output)
    (output/'coverage_manifest.json').write_text(json.dumps(dict(coverage='partial',
        included_yearling_sales=['KEESEP19'],included_juvenile_sales=['FTMMAY20'],
        excluded_juvenile_sales=['OBS March 2020','OBS Spring 2020','OBS June 2020'],
        identity_status='candidate_links_require_review'),indent=2)+'\n')
    (work_dir/'cohort_2019_source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return metrics,summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-dir',default='raw');p.add_argument('--work-dir',default='work')
    a=p.parse_args()
    metrics,_=import_files(a.raw_dir,a.work_dir)
    print(f"{metrics['sold_yearling_entries_supplied']} sold yearling purchases; {metrics['sold_yearling_entries_with_candidate']} provisional linked purchases")


if __name__=='__main__': main()
