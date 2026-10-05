import unittest
from pinhook.keeneland_catalog import extract_page

class ArchivedHeaderTest(unittest.TestCase):
 def test_2019_sex_on_separate_line(self):
  text='Consigned by Example Farm, Agent\nBAY COLT\nFoaled April 3, 2018\nInto Mischief ........................\nUrloveisasymphony ....................\nBy INTO MISCHIEF (2005).\n1st dam\nURLOVEISASYMPHONY, by Forest Wildcat.\nHip No.\n176\n'
  row,reasons,_=extract_page(text,1,'176.pdf','https://secure.keeneland.com/sales/Sep19/pdfs/')
  self.assertEqual(reasons,[])
  self.assertEqual(row['hip'],'176')
  self.assertEqual(row['sex'],'C')
  self.assertEqual(row['foaling_date'],'2018-04-03')
  self.assertEqual(row['dam'],'Urloveisasymphony')
