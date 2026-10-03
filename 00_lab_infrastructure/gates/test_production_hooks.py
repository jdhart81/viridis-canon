import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from corpus_ledger import build
from mirror_parity import check_parity
from certificate_inspection import resolve_binding
from doi_triage import manuscript_diff
from production_hooks import publication_report


class ProductionHooksTests(unittest.TestCase):
    def test_inv8_one_byte_divergence_overrides_valid_certificate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'mirror';gen=Path(tmp)/'author'
            relative=Path('07_nightly_engine/compound research papers/Run-142_test')
            source=gen/relative;mirror=root/'science-engine'/relative
            source.mkdir(parents=True);mirror.mkdir(parents=True)
            for p in (source,mirror):
                (p/'candidate.lean').write_text('theorem witness : 1 = 1 := rfl')
            certdir=root/'certs/Run-142';certdir.mkdir(parents=True)
            (certdir/'LEAN_ZERO_SORRY_CERTIFICATE.json').write_text('{}')
            fixture={'valid':True,'run_id':'Run-142','candidate_path':str(mirror/'candidate.lean'),
                     'candidate_sha256':hashlib.sha256((mirror/'candidate.lean').read_bytes()).hexdigest(),
                     'path':str(certdir/'LEAN_ZERO_SORRY_CERTIFICATE.json')}
            with patch('corpus_ledger.inspect_certificate',return_value=fixture):
                clean=build(root,root/'certs',gen)
                self.assertEqual(clean['run_entities'][0]['status'],'CERTIFIED')
                (source/'candidate.lean').write_bytes((source/'candidate.lean').read_bytes()+b' ')
                drift=build(root,root/'certs',gen)
            self.assertEqual(drift['run_entities'][0]['status'],'MIRROR_DRIFT')
            self.assertFalse(drift['run_entities'][0]['certificate_valid'])
            self.assertEqual(drift['receipt_era']['certified'],0)
            self.assertEqual(drift['run_entities'][0]['flow']['state'],'MIRROR_DRIFT')

    def test_missing_extra_and_symlink_files_fail_parity(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a';b=Path(tmp)/'b';a.mkdir();b.mkdir()
            (a/'paper').write_text('a');(b/'paper').write_text('a')
            self.assertEqual(check_parity(a,b)['status'],'MATCH')
            (b/'extra').write_text('x');self.assertEqual(check_parity(a,b)['status'],'MIRROR_DRIFT')
            (b/'extra').unlink();(b/'link').symlink_to(a/'paper')
            self.assertEqual(check_parity(a,b)['status'],'MIRROR_DRIFT')
            self.assertEqual(check_parity(a,Path(tmp)/'missing')['status'],'MIRROR_DRIFT')

    def test_certificate_cannot_read_author_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'mirror';root.mkdir();source=Path(tmp)/'author.lean';source.write_text('proof')
            with patch.object(Path,'read_bytes',side_effect=AssertionError('outside file must not be read')):
                with self.assertRaises(ValueError):resolve_binding({'path':str(source),'sha256':'x'},root)

    def test_extra_finder_metadata_exception_does_not_mask_proof_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a';b=Path(tmp)/'b';a.mkdir();b.mkdir()
            (a/'proof.lean').write_bytes(b'proof');(b/'proof.lean').write_bytes(b'proof')
            (b/'.DS_Store').write_bytes(b'\x00\x00\x00\x01Bud1'+b'finder')
            report=check_parity(a,b)
            self.assertEqual(report['status'],'MATCH')
            self.assertEqual(len(report['ignored_metadata_differences']),1)
            (a/'proof.lean').write_bytes(b'Proof')
            self.assertEqual(check_parity(a,b)['status'],'MIRROR_DRIFT')

    def test_finder_name_alone_and_two_sided_metadata_difference_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a';b=Path(tmp)/'b';a.mkdir();b.mkdir()
            (a/'paper').write_text('same');(b/'paper').write_text('same')
            (b/'.DS_Store').write_bytes(b'not Finder metadata')
            self.assertEqual(check_parity(a,b)['status'],'MIRROR_DRIFT')
            (b/'.DS_Store').write_bytes(b'\x00\x00\x00\x01Bud1B')
            (a/'.DS_Store').write_bytes(b'\x00\x00\x00\x01Bud1A')
            self.assertEqual(check_parity(a,b)['status'],'MIRROR_DRIFT')

    def test_missing_runtime_inputs_report_hold_without_metadata_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);artifact=root/'deposit';artifact.mkdir();meta=artifact/'zenodo_metadata.json';meta.write_text('{"title":"Canon"}')
            before=meta.read_bytes();result=publication_report(root,artifact,'test')
            self.assertEqual(result['status'],'HOLD');self.assertFalse(result['enforcement']);self.assertFalse(result['zenodo_writes']);self.assertEqual(before,meta.read_bytes())

    def test_manuscript_numbers_and_hypotheses_are_substantive(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'sealed.tex';b=Path(tmp)/'published.tex'
            a.write_text('\\documentclass{article}\n\\begin{document} For n >= 1, 27131 tests passed.\\end{document}')
            b.write_text(a.read_text().replace('27131','26691'))
            self.assertEqual(manuscript_diff(a,b)['bucket'],'SUBSTANTIVE')
            b.write_text(a.read_text().replace('For n >= 1,','For all n,'))
            self.assertEqual(manuscript_diff(a,b)['bucket'],'SUBSTANTIVE')
            b.write_text(a.read_text().replace('article','report'))
            self.assertEqual(manuscript_diff(a,b)['bucket'],'COSMETIC')

    def test_snapshot_hashes_and_call_order(self):
        base=Path(__file__).parent/'production_snapshots';manifest=json.loads((base/'MANIFEST.json').read_text())
        for r in manifest['snapshots']:
            for field,hashfield in [('before_path','sha256'),('installed_path','installed_sha256')]:
                self.assertEqual(hashlib.sha256((base/r[field]).read_bytes()).hexdigest(),r[hashfield])
        publisher=(base/'installed/_ZENODO_DEPOSITS/publish_dated_bundles.py').read_text()
        self.assertLess(publisher.index('release_coherence.validate_bundle(bundle)'),publisher.index('verification_coverage_report(bundle,'))
        checkpoint=(base/'installed/RESEARCH_PIPELINE_v2/nightly_checkpoint.py').read_text()
        self.assertIn('write_new(output, result)\n        verification_coverage_after_checkpoint(output)',checkpoint)

if __name__=='__main__':unittest.main()
