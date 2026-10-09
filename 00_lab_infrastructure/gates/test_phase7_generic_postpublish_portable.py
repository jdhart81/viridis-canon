"""Portable generic publication closeout preservation tests."""
import importlib.util, unittest, hashlib
from pathlib import Path

class Portable(unittest.TestCase):
    def test_postpublish_preserving_composition(self):
        gates=Path(__file__).parent
        fixture=gates/'tests/fixtures/phase7_generic_postpublish_v002'
        self.assertEqual((gates/'postpublish_digest.py').read_bytes(),(fixture/'postpublish_digest.py').read_bytes())
        self.assertEqual(hashlib.sha256((fixture/'postpublish_digest.py').read_bytes()).hexdigest(),'bae5d31235556296659141394c25e27b2df4b1088cf4c4feaf06e12650fbb830')
        self.assertEqual(hashlib.sha256((fixture/'coverage_provenance.py').read_bytes()).hexdigest(),'6892093f0c10f7697ca06d259b0e629b7eaa7bf19b4f747db56447c2cbbb1bec')
        target=fixture/'test_postpublish_digest.py'
        spec=importlib.util.spec_from_file_location('postpublish_portable_fixture',target)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        suite=unittest.defaultTestLoader.loadTestsFromModule(module)
        result=unittest.TestResult();suite.run(result)
        self.assertEqual(result.testsRun,41)
        self.assertTrue(result.wasSuccessful(),str(result.errors)+str(result.failures))
