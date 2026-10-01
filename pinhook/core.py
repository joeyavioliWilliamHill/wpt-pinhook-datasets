"""Normalization and conservative identity candidate generation."""
from __future__ import annotations
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ENTRY_FIELDS = ['source','sale_code','sale_year','sale_type','hip','source_entry_id','source_url','registry','registration_number',
                'foaling_date','foaling_year','sex','name','sire','dam','broodmare_sire',
                'breeder','consignor','sale_date','status','price_usd','reported_bid_usd','buyer','raw_sha256']
MATCH_FIELDS = ['yearling_sale_code','yearling_hip','juvenile_sale_code','juvenile_hip',
                'basis','decision','collision','multiple_juvenile_events',
                'competing_yearling_candidates','evidence_json','yearling_url','juvenile_url']

def clean(v): return str(v).strip() if v is not None else ''
def norm(v):
    x=unicodedata.normalize('NFKD',clean(v)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]','',x)
def sex(v):
    return {'c':'m','colt':'m','h':'m','horse':'m','g':'g','gelding':'g',
            'f':'f','filly':'f','m':'f','mare':'f'}.get(norm(v),norm(v))
def compatible_sex(a,b): return not a or not b or a==b or {a,b}=={'m','g'}
def iso_date(v):
    if not clean(v): return ''
    for fmt in ('%Y-%m-%d','%m/%d/%Y','%B %d, %Y'):
        try: return datetime.strptime(clean(v),fmt).date().isoformat()
        except ValueError: pass
    raise ValueError(f'Unrecognized date: {v!r}')
def price(v):
    x=clean(v).replace('$','').replace(',','')
    if not x: return ''
    amount=float(x)
    if amount<0: raise ValueError('Negative price')
    return f'{amount:.2f}'
