"""Normalize raw JSON from Fasig-Tipton's public horses results feed."""
import argparse,json,hashlib
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from .core import ENTRY_FIELDS,validate_entries,write_csv

def normalize(path,sale_code,source_url):
 raw=Path(path).read_bytes();data=json.loads(raw);out=[]
 if not isinstance(data,list) or not data:raise ValueError('Expected nonempty public horse list')
 for r in data:
  hip=str(int(r['hip']));amount=Decimal(str(r['price']));buyer=(r['purchaser'] or '').strip()
  dob=datetime.strptime(r['year_of_birth'],'%m/%d/%Y').date().isoformat()
  if buyer=='OUT' and amount==0:status,price,bid,purchaser='out','','',''
  elif buyer=='NOT SOLD' and amount>0:status,price,bid,purchaser='rna','',f'{amount:.2f}',''
  elif buyer and buyer not in ('OUT','NOT SOLD') and amount>0:status,price,bid,purchaser='sold',f'{amount:.2f}','','' if buyer=='---' else buyer
  else:raise ValueError(f'Hip {hip}: unknown price/status combination')
  if dob[:4]!=str(int(r['session'][:4])-2):raise ValueError(f'Hip {hip}: not a juvenile')
  out.append(dict(source='fasig_tipton_public_results_json',sale_code=sale_code,sale_year=r['session'][:4],sale_type='juvenile',hip=hip,source_entry_id=str(r['id']),source_url=source_url+'#/details/'+hip,registry='',registration_number='',foaling_date=dob,foaling_year=dob[:4],sex=r['sex'].strip(),name=(r.get('name') or '').strip(),sire=r['sire'].strip(),dam=r['dam'].strip(),broodmare_sire=(r.get('sire_of_dam') or '').strip(),breeder='',consignor=(r.get('property_line') or '').strip(),sale_date=r['session'],status=status,price_usd=price,reported_bid_usd=bid,buyer=purchaser,raw_sha256=hashlib.sha256(raw).hexdigest()))
 validate_entries(out)
 if len({r['hip'] for r in out})!=len(out):raise ValueError('Duplicate source hip')
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('output');p.add_argument('--sale-code',required=True);p.add_argument('--source-url',required=True);a=p.parse_args()
 rows=normalize(a.input,a.sale_code,a.source_url);write_csv(a.output,rows,ENTRY_FIELDS);print(len(rows),'entries written')
if __name__=='__main__':main()
