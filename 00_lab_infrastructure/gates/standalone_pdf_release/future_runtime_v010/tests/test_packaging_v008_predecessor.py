"""V007 source-only predecessor fixtures; no operational imports or admission."""
import contextlib
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import packaging_runtime as runtime


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, sort_keys=True, indent=2) + '\n').encode())
    return {'path': str(path), 'sha256': runtime.sha(path.read_bytes())}


class FrozenV007PredecessorTests(unittest.TestCase):
    def fixture(self, root):
        candidate, installed = root / 'candidate', root / 'installed'
        candidate.mkdir(); installed.mkdir()
        sources, modules, git = [], [], []
        for name in sorted(runtime.MODULE_NAMES):
            raw = ('# synthetic exact prior source ' + name + '\n').encode()
            for directory in (candidate, installed):
                (directory / name).write_bytes(raw)
            row = {'name': name, 'path': str(candidate / name), 'sha256': runtime.sha(raw),
                   'git_path': '00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v007/' + name}
            sources.append(row); modules.append({**row, 'path': str(installed / name)})
            git.append({'path': row['git_path'], 'type': 'blob', 'mode': '100644',
                        'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()})
        pr = put(root, 'pr.json', {'state': 'MERGED', 'baseRefName': 'main', 'number': 999,
             'url': 'https://github.com/jdhart81/viridis-canon/pull/999', 'mergeCommit': {'oid': 'a' * 40},
             'statusCheckRollup': [{'name': n, 'status': 'COMPLETED', 'conclusion': 'SUCCESS'}
                                  for n in runtime.REQUIRED_CHECKS]})
        commit = put(root, 'commit.json', {'sha': 'a' * 40, 'tree': {'sha': 'b' * 40}})
        tree = put(root, 'tree.json', {'sha': 'b' * 40, 'truncated': False, 'tree': git})
        anchor = put(root, 'anchor.json', {'synthetic_only': True})
        descriptor = put(root, 'descriptor.json', {'synthetic_only': True, 'writes': 0})
        review = put(root, 'review.json', {'standard': 'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-7',
             'status':'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS', 'reviewer':'explicit synthetic prior7 fixture',
             'legacy_closure':runtime.LEGACY_CLOSURE, **runtime.SOURCE_REVIEW_CHANGE_FLAGS,
             'review_scope': 'SOURCE_ONLY', 'actual_live_runtime_admission': False,
             'actual_seven_record_admission': 'PENDING_POST_INSTALL_FRESH_READBACK',
             'source_hashes': {r['name']: r['sha256'] for r in sources}})
        shared = {'source_origin': {'pull_request': pr, 'merge_commit': commit, 'tree': tree},
                  'source_review': review, 'user_authority': anchor, 'access_registry': anchor,
                  'installed_at_utc': '2020-01-01T00:00:00Z', 'legacy_closure':runtime.LEGACY_CLOSURE,
                  'transient_rehydration': runtime.TRANSIENT_REHYDRATION_POLICY,
                  'predecessor_installation': {'v001': runtime.V001_INSTALLATION,
                      'v002': runtime.V002_INSTALLATION, 'v003': runtime.V003_INSTALLATION,
                      'v004': runtime.V004_INSTALLATION, 'v005':runtime.V005_INSTALLATION,
                      'v006': runtime.V006_INSTALLATION},
                  'data_alias_observation': descriptor, 'platform_timezone_observation': descriptor}
        profile = put(root, 'profile.json', {'standard': 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-7',
                      'canonical_root': str(root), 'modules': modules, **shared})
        plan = put(root, 'plan.json', {'standard': 'VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-7',
                   'source_modules': sources, 'root_review': anchor, **shared})
        nomination = put(root, 'nomination.json', {
             'standard': 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-7',
             'status': 'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING',
             'profile': profile, 'merged_source_commit': 'a' * 40, 'root_review_receipt': anchor,
             'installer_source': {k: next(r for r in sources if r['name'] == 'install_packaging_runtime.py')[k]
                                  for k in ('path', 'sha256')}})
        publisher = root / 'publisher.py'; publisher.write_bytes(b'# unchanged synthetic publisher\n')
        failed = put(root, 'failed-health.json', {'synthetic_only': True, 'actual_child_exit_code': 1,
                     'status': 'HOLD', 'runtime_admission': False, 'clock_reset': False})
        bindings = {'V007_PROFILE': profile, 'V007_PLAN': plan, 'V007_NOMINATION': nomination,
                    'DATA_ALIAS_OBSERVATION': descriptor, 'PLATFORM_TIMEZONE_OBSERVATION': descriptor,
                    'HISTORICAL_PUBLISHER': {'path': str(publisher), 'sha256': runtime.sha(publisher.read_bytes())}}
        return bindings, sources, modules, failed

    def consume(self, root, bindings):
        with contextlib.ExitStack() as stack:
            for key, value in bindings.items():
                stack.enter_context(patch.object(runtime, key, value))
            stack.enter_context(patch.object(runtime, 'v006_predecessor_installation',
                 return_value={'prior_six': 'covered independently; source-only, no live verdict'}))
            stack.enter_context(patch.object(runtime, 'load', side_effect=AssertionError('no executable prior load')))
            return runtime.v007_predecessor_installation(root)

    def test_actual_v007_metadata_pins_and_all_seven_predecessors_are_explicit(self):
        self.assertEqual(runtime.V007_PROFILE, {'path': '_ZENODO_DEPOSITS/standalone_pdf_runtime_v007/CURRENT_PACKAGING_PROFILE.json',
             'sha256': '43a622c303ffbc33ced51fc04f30ae65de3d1a2a73356ad0005e7e69ad1a9669'})
        self.assertEqual(runtime.V007_NOMINATION, {'path': '_ZENODO_DEPOSITS/standalone_pdf_runtime_v007/INSTALLATION_NOMINATION.json',
             'sha256': '88bd6d9721f1750f99a0cec21e4e82382740a9ea4c772e722f3f097a0c8f1bf7'})
        self.assertEqual(runtime.V007_PLAN, {'path': '_ZENODO_DEPOSITS/standalone_pdf_runtime_v007/INSTALL_PLAN.json',
             'sha256': 'af0ada870f8f3d837c44872178e8ca47e1bd559eb8a79f2cb292029933136421'})
        self.assertEqual(set(runtime.PREDECESSOR_INSTALLATION), {'v001', 'v002', 'v003', 'v004', 'v005', 'v006', 'v007', 'v008', 'v009'})
        self.assertTrue(runtime.PROFILE_PATH.startswith('_ZENODO_DEPOSITS/standalone_pdf_runtime_v010/'))
        self.assertTrue(runtime.GIT_PREFIX.endswith('/future_runtime_v010/'))

    def test_complete19_source_proofs_preserve_failed_receipt_and_claim_no_runtime_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); bindings, sources, modules, failed = self.fixture(root)
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            value = self.consume(root, bindings)
            self.assertFalse(value['actual_runtime_admission']); self.assertFalse(value['certifies'])
            self.assertEqual(len(value['v007']['merged_source']['proofs']), 19)
            self.assertIn('SOURCE_READBACK_ONLY', value['status'])
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertFalse(json.loads(Path(failed['path']).read_bytes())['runtime_admission'])

    def test_changed_source_installed_or_any_fixed_metadata_holds_without_overwrite(self):
        for field in ('source', 'installed', 'profile', 'plan', 'nomination'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve(); bindings, sources, modules, _ = self.fixture(root)
                path = Path(sources[0]['path'] if field == 'source' else modules[0]['path'] if field == 'installed'
                            else bindings['V007_' + field.upper()]['path'])
                changed = path.read_bytes() + b'changed'; path.write_bytes(changed)
                with self.assertRaises(runtime.PackagingHold): self.consume(root, bindings)
                self.assertEqual(path.read_bytes(), changed)

    def test_missing_source_installed_or_fixed_metadata_holds_without_recreation(self):
        for field in ('source', 'installed', 'profile', 'plan', 'nomination'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve(); bindings, sources, modules, _ = self.fixture(root)
                path = Path(sources[0]['path'] if field == 'source' else modules[0]['path'] if field == 'installed'
                            else bindings['V007_' + field.upper()]['path'])
                path.unlink()
                with self.assertRaises(runtime.PackagingHold): self.consume(root, bindings)
                self.assertFalse(path.exists())

    def test_rebound_fake_pass_or_wrong_nomination_relation_still_holds(self):
        for field in ('status', 'root_review_receipt'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve(); bindings, _, _, _ = self.fixture(root)
                value = json.loads(Path(bindings['V007_NOMINATION']['path']).read_bytes())
                value[field] = ('FRESH_DEFAULT_FULL_POPULATION_READBACK_PASS' if field == 'status'
                                else put(root, 'unrelated-review.json', {'synthetic_only': True}))
                bindings['V007_NOMINATION'] = put(root, 'nomination.json', value)
                with self.assertRaises(runtime.PackagingHold): self.consume(root, bindings)

    def test_missing_or_escaped_source_origin_cannot_supply_genuine_provenance(self):
        for kind in ('missing', 'escape'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve(); bindings, _, _, _ = self.fixture(root)
                profile = json.loads(Path(bindings['V007_PROFILE']['path']).read_bytes())
                origin = profile['source_origin']['tree']
                if kind == 'missing': Path(origin['path']).unlink()
                else:
                    with tempfile.TemporaryDirectory() as outside:
                        target = Path(outside).resolve() / 'tree.json'
                        target.write_bytes(Path(origin['path']).read_bytes())
                        profile['source_origin']['tree'] = {'path': str(target), 'sha256': origin['sha256']}
                        bindings['V007_PROFILE'] = put(root, 'profile.json', profile)
                        nomination = json.loads(Path(bindings['V007_NOMINATION']['path']).read_bytes())
                        nomination['profile'] = bindings['V007_PROFILE']
                        bindings['V007_NOMINATION'] = put(root, 'nomination.json', nomination)
                        with self.assertRaisesRegex(runtime.PackagingHold, 'REGULAR_CONTAINED_SOURCE'):
                            self.consume(root, bindings)
                    continue
                with self.assertRaises(runtime.PackagingHold): self.consume(root, bindings)

    def test_source_origin_recreated_during_read_is_rejected_by_fresh_six_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); bindings, _, _, _ = self.fixture(root)
            real = Path.read_bytes; fired = []
            def race(path):
                raw = real(path)
                if path == root / 'tree.json' and not fired:
                    replacement = root / 'replacement.json'; replacement.write_bytes(raw)
                    replacement.replace(path); fired.append(True)
                return raw
            with patch.object(Path, 'read_bytes', race):
                with self.assertRaisesRegex(runtime.PackagingHold, 'SOURCE_HASH_OR_RACE'):
                    self.consume(root, bindings)
            self.assertTrue(fired)

    def test_namespace_cardinality_is19_for_v7_and_current_but17_for_six_older(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); bindings, sources, modules, _ = self.fixture(root)
            for prefix in ('00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v007/', runtime.GIT_PREFIX):
                rows = [{**r, 'git_path': prefix+r['name']} for r in sources]
                self.assertEqual(len(runtime.module_table(root, rows, git_prefix=prefix)), 19)
                with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_ADDITIVE_MODULES'):
                    runtime.module_table(root, [r for r in rows if r['name'] in runtime.FROZEN_MODULE_NAMES], git_prefix=prefix)
            for version in range(1,7):
                prefix = '00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v'+str(version).zfill(3)+'/'
                rows = [{**r, 'git_path': prefix+r['name']} for r in sources]
                old = [r for r in rows if r['name'] in runtime.FROZEN_MODULE_NAMES]
                self.assertEqual(len(runtime.module_table(root, old, git_prefix=prefix)),17)
                with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_ADDITIVE_MODULES'):
                    runtime.module_table(root, rows, git_prefix=prefix)
            with self.assertRaisesRegex(runtime.PackagingHold, 'FIXED_MODULE_TABLE_NAMESPACE'):
                runtime.module_table(root, sources, git_prefix='unreviewed/namespace/')

    def test_each_new_v7_worker_source_is_required_and_cannot_be_dropped(self):
        for name in ('scientific_registration_worker.py','owner_content_worker.py'):
            for location in ('source','installed'):
                with self.subTest(name=name,location=location), tempfile.TemporaryDirectory() as tmp:
                    root=Path(tmp).resolve();bindings,sources,modules,_=self.fixture(root)
                    rows=sources if location=='source' else modules
                    path=Path(next(r['path']for r in rows if r['name']==name))
                    original=path.read_bytes();path.write_bytes(original+b'changed')
                    with self.assertRaises(runtime.PackagingHold):self.consume(root,bindings)
                    self.assertEqual(path.read_bytes(),original+b'changed')

    def test_v7_source_only_review_must_retain_exact_nine_flags(self):
        for field in (*runtime.SOURCE_REVIEW_CHANGE_FLAGS, 'actual_live_runtime_admission'):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();bindings,_,_,_=self.fixture(root)
                profile=json.loads(Path(bindings['V007_PROFILE']['path']).read_bytes())
                review=json.loads(Path(profile['source_review']['path']).read_bytes())
                review[field]=not review[field]
                profile['source_review']=put(root,'review.json',review)
                bindings['V007_PROFILE']=put(root,'profile.json',profile)
                plan=json.loads(Path(bindings['V007_PLAN']['path']).read_bytes())
                plan['source_review']=profile['source_review'];bindings['V007_PLAN']=put(root,'plan.json',plan)
                nomination=json.loads(Path(bindings['V007_NOMINATION']['path']).read_bytes())
                nomination['profile']=bindings['V007_PROFILE'];bindings['V007_NOMINATION']=put(root,'nomination.json',nomination)
                with self.assertRaisesRegex(runtime.PackagingHold,'FROZEN_V007_SOURCE_REVIEW_SCOPE'):
                    self.consume(root,bindings)

    def test_six_older_predecessor_body_is_literal_preserved_v7_body(self):
        import ast
        here=Path(__file__).resolve().parents[1]
        before_path=here.parent/'future_runtime_v007/packaging_runtime.py'
        before=before_path.read_text();after=(here/'packaging_runtime.py').read_text()
        original=next(n for n in ast.parse(before).body if isinstance(n,ast.FunctionDef)and n.name=='predecessor_installation')
        copied=next(n for n in ast.parse(after).body if isinstance(n,ast.FunctionDef)and n.name=='v006_predecessor_installation')
        self.assertEqual(ast.get_source_segment(before,original),
            ast.get_source_segment(after,copied).replace('def v006_predecessor_installation(', 'def predecessor_installation(',1))


if __name__ == '__main__': unittest.main()
