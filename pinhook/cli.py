"""CLI: normalize local exports, generate review candidates, build outcomes."""
import argparse
import json
from pathlib import Path
from .core import ENTRY_FIELDS,MATCH_FIELDS,keeneland_json,generic_csv,read_csv,write_csv,candidates,validate_entries

def cohort(yearlings,juveniles,decisions,observed_until):
    validate_entries(yearlings);validate_entries(juveniles)
    by_j={(r['sale_code'],r['hip']):r for r in juveniles}
    by_y={(r['sale_code'],r['hip']):r for r in yearlings}
    linked={}
    used=set(); juvenile_owner={}
    for d in decisions:
        if d.get('decision')!='accepted': continue
        ky=(d['yearling_sale_code'],d['yearling_hip']); kt=(d['juvenile_sale_code'],d['juvenile_hip'])
        if ky not in by_y or kt not in by_j: raise ValueError(f'Accepted decision references absent hip: {ky} -> {kt}')
        if (ky,kt) in used: raise ValueError(f'Duplicate accepted pair: {ky} -> {kt}')
        if kt in juvenile_owner and juvenile_owner[kt]!=ky: raise ValueError(f'Juvenile hip assigned to multiple yearlings: {kt}')
        juvenile_owner[kt]=ky
        used.add((ky,kt));linked.setdefault(ky,[]).append(by_j[kt])
    out=[]
    for y in yearlings:
        ky=(y['sale_code'],y['hip']); events=sorted(linked.get(ky,[]),key=lambda r:(r.get('sale_date') or '9999',r['sale_code'],r['hip']))
        first=events[0] if events else None
        first_sold=next((e for e in events if e['status']=='sold'),None)
        selected=first_sold or first
        if first_sold: outcome='sold_at_2yo'
        elif first: outcome={'rna':'rna_at_2yo','out':'out_at_2yo','entered_not_sold':'entered_not_sold_at_2yo'}.get(first['status'],'unresolved')
        else: outcome='no_2yo_sale_identified'
        yp=float(y['price_usd']) if y.get('status')=='sold' and y.get('price_usd') else None
        tp=float(first_sold['price_usd']) if first_sold and first_sold.get('price_usd') else None
        out.append(dict(yearling_sale_code=y['sale_code'],yearling_hip=y['hip'],eligible_purchase=str(yp is not None).lower(),
            first_juvenile_sale_code=first['sale_code'] if first else '',first_juvenile_hip=first['hip'] if first else '',
            selected_resale_sale_code=selected['sale_code'] if selected else '',selected_resale_hip=selected['hip'] if selected else '',
            juvenile_event_count=len(events),outcome=outcome,yearling_price_usd=yp if yp is not None else '',
            juvenile_price_usd=tp if tp is not None else '',appreciation_usd=round(tp-yp,2) if tp is not None and yp else '',
            gross_return_pct=round(100*(tp/yp-1),4) if tp is not None and yp else '',
            observed_until=observed_until,coverage='provided_juvenile_sales_only'))
    return out

def main():
    p=argparse.ArgumentParser(prog='pinhook')
    sub=p.add_subparsers(dest='command',required=True)
    k=sub.add_parser('normalize-keeneland'); k.add_argument('input');k.add_argument('output')
    g=sub.add_parser('normalize-csv');g.add_argument('input');g.add_argument('output')
    for x in (k,g):
        x.add_argument('--sale-code',required=True);x.add_argument('--sale-year',required=True,type=int)
        x.add_argument('--sale-type',required=True,choices=['yearling','juvenile']);x.add_argument('--source-url',required=True)
    k.add_argument('--sessions-json',help='JSON mapping session number to YYYY-MM-DD')
    g.add_argument('--source',required=True);g.add_argument('--columns-json',help='Mapping canonical header -> supplied header')
    m=sub.add_parser('match');m.add_argument('yearlings');m.add_argument('juveniles');m.add_argument('output')
    c=sub.add_parser('cohort');c.add_argument('yearlings');c.add_argument('juveniles');c.add_argument('reviewed_decisions');c.add_argument('output');c.add_argument('--observed-until',required=True)
    a=p.parse_args()
    if a.command=='normalize-keeneland':
        rows=keeneland_json(a.input,a.sale_code,a.sale_year,a.sale_type,a.source_url,
            json.loads(Path(a.sessions_json).read_text()) if a.sessions_json else None)
        fields=ENTRY_FIELDS
    elif a.command=='normalize-csv':
        rows=generic_csv(a.input,a.sale_code,a.sale_year,a.sale_type,a.source,a.source_url,
            json.loads(Path(a.columns_json).read_text()) if a.columns_json else None)
        fields=ENTRY_FIELDS
    elif a.command=='match': rows=candidates(read_csv(a.yearlings),read_csv(a.juveniles));fields=MATCH_FIELDS
    else:
        rows=cohort(read_csv(a.yearlings),read_csv(a.juveniles),read_csv(a.reviewed_decisions),a.observed_until)
        fields=list(rows[0]) if rows else []
    write_csv(a.output,rows,fields)
    print(f'{len(rows)} rows written to {a.output}')
if __name__=='__main__': main()
