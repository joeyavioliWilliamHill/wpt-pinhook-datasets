"""Extract identity fields from Fasig-Tipton 2025 Midlantic per-hip catalog pages.

Usage: python -m pinhook.pdf_catalog raw/ft_may_2025.pdf work/ft_catalog.csv
Requires: pip install 'pypdf>=6' fonttools
Every low-confidence page is emitted to a review CSV; no sale outcomes are inferred.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from pypdf import PdfReader

SOURCE_URL='https://www.fasigtipton.com/catalogs/2025/0520/web.pdf'
FIELDS=['hip','name','foaling_date','sex','sire','dam','consignor','source_url','source_page','raw_pdf_sha256']
REVIEW_FIELDS=['source_page','hip_guess','reason','header_text']
MONTHS={m:i for i,m in enumerate(('January','February','March','April','May','June','July','August','September','October','November','December'),1)}

def extract_page(text,page):
    lines=[re.sub(r'\s+',' ',x).strip() for x in text.splitlines() if x.strip()]
    header=[]
    for line in lines:
        if re.match(r'^By\s+[A-Z][A-Z\s\-()]+\s*\(',line): break
        if line.lower()=='1st dam': break
        header.append(line)
    top='\n'.join(header[:45])
    hip_match=re.search(r'(?m)^(\d+)\s*(?:Consigned by|Property of)\b',top)
    hip=hip_match.group(1) if hip_match else ''
    reasons=[]
    if not hip: reasons.append('hip_missing')
    if hip and hip!=str(page): reasons.append('hip_page_mismatch')
    date_match=re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s*(20\d{2})\b',top)
    dob=f'{date_match.group(3)}-{MONTHS[date_match.group(1)]:02d}-{int(date_match.group(2)):02d}' if date_match else ''
    if not dob: reasons.append('foaling_date_missing')
    sex_match=re.search(r'(?i)\b(filly|colt|gelding|mare|horse)\b',top)
    sex={'filly':'F','colt':'C','gelding':'G','mare':'M','horse':'H'}.get(sex_match.group(1).lower(),'') if sex_match else ''
    if not sex: reasons.append('sex_missing')
    # The last three dotted rows are sire, dam, and subject; dots are separated by spaces.
    # E.g. Blame ..... / Collections Choice ... / (2014) / Blame Kate .....
    pedigree=[]
    for line in header:
        match=re.match(r'^(.+?)\s+(?:\.\s*){3,}$',line)
        if match: pedigree.append(match.group(1).strip())
    # Named subjects have a dotted line; unnamed subjects often end in a single dot.
    subject_dotted=bool(pedigree and re.search(r'(?i)\b(filly|colt|gelding|mare|horse)\b',pedigree[-1]))
    cons_match=re.search(r'(?m)^\d+\s*(?:Consigned by|Property of)\s+(.+)$',top)
    consignor=cons_match.group(1).strip() if cons_match else ''
    if not consignor: reasons.append('consignor_missing')
    name=''
    if cons_match:
        subsequent=top[cons_match.end():].splitlines()
        name=next((line.strip() for line in subsequent if line.strip()),'')
    if not name or re.search(r'(?i)\b(filly|colt|gelding)\b',name):
        name='';reasons.append('name_missing_or_unnamed')
    if name and pedigree:
        norm=lambda value: re.sub(r'[^a-z0-9]','',value.lower())
        subject_dotted=norm(pedigree[-1])==norm(name)
    if subject_dotted and len(pedigree)>=3:
        sire,dam=pedigree[-3:-1]
    elif not name and len(pedigree)>=2:
        sire,dam=pedigree[-2:]
    else:
        sire=dam='';reasons.append('pedigree_lines_missing')
    if sire and dam:
        narrative=re.search(r'(?im)^1st dam\s*\n\s*(.+)$',text)
        if narrative:
            first_dam=re.sub(r'[^a-z0-9]','',narrative.group(1).split(',')[0].lower())
            if first_dam and first_dam!=re.sub(r'[^a-z0-9]','',dam.lower()):
                reasons.append('dam_narrative_conflict')
    row=dict(hip=hip,name=name,foaling_date=dob,sex=sex,sire=sire,dam=dam,
             consignor=consignor,source_url=f'{SOURCE_URL}#page={page}',source_page=page)
    # Name is optional, but missing identity fields or internal conflicts require review.
    hard=[r for r in reasons if r!='name_missing_or_unnamed']
    return row,hard,top[:2200]

def write(path,rows,fields):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf');p.add_argument('output');p.add_argument('--review',default=None)
    a=p.parse_args(); data=Path(a.pdf).read_bytes(); digest=hashlib.sha256(data).hexdigest()
    reader=PdfReader(a.pdf); accepted=[];review=[]
    for index,page in enumerate(reader.pages,1):
        text=page.extract_text() or ''
        row,reasons,header=extract_page(text,index)
        if reasons: review.append(dict(source_page=index,hip_guess=row['hip'],reason='|'.join(reasons),header_text=header))
        else:
            row['raw_pdf_sha256']=digest;accepted.append(row)
    counts=Counter(r['hip'] for r in accepted)
    duplicates={hip for hip,count in counts.items() if count>1}
    if duplicates: raise ValueError(f'Duplicate parsed hips: {sorted(duplicates)}')
    write(a.output,accepted,FIELDS)
    review_path=a.review or str(Path(a.output).with_name(Path(a.output).stem+'_review.csv'))
    write(review_path,review,REVIEW_FIELDS)
    manifest=dict(source_url=SOURCE_URL,local_pdf=a.pdf,sha256=digest,pages=len(reader.pages),
                  accepted=len(accepted),review=len(review),parser='fasig_midlantic_2025_v1')
    Path(a.output+'.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{len(reader.pages)} pages: {len(accepted)} parsed, {len(review)} review -> {a.output}, {review_path}')
    example=next((r for r in accepted if r['hip']=='64'),None)
    print('Hip 64:',json.dumps(example,ensure_ascii=False) if example else 'REVIEW QUEUE')
if __name__=='__main__': main()
