import unittest

from pinhook.enrich_catalog import enrich


class CatalogEnrichmentTest(unittest.TestCase):
    def test_impossible_calendar_date_is_quarantined(self):
        result = dict(sale_code='KEESEP19', hip='18', status='sold', price_usd='190000.00',
                      sire='Into Mischief', dam='Example Dam', sex='Filly', foaling_year='2018',
                      foaling_date='', raw_sha256='result_hash')
        page = dict(hip='18', sire='Into Mischief', dam='Example Dam', sex='F',
                    foaling_date='2018-02-30', source_url='https://example.test/18.pdf',
                    raw_pdf_sha256='catalog_hash')
        rows, evidence = enrich([result], [page])
        self.assertEqual(rows[0]['foaling_date'], '')
        self.assertIn('invalid_or_missing_birth_date', evidence[0]['reason'])

    def test_conflicting_full_sibling_does_not_gain_birth_date(self):
        result = dict(sale_code='KEESEP19', hip='18', status='sold', price_usd='190000.00',
                      sire='Into Mischief', dam='Example Dam', sex='Filly', foaling_year='2018',
                      foaling_date='', raw_sha256='result_hash')
        sibling_page = dict(hip='18', sire='Into Mischief', dam='Example Dam', sex='Filly',
                            foaling_date='2017-04-09', source_url='https://example.test/18.pdf',
                            raw_pdf_sha256='catalog_hash')
        rows, evidence = enrich([result], [sibling_page])
        self.assertEqual(rows[0]['foaling_date'], '')
        self.assertIn('birth_year_conflict', evidence[0]['reason'])
        self.assertEqual(rows[0]['price_usd'], '190000.00')

    def test_exact_catalog_page_preserves_sale_provenance(self):
        result = dict(sale_code='KEESEP19', hip='18', status='sold', price_usd='190000.00',
                      sire='Into Mischief', dam='Example Dam', sex='Filly', foaling_year='2018',
                      foaling_date='', raw_sha256='result_hash')
        page = dict(hip='18', sire='INTO MISCHIEF', dam='Example Dam', sex='F',
                    foaling_date='2018-04-09', source_url='https://example.test/18.pdf',
                    source_page='18', raw_pdf_sha256='catalog_hash')
        rows, evidence = enrich([result], [page])
        self.assertEqual(rows[0]['foaling_date'], '2018-04-09')
        self.assertEqual(rows[0]['raw_sha256'], 'result_hash')
        self.assertEqual(evidence[0]['catalog_raw_pdf_sha256'], 'catalog_hash')


if __name__ == '__main__': unittest.main()
