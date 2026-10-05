"""Extract 2024 Keeneland September identities from archived book PDFs.

Each accepted page preserves its book URL, PDF page, hip, and file hash.
Catalog pages establish identity only; join official results separately.
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

BASE = 'https://secure.keeneland.com/sales/k224/pdfs/'
MONTHS = {month: i for i, month in enumerate(('January','February','March','April','May','June','July','August','September','October','November','December'),1)}
FIELDS = ['hip','name','foaling_date','sex','sire','dam','consignor','source_url','source_page','raw_pdf_sha256']
REVIEW = ['book','source_page','hip_guess','reason','header_text']


def write(path, rows, fields):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with open(path,'w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def key(value):
    return re.sub(r'[^a-z0-9]', '', value.casefold())


def extract_page(text, page, book, base_url=BASE):
    lines = [re.sub(r'\s+', ' ', x).strip() for x in text.splitlines() if x.strip()]
    hip_matches = re.findall(r'(?im)^Hip No\.\s*\n\s*(\d{1,4})\s*$', text)
    # Some pages include the hip both at top and bottom; accept only one distinct ID.
    hips = set(hip_matches)
    hip = next(iter(hips)) if len(hips) == 1 else ''
    top = '\n'.join(lines[:45])
    if not hip and not re.search(r'(?i)\bConsigned by\b', top):
        return None, [], top[:1800]  # Index/front matter, not a horse page.
    reasons = []
    if not hip: reasons.append('hip_missing_or_ambiguous')
    date = re.search(r'(?i)\bfoaled\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s*(20\d{2})\b', top)
    dob = f'{date.group(3)}-{MONTHS[date.group(1).title()]:02d}-{int(date.group(2)):02d}' if date else ''
    if not dob: reasons.append('foaling_date_missing')
    sex_match = re.search(r'(?i)\b(filly|colt|gelding|mare|horse)\s*;?\s*foaled\b',top)
    sex = {'filly':'F','colt':'C','gelding':'G','mare':'M','horse':'H'}.get(sex_match.group(1).lower(),'') if sex_match else ''
    if not sex: reasons.append('sex_missing')
    by = next((i for i,x in enumerate(lines) if re.match(r'(?i)^By\s+\S',x)),len(lines))
    head = lines[:by]
    dotted = []
    for line in head:
        match = re.match(r'^(.+?)\s*\.{4,}(?:\s*\(\d{4}\))?\s*$',line)
        if match: dotted.append(match.group(1).strip())
    if len(dotted) >= 2: sire, dam = dotted[-2:]
    else: sire = dam = ''; reasons.append('pedigree_missing')
    cons = re.search(r'(?im)^Consigned by\s+(.+)$',top)
    consignor = cons.group(1).strip() if cons else ''
    if not consignor: reasons.append('consignor_missing')
    name = ''
    if cons:
        following = top[cons.end():].splitlines()
        before_sex = []
        for line in following:
            if re.search(r'(?i)\b(filly|colt|gelding|mare|horse)\s*;?\s*foaled\b',line): break
            before_sex.append(line.strip())
        # Uppercase catalog names are usually the last line before the color/sex line.
        if before_sex and before_sex[-1].isupper(): name = before_sex[-1]
    narrative = re.search(r'(?im)^1st dam\s*\n\s*([^\n,]+),\s*by\b',text)
    if dam and narrative and key(dam) != key(narrative.group(1)):
        reasons.append('dam_narrative_conflict')
    source_url = f'{base_url.rstrip("/")}/{book}#page={page}'
    return dict(hip=hip,name=name,foaling_date=dob,sex=sex,sire=sire,dam=dam,
                consignor=consignor,source_url=source_url,source_page=page), reasons, top[:1800]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', help='Accepted identity CSV')
    p.add_argument('books',nargs='+',help='Downloaded Keeneland 2024 Book PDF paths')
    p.add_argument('--review',help='Review CSV (default: <output stem>_review.csv)')
    p.add_argument('--base-url',default=BASE,help='Archived sale PDF directory, e.g. https://secure.keeneland.com/sales/Sep19/pdfs/')
    a = p.parse_args()
    accepted, review, books = [], [], []
    for path_str in a.books:
        path = Path(path_str)
        book = path.name
        if not re.fullmatch(r'Book\d+[a-z]?\.pdf',book,re.I):
            raise ValueError(f'Expected original BookN.pdf filename: {path}')
        pdf = PdfReader(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        before = len(accepted)
        for number, page in enumerate(pdf.pages,1):
            row, reasons, header = extract_page(page.extract_text() or '',number,book,a.base_url)
            if row is None: continue
            if reasons: review.append(dict(book=book,source_page=number,hip_guess=row['hip'],reason='|'.join(reasons),header_text=header))
            else: row['raw_pdf_sha256'] = digest; accepted.append(row)
        books.append(dict(book=book,sha256=digest,pages=len(pdf.pages),accepted=len(accepted)-before))
    counts = Counter(row['hip'] for row in accepted)
    duplicates = [hip for hip,n in counts.items() if n>1]
    if duplicates: raise ValueError(f'Duplicate accepted hips: {duplicates[:20]}')
    write(a.output,accepted,FIELDS)
    review_path = a.review or str(Path(a.output).with_name(Path(a.output).stem+'_review.csv'))
    write(review_path,review,REVIEW)
    Path(a.output+'.manifest.json').write_text(json.dumps(dict(books=books,accepted=len(accepted),review=len(review)),indent=2)+'\n')
    print(f'{len(accepted)} identities parsed, {len(review)} review -> {a.output}, {review_path}')
    print('Hip 1956:',json.dumps(next((r for r in accepted if r['hip']=='1956'),None)))


if __name__ == '__main__': main()
