import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from run_flow import flow

class CurrentReceiptFlowTests(unittest.TestCase):
    def test_fresh_certified_attempt_ignores_historical_failed_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);old=root/'RESEARCH_PIPELINE_v2/lean_certificates/Run-177';old.mkdir(parents=True)
            (old/'COMPARATOR_CLOUD_RECEIPT.json').write_text(json.dumps({'status':'HOLD','provider_response':{'output':'old error'}}))
            cert=old/'LEAN_ZERO_SORRY_CERTIFICATE.json';cert.write_text(json.dumps({'bindings':{'independent_cloud_receipt':{'path':'new','sha256':'hash'}}}))
            fresh=root/'new';fresh.write_text(json.dumps({'status':'VERIFIED'}))
            row={'id':'Run-177','status':'CERTIFIED','certificate_valid':True,'certificate':str(cert),'path':'paper'}
            with patch('certificate_inspection.inspect_certificate',return_value={'valid':True}),patch('certificate_inspection.resolve_binding',return_value=fresh):
                result=flow(root,row)
            self.assertEqual(result['state'],'CERTIFIED');self.assertEqual(result['causes'],[])
            self.assertEqual(result['receipts'][0]['path'],str(fresh))
            self.assertEqual(json.loads((old/'COMPARATOR_CLOUD_RECEIPT.json').read_text())['status'],'HOLD')

    def test_invalid_current_certificate_is_held(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);row={'id':'Run-177','status':'CERTIFIED','certificate_valid':True,'certificate':str(root/'missing'),'path':'paper'}
            with patch('certificate_inspection.inspect_certificate',return_value={'valid':False}):result=flow(root,row)
            self.assertEqual(result['state'],'HOLD_MISSING_OR_MALFORMED_RECEIPT')

    def test_drift_precedes_even_a_recorded_certificate(self):
        result=flow(Path('/unread'),{'id':'Run-177','status':'MIRROR_DRIFT','certificate_valid':True})
        self.assertEqual(result['state'],'MIRROR_DRIFT')
