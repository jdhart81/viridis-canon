"""Portable exact-boundary regression fixtures; no live tree or network."""
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
import phase7_policy_versions as versions
import phase7_runtime_update as runtime

HERE = Path(__file__).parent
RAW = (HERE/'fixtures/authority_framing/GAME_PLAN_SECTIONS.md').read_bytes()

class PortableAuthorityFraming(unittest.TestCase):
    def test_exact_boundary_delta_and_old_scientific_pin(self):
        view = versions.normalize_authority_plan(RAW)
        self.assertEqual(len(RAW)-len(view),5)
        a,b = versions._authority_section(view,versions.SIMPLIFICATION_HEADER)
        self.assertEqual(hashlib.sha256(view[a:b]).hexdigest(),versions.SIMPLIFICATION_SHA256)
        self.assertEqual(versions.normalize_authority_plan(view),view)

    def test_old_audit_identity_preserved(self):
        audit = runtime.audit_section(RAW)
        self.assertEqual(hashlib.sha256(audit).hexdigest(),runtime.APPROVED_AUDIT_SECTION_SHA256)

    def test_prior_plan_has_no_normalization(self):
        old = RAW[:RAW.index(versions.APPENDIX_HEADER.encode())]
        self.assertEqual(versions.normalize_authority_plan(old),old)

    def test_new_approved_appendix_terminal_separator_only(self):
        self.assertEqual(versions.normalize_authority_plan(RAW+versions.SUFFIX),versions.normalize_authority_plan(RAW)+versions.SUFFIX)
        with self.assertRaises(ValueError):
            versions.normalize_authority_plan(RAW+versions.SUFFIX+versions.SUFFIX)

    def test_each_minimal_gate_scientific_mutation_holds(self):
        changes = [(b'1. **Certificate:**',b'1. **No certificate:**'),(b'2. **Scope:**',b'2. **Scope waiver:**'),(b'3. **INV-9:**',b'3. **INV-9 bypass:**'),(b'4. **Binding:**',b'4. **Binding optional:**'),(b'5. **Disclaimer:**',b'5. **No disclaimer:**'),(b'10 writes/day',b'100 writes/day'),(b'Nothing else blocks publication.',b'Everything else blocks publication.'),(b'Full papers stay standalone.',b'Full papers become digests.')]
        for before,after in changes:
            with self.subTest(before=before):
                self.assertIn(before,RAW)
                with self.assertRaises(ValueError):
                    versions.normalize_authority_plan(RAW.replace(before,after))

    def test_unknown_or_changed_approval_holds(self):
        for changed in [RAW+b'\n## Unknown approval\nPass everything.\n', RAW.replace(b'Claude audit PASS',b'Claude audit FAIL'),RAW.replace(versions.APPENDIX_HEADER.encode(),versions.APPENDIX_HEADER.encode()+b' duplicate'),RAW+versions.APPENDIX_HEADER.encode()+b'\n']:
            with self.subTest(digest=hashlib.sha256(changed).hexdigest()),self.assertRaises(ValueError):
                versions.normalize_authority_plan(changed)

    def test_malformed_or_repeated_boundary_holds(self):
        at = RAW.index(versions.APPENDIX_HEADER.encode())
        boundary = RAW.rfind(versions.SUFFIX,0,at)
        for suffix in [b'\n--- \n',b'\n----\n',b'\n--\n',b'\n***\n',b'\n---\n\n---\n',b'\n---\nextra scientific claim\n',b'\n\n---\n']:
            with self.subTest(suffix=suffix),self.assertRaises(ValueError):
                versions.normalize_authority_plan(RAW[:boundary]+suffix+RAW[boundary+5:])

    def test_archive_reader_keeps_every_other_byte_and_restores(self):
        root=HERE.resolve();path=root/'reports/verification-coverage/GAME_PLAN.md'
        own=SimpleNamespace(read_regular=lambda p:RAW if Path(p)==path else b'exact other bytes')
        consumer=SimpleNamespace(d=own);original=own.read_regular
        with versions._exact_authority_framing(consumer,root):
            self.assertEqual(own.read_regular(path),versions.normalize_authority_plan(RAW))
            self.assertEqual(own.read_regular(root/'other'),b'exact other bytes')
        self.assertIs(own.read_regular,original)

    def test_reader_restores_on_original_consumer_hold(self):
        own=SimpleNamespace(read_regular=lambda p:RAW);consumer=SimpleNamespace(d=own);original=own.read_regular
        with self.assertRaisesRegex(ValueError,'original HOLD'):
            with versions._exact_authority_framing(consumer,HERE):
                raise ValueError('original HOLD')
        self.assertIs(own.read_regular,original)

    def test_shared_reader_or_changed_source_holds(self):
        with self.assertRaises(versions.VersionHold):
            with versions._exact_authority_framing(SimpleNamespace(d=versions.d),HERE):
                pass
        calls=[]
        def reader(path):
            calls.append(path)
            return RAW if len(calls)==1 else RAW+b'changed'
        with self.assertRaises(versions.VersionHold):
            with versions._exact_authority_framing(SimpleNamespace(d=SimpleNamespace(read_regular=reader)),HERE):
                pass

    def test_caller_replacing_private_reader_holds_and_restores(self):
        own=SimpleNamespace(read_regular=lambda p:RAW);consumer=SimpleNamespace(d=own);original=own.read_regular
        with self.assertRaises(versions.VersionHold):
            with versions._exact_authority_framing(consumer,HERE):
                own.read_regular=lambda p:b'forged'
        self.assertIs(own.read_regular,original)