def status(v,amount='',out=False,rna=False):
    x=norm(v)
    if out or x in {'out','withdrawn','scratched'}: return 'out'
    if rna or x in {'rna','notattained','reserve not attained'.replace(' ','')} : return 'rna'
    if x in {'sold','post sale'.replace(' ','')} or (amount and not x): return 'sold'
    if x in {'enterednotsold','notsold'}: return 'entered_not_sold'
    return 'unknown'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_csv(path,rows,fields):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def read_csv(path):
    with open(path,newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def validate_entries(rows):
    seen=set()
    for i,r in enumerate(rows,2):
        k=(r.get('sale_code'),r.get('hip'))
        if not all(k): raise ValueError(f'row {i}: missing sale_code/hip')
        if k in seen: raise ValueError(f'row {i}: duplicate sale_code/hip {k}')
        seen.add(k)
        if r.get('status')=='sold' and not r.get('price_usd'):
            raise ValueError(f'row {i}: sold but no price {k}')
    return rows

def keeneland_json(path,sale_code,sale_year,sale_type,source_url,sessions=None):
    """Adapt WPT-style Keeneland sale_data JSON. Sale ID and sessions supplied externally."""
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    records=data.values() if isinstance(data,dict) else data
    if not isinstance(records,list) and not isinstance(data,dict): raise ValueError('Expected JSON map or list')
    digest=sha(path); out=[]
    for r in records:
        hip=clean(r.get('field_hip_number'))
        if not hip: continue
        amount=price(r.get('field_sale_price') or r.get('field_price'))
        session=clean(r.get('field_session'))
        sale_date=(sessions or {}).get(session,'')
        foaled=iso_date(r.get('field_foaling_date'))
        st=status('',amount,out=norm(r.get('field_out')) in {'y','yes','true','1'},
                  rna=norm(r.get('field_rna_indicator')) in {'y','yes','true','1'})
        out.append(dict(source='keeneland',sale_code=sale_code,sale_year=str(sale_year),sale_type=sale_type,
            hip=hip,source_entry_id=clean(r.get('field_entry_detail_id') or r.get('node_id')),registry='',registration_number='',
            source_url=source_url,foaling_date=foaled,foaling_year=foaled[:4],sex=clean(r.get('field_sex')),
            name=clean(r.get('title')),sire=clean(r.get('field_sire')),dam=clean(r.get('field_dam')),
            broodmare_sire=clean(r.get('field_broodmare_sire')),breeder='',
            consignor=clean(r.get('field_consignor_name') or r.get('field_consignor')),
            sale_date=sale_date,status=st,
            price_usd=amount if st=='sold' else '',reported_bid_usd=amount if st=='rna' else '',buyer=clean(r.get('field_buyer_name') or r.get('field_buyer')),raw_sha256=digest))
    return validate_entries(out)

def generic_csv(path,sale_code,sale_year,sale_type,source,source_url,column_map=None):
    """CSV with canonical headers or a mapping canonical_name -> source_column."""
    mapping=column_map or {}; digest=sha(path); out=[]
    for raw in read_csv(path):
        get=lambda key: clean(raw.get(mapping.get(key,key)))
        hip=get('hip')
        if not hip: continue
        foaled=iso_date(get('foaling_date'))
        amount=price(get('price_usd'))
        st=status(get('status'),amount)
        out.append(dict(source=source,sale_code=sale_code,sale_year=str(sale_year),sale_type=sale_type,
            hip=hip,source_entry_id=get('source_entry_id'),registry=get('registry'),registration_number=get('registration_number'),source_url=get('source_url') or source_url,
            foaling_date=foaled,foaling_year=get('foaling_year') or foaled[:4],sex=get('sex'),
            name=get('name'),sire=get('sire'),dam=get('dam'),broodmare_sire=get('broodmare_sire'),
            breeder=get('breeder'),consignor=get('consignor'),sale_date=iso_date(get('sale_date')),
            status=st,price_usd=amount if st=='sold' else '',reported_bid_usd=amount if st=='rna' else '',buyer=get('buyer'),raw_sha256=digest))
    return validate_entries(out)

def pair_basis(y,t):
    yr,tr=norm(y.get('registration_number')),norm(t.get('registration_number'))
    registry_same=norm(y.get('registry')) and norm(y.get('registry'))==norm(t.get('registry'))
    if yr and tr and registry_same and yr!=tr: return None
    if y.get('foaling_year') and t.get('foaling_year') and y['foaling_year']!=t['foaling_year']: return None
    if not compatible_sex(sex(y.get('sex')),sex(t.get('sex'))): return None
    dy,dt=y.get('foaling_date'),t.get('foaling_date')
    if dy and dt and dy!=dt: return None
    same_pedigree=norm(y.get('sire')) and norm(y.get('dam')) and norm(y['sire'])==norm(t.get('sire')) and norm(y['dam'])==norm(t.get('dam'))
    if yr and tr and registry_same and yr==tr: return 'registry_number'
    if not same_pedigree: return None
    if dy and dt and sex(y.get('sex')) and sex(t.get('sex')): return 'pedigree_dob_sex'
    return 'pedigree_year'

def candidates(yearlings,juveniles):
    validate_entries(yearlings); validate_entries(juveniles)
    blocks=defaultdict(list); regblocks=defaultdict(list)
    for t in juveniles:
        blocks[(t.get('foaling_year'),norm(t.get('sire')),norm(t.get('dam')))].append(t)
        if t.get('registration_number'): regblocks[norm(t['registration_number'])].append(t)
    pairs=[]
    for y in yearlings:
        key=(y.get('foaling_year'),norm(y.get('sire')),norm(y.get('dam')))
        options={(t['sale_code'],t['hip']):t for t in blocks[key]}
        for t in regblocks[norm(y.get('registration_number'))] if y.get('registration_number') else []:
            options[(t['sale_code'],t['hip'])]=t
        for t in options.values():
            basis=pair_basis(y,t)
            if basis:
                evidence={k:[y.get(k,''),t.get(k,'')] for k in ('name','foaling_date','foaling_year','sex','sire','dam','breeder')}
                pairs.append(dict(yearling_sale_code=y['sale_code'],yearling_hip=y['hip'],
                    juvenile_sale_code=t['sale_code'],juvenile_hip=t['hip'],basis=basis,
                    decision='review',collision='',evidence_json=json.dumps(evidence,ensure_ascii=False),
                    yearling_url=y.get('source_url',''),juvenile_url=t.get('source_url','')))
    left=Counter((p['yearling_sale_code'],p['yearling_hip']) for p in pairs)
    right=Counter((p['juvenile_sale_code'],p['juvenile_hip']) for p in pairs)
    for p in pairs:
        repeat=left[(p['yearling_sale_code'],p['yearling_hip'])]>1
        competing=right[(p['juvenile_sale_code'],p['juvenile_hip'])]>1
        p['multiple_juvenile_events']='true' if repeat else 'false'
        p['competing_yearling_candidates']='true' if competing else 'false'
        # Retain the legacy umbrella flag for existing CSV consumers.
        p['collision']='true' if repeat or competing else 'false'
    return pairs
