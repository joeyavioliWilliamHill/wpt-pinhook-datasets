import json,tempfile,unittest
from pathlib import Path
from pinhook.fasig_api_results import normalize

class PublicResultsTest(unittest.TestCase):
 def test_rna_bid_is_not_proceeds_and_raw_id_is_preserved(self):
  row=dict(id=73150,hip=3,session='2022-03-30',year_of_birth='02/12/2020',purchaser='NOT SOLD',price='75000.00',sex='C',sire='Sire',dam='Dam')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.json';p.write_text(json.dumps([row]));r=normalize(p,'FTGULF22','https://example.test/sale')[0]
  self.assertEqual(r['status'],'rna');self.assertEqual(r['price_usd'],'');self.assertEqual(r['reported_bid_usd'],'75000.00');self.assertEqual(r['source_entry_id'],'73150')
 def test_racing_age_record_rejected(self):
  row=dict(id=1,hip=1,session='2022-03-30',year_of_birth='02/12/2019',purchaser='OUT',price='0',sex='C',sire='Sire',dam='Dam')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.json';p.write_text(json.dumps([row]))
   with self.assertRaisesRegex(ValueError,'not a juvenile'):normalize(p,'FTGULF22','https://example.test/sale')