class PortableClosedCorpusNamespace(unittest.TestCase):
    def setUp(self):
        self.original=(HERE/'fixtures/registration_baselines/corpus_ledger.py').read_bytes()
        self.new=(HERE/'corpus_ledger.py').read_bytes()

    def test_original_legacy_and_two_pinned_dispatchers_pass(self):
        report=runtime.corpus_preservation(self.original,self.new)
        self.assertEqual(report['status'],'ORIGINAL_SELECTOR_AND_LEGACY_BODIES_IDENTICAL')
        self.assertEqual(report['registry_import_caller']['status'],'EXACT_ORIGINAL_ALIAS_AND_APPROVED_NAMESPACE_WRAPPER')

    def test_closed_additional_name_only(self):
        self.assertIn('registration_imports.py',runtime.POLICY_MODULE_NAMES)
        self.assertNotIn('unreviewed_imports.py',runtime.POLICY_MODULE_NAMES)

    def test_changed_old_legacy_body_holds(self):
        changed=self.new.replace(b'"""Revalidate exact approved releases;',b'"""Unconditionally accept releases;',1)
        self.assertNotEqual(changed,self.new)
        with self.assertRaises(ValueError):runtime.corpus_preservation(self.original,changed)

    def test_changed_source_alias_body_holds(self):
        changed=self.new.replace(b'return methods_digest_registration.preserve(ledger, previous, legacy=_preserve_publication_registrations_legacy)',b'return ledger',1)
        with self.assertRaises(ValueError):runtime.corpus_preservation(self.original,changed)

    def test_changed_new_wrapper_body_holds(self):
        changed=self.new.replace(b'with source_session(Path(ledger[\'tree_root\'])):',b'with source_session(Path(\'/private/tmp\')):',1)
        self.assertNotEqual(changed,self.new)
        with self.assertRaises(ValueError):runtime.corpus_preservation(self.original,changed)

    def test_missing_alias_unknown_extra_and_duplicate_holds(self):
        tree=ast.parse(self.new)
        alias=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_preserve_publication_registrations_source_original')
        lines=self.new.splitlines(keepends=True)
        changed=b''.join(lines[:alias.lineno-1]+lines[alias.end_lineno:])
        for candidate in [changed,self.new+b'\ndef unreviewed_extra():\n return True\n',self.new+b'\ndef preserve_publication_registrations(ledger, previous):\n return ledger\n']:
            with self.subTest(digest=hashlib.sha256(candidate).hexdigest()),self.assertRaises(ValueError):runtime.corpus_preservation(self.original,candidate)

    def test_alias_args_return_and_decorator_holds(self):
        for old,new in [(b'def _preserve_publication_registrations_source_original(ledger, previous):',b'def _preserve_publication_registrations_source_original(ledger, previous=None):'),(b'def _preserve_publication_registrations_source_original(ledger, previous):',b'def _preserve_publication_registrations_source_original(ledger, previous) -> bool:'),(b'def _preserve_publication_registrations_source_original(ledger, previous):',b'@unreviewed\ndef _preserve_publication_registrations_source_original(ledger, previous):')]:
            with self.subTest(new=new),self.assertRaises(ValueError):runtime.corpus_preservation(self.original,self.new.replace(old,new,1))

    def test_wrapper_after_original_cli_guard_holds(self):
        tree=ast.parse(self.new);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='preserve_publication_registrations');lines=self.new.splitlines(keepends=True)
        wrapper=b''.join(lines[fn.lineno-1:fn.end_lineno]);rest=b''.join(lines[:fn.lineno-1]+lines[fn.end_lineno:])
        with self.assertRaises(ValueError):runtime.corpus_preservation(self.original,rest+b'\n'+wrapper+b'\n')

if __name__=='__main__':unittest.main()
