import tempfile
import unittest
from pathlib import Path
from pinhook.core import candidates, generic_csv, write_csv
from pinhook.cli import cohort

class PipelineTest(unittest.TestCase):
    def row(self,sale,hip,foal,sex,status='sold',price='10000',dam='Collections Choice',sale_date=''):
        return dict(sale_code=sale,hip=hip,foaling_year=foal[:4],foaling_date=foal,
                    sire='Blame',dam=dam,sex=sex,status=status,price_usd=price,sale_date=sale_date)
    def test_real_catalog_identity_and_full_sibling_negative(self):
        y=[self.row('KEESEP24','1956','2023-04-08','F',price='22000')]
        t=[self.row('FTMMAY25','64','2023-04-08','F',price='350000'),
           self.row('OTHER25','8','2022-04-08','F',price='100000')]
        matches=candidates(y,t)
        self.assertEqual([(x['juvenile_hip'],x['basis']) for x in matches],[('64','pedigree_dob_sex')])
        self.assertEqual(matches[0]['decision'],'review')
    def test_rna_followed_by_sold_and_unmatched(self):
        ys=[self.row('KEESEP24','1956','2023-04-08','F',price='22000'),
            self.row('KEESEP24','1957','2023-04-09','F',price='5000')]
        ts=[self.row('OBSMAR25','12','2023-04-08','F','rna','',sale_date='2025-03-11'),
            self.row('FTMMAY25','64','2023-04-08','F','sold','350000',sale_date='2025-05-20')]
        ds=[dict(decision='accepted',yearling_sale_code='KEESEP24',yearling_hip='1956',juvenile_sale_code=t['sale_code'],juvenile_hip=t['hip']) for t in ts]
        out=cohort(ys,ts,ds,'2025-12-31')
        self.assertEqual((out[0]['first_juvenile_hip'],out[0]['selected_resale_hip'],out[0]['juvenile_event_count']),('12','64',2))
        self.assertEqual(out[0]['appreciation_usd'],328000)
        self.assertEqual(out[1]['outcome'],'no_2yo_sale_identified')
    def test_rna_bid_is_not_transaction_price(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'raw.csv'
            write_csv(p,[dict(hip='3',sire='Blame',dam='Example',foaling_date='2023-04-08',sex='F',status='RNA',price_usd='$90,000')],
                      ['hip','sire','dam','foaling_date','sex','status','price_usd'])
            rows=generic_csv(p,'TEST25',2025,'juvenile','test','https://example.test')
            self.assertEqual((rows[0]['status'],rows[0]['price_usd']),('rna',''))
            self.assertEqual(rows[0]['reported_bid_usd'],'90000.00')
if __name__=='__main__':unittest.main()
