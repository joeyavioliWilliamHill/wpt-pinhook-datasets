import json
import tempfile
import unittest
from pathlib import Path

from pinhook import fasig_results, obs_results
from pinhook.acquire import SOURCES, check
from pinhook.core import raw_or_json

FT_CSV = '''SESSION,HIP,SEX,SIRE,DAM,YEAR OF BIRTH,PURCHASER,PRICE,SIRE OF DAM,PROPERTY LINE
2024-07-09,1,C,SIRE,DAM,03/01/2023,SOME BUYER AGENT,40000,DAMSIRE,AGENT
2024-07-09,2,F,SIRE,DAM2,04/02/2023,NOT SOLD,13000,DAMSIRE,AGENT
2024-07-09,3,F,SIRE,DAM3,04/03/2023,"III STOOGES",40000,DAMSIRE,AGENT
2024-07-09,4,F,SIRE,DAM4,04/03/2023,OUT,0,,AGENT
'''
FT_JSON = [
    dict(id=1, sale=251, session='2024-07-09', hip=1, sex='C', sire='SIRE', dam='DAM', year_of_birth='03/01/2023',
         purchaser='Some Buyer, Agent', price='40000.00', sire_of_dam='DAMSIRE', property_line='AGENT', out=False),
    dict(id=2, sale=251, session='2024-07-09', hip=2, sex='F', sire='SIRE', dam='DAM2', year_of_birth='04/02/2023',
         purchaser='NOT SOLD', price='13000.00', sire_of_dam='DAMSIRE', property_line='AGENT', out=False),
    dict(id=3, sale=251, session='2024-07-09', hip=3, sex='F', sire='SIRE', dam='DAM3', year_of_birth='04/03/2023',
         purchaser='"III STOOGES"', price='40000.00', sire_of_dam='DAMSIRE', property_line='AGENT', out=False),
    dict(id=4, sale=251, session='2024-07-09', hip=4, sex='F', sire='SIRE', dam='DAM4', year_of_birth='04/03/2023',
         purchaser='OUT', price='0.00', sire_of_dam=None, property_line='AGENT', out=True),
]
OBS_CSV = '''Hip Number,Foaling Year,Foaling Date,Sex,Sire Name,Dam Name,IN Out Status,Buyer Name,Hammer Price,Horse Name,Dam Sire,Property Line 1
1,2023,02/19/2023,C,Sire,Dam,I,RNA,-30000,,Damsire,Agent
2,2023,02/13/2023,F,Sire,Dam2,I,RM 18 Stables,55000,,Damsire,Agent
3,2023,04/24/2023,F,Sire,Dam3,O,OUT,,,Damsire,Agent
'''
OBS_JSON = dict(sale_code='O325', sale_hip=[
    dict(hip_number='1', foaling_year='2023', foaling_date='02/19/2023', sex='C', sire_name='Sire', dam_name='Dam',
         in_out_status='I', buyer_name='RNA', hammer_price=-30000, horse_name='', dam_sire='Damsire', property_line_1='Agent'),
    dict(hip_number='2', foaling_year='2023', foaling_date='02/13/2023', sex='F', sire_name='Sire', dam_name='Dam2',
         in_out_status='I', buyer_name='RM 18 Stables', hammer_price='55000.00', horse_name='', dam_sire='Damsire', property_line_1='Agent'),
    dict(hip_number='3', foaling_year='2023', foaling_date='04/24/2023', sex='F', sire_name='Sire', dam_name='Dam3',
         in_out_status='O', buyer_name='OUT', hammer_price=None, horse_name='', dam_sire='Damsire', property_line_1='Agent'),
])
VOLATILE = {'source', 'raw_sha256'}


def strip(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if k not in VOLATILE} for r in rows]


class JsonFeedParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)

    def tearDown(self) -> None:
        self.dir.cleanup()

    def test_fasig_json_matches_csv_export(self) -> None:
        (self.root / 'a.csv').write_text(FT_CSV)
        (self.root / 'a.json').write_text(json.dumps(FT_JSON))
        csv_rows = fasig_results.normalize(self.root / 'a.csv', 'FTJUL24', 'yearling', 'u')
        json_rows = fasig_results.normalize(self.root / 'a.json', 'FTJUL24', 'yearling', 'u')
        self.assertEqual(strip(csv_rows), strip(json_rows))
        self.assertEqual([r['status'] for r in json_rows], ['sold', 'rna', 'sold', 'out'])
        self.assertEqual(json_rows[2]['buyer'], 'III STOOGES')
        self.assertEqual(json_rows[0]['source'], 'fasig_tipton_public_results_json')

    def test_obs_json_matches_csv_export(self) -> None:
        (self.root / 'a.csv').write_text(OBS_CSV)
        (self.root / 'a.json').write_text(json.dumps(OBS_JSON))
        csv_rows, _ = obs_results.normalize(self.root / 'a.csv', 'march')
        json_rows, _ = obs_results.normalize(self.root / 'a.json', 'march')
        self.assertEqual(strip(csv_rows), strip(json_rows))
        self.assertEqual([r['reported_bid_usd'] for r in json_rows], ['30000.00', '', ''])

    def test_raw_or_json_prefers_original_export(self) -> None:
        csv_path = self.root / 'ft_july24_results.csv'
        self.assertEqual(raw_or_json(csv_path), csv_path)
        csv_path.with_suffix('.json').write_text('[]')
        self.assertEqual(raw_or_json(csv_path), csv_path.with_suffix('.json'))
        csv_path.write_text(FT_CSV)
        self.assertEqual(raw_or_json(csv_path), csv_path)


class CheckTest(unittest.TestCase):
    def test_rejects_wrong_fasig_sale(self) -> None:
        source = next(s for s in SOURCES if s.raw == 'ft_july24_results.json')
        with self.assertRaisesRegex(ValueError, 'sale'):
            check(source, json.dumps([dict(FT_JSON[0], sale=999)]).encode())
        self.assertEqual(check(source, json.dumps(FT_JSON).encode()), 4)

    def test_rejects_wrong_or_incomplete_obs_sale(self) -> None:
        source = next(s for s in SOURCES if s.raw == 'obs_march25_results.json')
        rows = [dict(r, sale_id=str(source.sale_id)) for r in OBS_JSON['sale_hip']]
        self.assertEqual(check(source, json.dumps(dict(sale_id=str(source.sale_id), sale_hip=rows)).encode()), 3)
        with self.assertRaisesRegex(ValueError, 'sale'):
            check(source, json.dumps(dict(sale_id='999', sale_hip=[dict(r, sale_id='999') for r in rows])).encode())
        with self.assertRaises(KeyError):
            check(source, json.dumps(dict(sale_id=str(source.sale_id), sale_hip=[dict(sale_id=str(source.sale_id))])).encode())

    def test_rejects_html_instead_of_workbook(self) -> None:
        source = next(s for s in SOURCES if s.raw == 'obs_march23_results.xls')
        with self.assertRaises(ValueError):
            check(source, b'<html>not found</html>')

    def test_every_rebuild_input_has_a_source(self) -> None:
        outputs = {s.output for s in SOURCES}
        for year in (2022, 2023, 2024):
            y, j = str(year)[-2:], str(year + 1)[-2:]
            for stem in ('kee_sep', 'ft_ky_oct', 'ft_saratoga', 'ft_nybred', 'ft_july'):
                self.assertIn(f'{stem}{y}_full.csv', outputs)
            for stem in ('obs_march', 'obs_spring', 'obs_june'):
                self.assertIn(f'{stem}{j}_full.csv', outputs)
            self.assertIn('ft_may25_results_full.csv' if year == 2024 else f'ft_may{j}_full.csv', outputs)


if __name__ == '__main__':
    unittest.main()
