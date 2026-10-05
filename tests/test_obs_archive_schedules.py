import unittest
from pinhook.obs_legacy_excel import SALES

class ArchiveScheduleTest(unittest.TestCase):
 def day(self,sale,hip):
  return next(d for lo,hi,d in SALES[sale][2] if lo<=hip<=hi)
 def test_postponed_2020_spring_and_supplements(self):
  self.assertEqual(self.day('spring20',1),'2020-06-09')
  self.assertEqual(self.day('spring20',1253),'2020-06-10')
  self.assertEqual(self.day('spring20',1315),'2020-06-12')
 def test_july_not_june_2020(self):
  self.assertEqual(SALES['july20'][0],'OBSJUL20')
  self.assertEqual(self.day('july20',1114),'2020-07-16')
 def test_2021_session_boundaries(self):
  self.assertEqual(self.day('march21',283),'2021-03-17')
  self.assertEqual(self.day('spring21',913),'2021-04-23')
  self.assertEqual(self.day('june21',880),'2021-06-11')
