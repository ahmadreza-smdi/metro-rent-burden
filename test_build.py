"""Hand-worked denominator/unknown/geography-independent arithmetic checks."""
import unittest
from build import measures

def fixture(values):return {f'B25070_E{i:03}':str(v) for i,v in enumerate(values,1)}
class Arithmetic(unittest.TestCase):
 def test_excludes_not_computed_instead_of_diluting_share(self):
  r=measures(fixture([100,10,10,10,5,5,10,10,10,10,20]))
  self.assertEqual((r['computable_units'],r['rent_30plus_units'],r['rent_50plus_units']),(80,40,10))
  self.assertEqual((r['rent_30plus_pct'],r['rent_50plus_pct']),(50,12.5))
 def test_all_computable_is_severely_burdened(self):
  r=measures(fixture([10,0,0,0,0,0,0,0,0,10,0]))
  self.assertEqual((r['rent_30plus_pct'],r['rent_50plus_pct']),(100,100))
 def test_zero_denominator_is_not_zero_burden(self):
  r=measures(fixture([10,0,0,0,0,0,0,0,0,0,10]))
  self.assertIsNone(r['rent_30plus_pct']);self.assertIsNone(r['rent_50plus_pct'])
 def test_unavailable_is_not_zero(self):
  r=fixture([100,10,10,10,5,5,10,10,10,10,20]);r['B25070_E010']='-666666666'
  self.assertEqual(measures(r)['status'],'unavailable source estimate')
 def test_missing_category_is_not_zero(self):
  r=fixture([100,10,10,10,5,5,10,10,10,10,20]);del r['B25070_E007']
  self.assertEqual(measures(r)['status'],'unavailable source estimate')
 def test_nonadditive_source_fails_closed(self):
  with self.assertRaises(ValueError):measures(fixture([101,10,10,10,5,5,10,10,10,10,20]))
if __name__=='__main__':unittest.main()
