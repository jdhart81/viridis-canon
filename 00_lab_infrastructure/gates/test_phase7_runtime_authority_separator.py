"""The exact approved appended separator never broadens runtime authority."""
import ast
from pathlib import Path
import hashlib
import unittest
import phase7_runtime_update as runtime

FIXTURES = Path(__file__).parent/'testdata/phase7_runtime_authority'

class AuthoritySeparatorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.old=(FIXTURES/'APPROVED_SECTION.md').read_bytes()
  cls.decoupling=(FIXTURES/'DECOUPLING_SECTION.md').read_bytes()
  cls.simplification=(FIXTURES/'SIMPLIFICATION_SECTION.md').read_bytes()
  cls.current=b'# Prior plan\n\n'+cls.old+b'\n---\n\n'+cls.decoupling+b'\n'+cls.simplification
 def accepted(self,raw):
  result=runtime.audit_section(raw)
  if hashlib.sha256(result).hexdigest()!=runtime.APPROVED_AUDIT_SECTION_SHA256 or result!=self.old:raise ValueError('runtime update lacks exact approved audit authority')
  return result
 def test_exact_old_authority_passes(self):self.assertEqual(self.accepted(self.old),self.old)
 def test_exact_current_separator_with_two_pinned_sections_passes(self):self.assertEqual(self.accepted(self.current),self.old)
 def test_actual_fixture_pins_match_literals(self):
  self.assertEqual(hashlib.sha256(self.old).hexdigest(),runtime.APPROVED_AUDIT_SECTION_SHA256)
  self.assertEqual([hashlib.sha256(v).hexdigest()for v in (self.decoupling,self.simplification)],[row[1]for row in runtime.APPROVED_AUDIT_APPENDICES])
 def test_changed_old_approval_fails(self):
  with self.assertRaises(ValueError):self.accepted(self.current.replace(self.old,self.old[:-2]+b'X\n',1))
 def test_changed_decoupling_fails(self):
  with self.assertRaisesRegex(ValueError,'appendix bytes differ'):self.accepted(self.current.replace(self.decoupling,self.decoupling.replace(b'Witness bundle',b'Altered bundle',1)))
 def test_changed_simplification_fails(self):
  with self.assertRaisesRegex(ValueError,'appendix bytes differ'):self.accepted(self.current.replace(self.simplification,self.simplification+b'Unapproved extra authority.\n'))
 def test_duplicate_old_header_fails(self):
  with self.assertRaisesRegex(ValueError,'unique approved audit section'):self.accepted(self.current+b'\n'+self.old)
 def test_duplicate_decoupling_header_fails(self):
  with self.assertRaisesRegex(ValueError,'unique exact approved authority appendix'):self.accepted(self.current+b'\n'+self.decoupling)
 def test_duplicate_simplification_header_fails(self):
  with self.assertRaises(ValueError):self.accepted(self.current+b'\n'+self.simplification)
 def test_arbitrary_padding_after_old_approval_fails(self):
  with self.assertRaises(ValueError):self.accepted(self.current.replace(self.old+b'\n---\n',self.old+b' \n---\n',1))
 def test_second_separator_after_old_approval_fails(self):
  with self.assertRaises(ValueError):self.accepted(self.current.replace(self.old+b'\n---\n',self.old+b'\n---\n\n---\n',1))
 def test_missing_decoupling_pin_fails(self):
  with self.assertRaisesRegex(ValueError,'unique exact approved authority appendix'):self.accepted(b'# Prior\n'+self.old+b'\n---\n\n'+self.simplification)
 def test_missing_simplification_pin_fails(self):
  with self.assertRaises(ValueError):self.accepted(b'# Prior\n'+self.old+b'\n---\n\n'+self.decoupling)
 def test_separator_without_either_appendix_fails(self):
  with self.assertRaises(ValueError):self.accepted(self.old+b'\n---\n')
 def test_single_newline_suffix_fails(self):
  with self.assertRaises(ValueError):self.accepted(self.old+b'\n')
 def test_reordered_appendices_fail(self):
  with self.assertRaises(ValueError):self.accepted(self.old+b'\n---\n\n'+self.simplification+b'\n'+self.decoupling)

if __name__=='__main__':unittest.main()
