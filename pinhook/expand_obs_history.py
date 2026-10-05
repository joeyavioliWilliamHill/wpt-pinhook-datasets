"""Acquire archived OBS workbooks and expand 2019–2021 purchase cohorts."""
import argparse
import hashlib
import json
import urllib.request
from collections import Counter
from pathlib import Path
from .obs_legacy_excel import normalize, SALES
from .core import read_csv, write_csv, ENTRY_FIELDS
from .build_cohort_year import generate

FILES = {
 'march20':'Mar20_Excel.xls', 'spring20':'Apr20_Excel.xls', 'july20':'Jul20_Excel.xls',
 'march21':'Mar21_Excel.xls', 'spring21':'Apr21_Excel.xls', 'june21':'Jun21_Excel.xls',
 'march22':'Mar22_Excel.xls', 'spring22':'Apr22_Excel.xlsx', 'june22':'Jun22_Excel.xls',
}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--download',action='store_true')
 p.add_argument('--raw-dir',default='raw')
 p.add_argument('--work-dir',default='work')
 a=p.parse_args();raw=Path(a.raw_dir);work=Path(a.work_dir)
 raw.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True,exist_ok=True)
 sources=[];ready={}
 for sale,filename in FILES.items():
  local=raw/f'obs_{sale[:-2]}{sale[-2:]}_results{Path(filename).suffix}'
  url=f'https://www.obscatalog.com/OBSPAGES/{filename}'
  record=dict(sale=sale,official_page=SALES[sale][1],download_url=url,local_file=str(local))
  if not local.exists() and a.download:
   try:
    with urllib.request.urlopen(url,timeout=20) as response: data=response.read()
    if not (data.startswith(b'\xd0\xcf\x11\xe0') or data.startswith(b'PK')):
     raise ValueError('Response is not an Excel workbook; not saved')
    temp=local.with_suffix(local.suffix+'.part');temp.write_bytes(data);temp.replace(local)
   except Exception as e: record['download_error']=str(e)
  if local.exists():
   record['sha256']=hashlib.sha256(local.read_bytes()).hexdigest()
   try:
    rows,excluded=normalize(local,sale)
    if not rows: raise ValueError('Workbook yielded zero entries')
    dest=work/f'obs_{sale}_full.csv';write_csv(dest,rows,ENTRY_FIELDS)
    ready[sale]=dest;record.update(entries=len(rows),excluded_hips=excluded,status_counts=dict(Counter(r['status'] for r in rows)))
    print(f'{sale}: {len(rows)} normalized entries')
   except Exception as e: record['validation_error']=str(e);print(f'{sale}: validation failed: {e}')
  else: print(f'Missing {local}: download Results in Excel from {SALES[sale][1]}')
  sources.append(record)
 (work/'obs_expansion_sources.json').write_text(json.dumps(sources,indent=2)+'\n')
 comparisons=[]
 for year,sales in [(2019,['march20','spring20','july20']),(2020,['march21','spring21','june21']),(2021,['march22','spring22','june22'])]:
  base=work/f'cohort_{year}_to_{year+1}_partial'
  required=[base/'yearling_entries.csv',base/'juvenile_entries.csv',base/'cohort_by_purchase.csv']
  if any(s not in ready for s in sales) or any(not f.exists() for f in required):
   print(f'{year}: not rebuilt; requires all three OBS files and original partial cohort');continue
  dest=work/f'cohort_{year}_to_{year+1}_expanded'
  generate(year,[required[0]],[required[1]]+[ready[s] for s in sales],dest)
  before=read_csv(required[2]);after=read_csv(dest/'cohort_by_purchase.csv')
  b={(r['yearling_sale_code'],r['yearling_hip']):r for r in before}
  n={(r['yearling_sale_code'],r['yearling_hip']):r for r in after}
  if b.keys()!=n.keys():raise ValueError('Purchase denominators changed unexpectedly')
  result=dict(cohort=f'{year}_to_{year+1}',purchase_rows=len(after),candidate_purchases_before=sum(int(r['candidate_event_count'])>0 for r in before),candidate_purchases_after=sum(int(r['candidate_event_count'])>0 for r in after),new_candidate_purchases=sum(int(n[k]['candidate_event_count'])>0 and int(b[k]['candidate_event_count'])==0 for k in b),sold_candidates_before=sum(r['outcome_in_covered_sales']=='sold_at_2yo' for r in before),sold_candidates_after=sum(r['outcome_in_covered_sales']=='sold_at_2yo' for r in after),ambiguous_after=sum(r['identity_decision']=='ambiguous_review' for r in after),identity_status='provisional_review_required')
  comparisons.append(result);print(json.dumps(result,indent=2))
 (work/'obs_expansion_comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
 if comparisons:write_csv(work/'obs_expansion_comparison.csv',comparisons,list(comparisons[0]))
 print('Original cohorts preserved. New matches remain review candidates.')

if __name__=='__main__':main()
