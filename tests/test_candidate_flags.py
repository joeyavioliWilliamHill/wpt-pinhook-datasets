import unittest

from pinhook.core import candidates
from pinhook.multi_sale_cohort import build


def entry(sale, hip, sale_type, date, status='sold'):
    return dict(sale_code=sale, hip=str(hip), sale_type=sale_type,
                sale_date=date, status=status, price_usd='50000' if status == 'sold' else '',
                reported_bid_usd='', foaling_year='2021', foaling_date='2021-02-19',
                sex='C', sire='Maximus Mischief', dam='L. A. Way', source_url='example')


class CandidateFlagsTest(unittest.TestCase):
    def test_repeat_juvenile_events_do_not_imply_competing_yearlings(self):
        yearlings = [entry('FTJUL22', 8, 'yearling', '2022-07-12')]
        juveniles = [entry('OBSMAR23', 603, 'juvenile', '2023-03-22', 'out'),
                     entry('FTMMAY23', 253, 'juvenile', '2023-05-22')]
        links = candidates(yearlings, juveniles)
        self.assertEqual(len(links), 2)
        self.assertTrue(all(p['multiple_juvenile_events'] == 'true' for p in links))
        self.assertTrue(all(p['competing_yearling_candidates'] == 'false' for p in links))
        result = build(yearlings, juveniles, links)[0]
        self.assertEqual(result['identity_decision'], 'review')
        self.assertEqual(result['outcome_in_covered_sales'], 'sold_at_2yo')
        self.assertEqual(result['multiple_juvenile_events'], 'true')
        self.assertEqual(result['competing_yearling_candidates'], 'false')

    def test_same_juvenile_matched_to_two_yearling_entries_needs_review(self):
        yearlings = [entry('FTJUL22', 8, 'yearling', '2022-07-12'),
                     entry('FTKYOCT22', 100, 'yearling', '2022-10-24')]
        juveniles = [entry('FTMMAY23', 253, 'juvenile', '2023-05-22')]
        links = candidates(yearlings, juveniles)
        self.assertTrue(all(p['multiple_juvenile_events'] == 'false' for p in links))
        self.assertTrue(all(p['competing_yearling_candidates'] == 'true' for p in links))
        rows = build(yearlings, juveniles, links)
        self.assertTrue(all(r['outcome_in_covered_sales'] == 'ambiguous_identity_review' for r in rows))
        self.assertTrue(all(r['appreciation_usd'] == '' for r in rows))


if __name__ == '__main__':
    unittest.main()
