"""Portable behavioral tests of inactive exact-source patches.

Synthetic science/authority bytes exercise validation; only their test-local
hash constants are substituted in fresh namespaces. Production authority pins
are separately asserted. No CORE file is executed, installed or changed.
"""
from contextlib import contextmanager, ExitStack, redirect_stdout, redirect_stderr
import io
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock
import unittest

TOOLS = Path(__file__).resolve().parents[1]
BUNDLE = TOOLS / 'allocation_correction'
RESOLVER = TOOLS / 'effective_allocation.py'


def digest(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(encoded(value)); return path

def namespace():
    value = {'__file__':str(RESOLVER),'__name__':'allocation_fixture'}
    exec(compile(RESOLVER.read_bytes(),str(RESOLVER),'exec'),value)
    return value


def module(path):
    spec=importlib.util.spec_from_file_location('allocation_patch_'+path.stem,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


class Fixture:
    def __init__(self, root):
        self.root=root;self.pipeline=root/'RESEARCH_PIPELINE_v2';self.finalized=self.pipeline/'finalized_runs'
        self.surface=save(self.pipeline/'PUBLIC_IDENTITY_RECONCILIATION_SURFACE_2026-08-30.json',
                          {'authoritative_ledger_max_row_observed':142,'records':[{'proposed_ledger_row':89}]})
        self.ledger=root/'ZENODO_SUBMISSION_LEDGER.md';self.ledger.write_text('| 142 | date | historical | old | source | scope | route | held | — |\n')
        self.ns=namespace();self.science={};r=self.finalized/'Run-183';r.mkdir(parents=True)
        metadata=dict(abbreviation='MCSL',description='Synthetic test claims',version='1',license=None,
                      series_route='methods',spine_gate='NOT_ADMITTED',spine_reason='test branch',
                      notes='test only',keywords=['one','two','three'],ledger_row=None,spine_admitted=False)
        self.title='Synthetic matched contribution note'
        science_values={'CANON_PRODUCT_ROUTE.json':{'product_line':'test methods'},
            'FINALIZED_PACKAGE.json':{'status':'FINALIZED','external_mutation':False,'run_id':'Run-183'},
            'LEAN_ZERO_SORRY_CERTIFICATE.json':{'fixture_only':True},
            'PAPER_PACKAGE_MANIFEST.json':{'title':self.title,'run_id':'Run-183','release_metadata':metadata,'artifacts':{'paper_pdf':'paper.pdf'}},
            'POST_ARISTOTLE_REVIEW.json':{'verdict':'pass','fixture_only':True}}
        for role,(name,_) in self.ns['SCIENCE'].items():
            path=r/name
            if name=='paper.pdf':path.write_bytes(b'synthetic fixture bytes; never used as scientific evidence')
            else:save(path,science_values[name])
            self.science[role]=(name,digest(path.read_bytes()))
        (r/'Fixture.lean').write_text('-- no Lean execution in these tests\n');(r/'summary.md').write_text('Synthetic review fixture\n')
        self.proposals={}
        for run,abbreviation,title in [('Run-177','TAAA','Synthetic arbitration note'),('Run-183','MCSL',self.title)]:
            proposal=dict(standard='VRS-RELEASE-BINDING-PROPOSAL-1',status='READY_FOR_EXACT_AUTHORIZATION',run_id=run,
                          title=title,abbreviation=abbreviation,proposed_ledger_row=147,proposed_license='cc-by-4.0',
                          publication_authorized=False,evidence={key:pair[1]for key,pair in self.science.items()})
            p=save(self.finalized/run/'RELEASE_BINDING_PROPOSAL.json',proposal);self.proposals[run]=digest(p.read_bytes())
        self.linked=save(root/'engine/linked.json',{'fixture_only':'approved narrow row correction'})
        self.authority_path=root/'engine/authority.json'
        self.authority=dict(schema='VRS-JUSTIN-ROW-CORRECTION-AUTHORITY-1',at_utc='2026-10-16T11:33:41+00:00',
            human_source='portable test fixture',source_text='Yes, use row148 for Run-183',proposal_path=str(self.linked),
            proposal_sha256=digest(self.linked.read_bytes()),approved=True,run183_row=148,run177_row=147,
            scientific_evidence_changes_authorized=False,publication_authorized=False,original_packets_preserved=True)
        save(self.authority_path,self.authority)
        self.overlay_path=r/self.ns['OVERLAY_NAME']
        self.overlay=dict(standard='VRS-APPROVED-LINKED-ALLOCATION-CORRECTION-1',run_id='Run-183',old_proposed_row=147,
            approved_local_row=148,run177_row_unchanged=147,
            original_proposal=dict(path=str(r/'RELEASE_BINDING_PROPOSAL.json'),sha256=self.proposals['Run-183'],exists=True),
            authority=dict(path=str(self.authority_path),sha256=digest(self.authority_path.read_bytes())),
            scientific_evidence=[dict(field=key,path=str(r/name),sha256=h,expected_sha256=h,exists=True,matches=True)for key,(name,h)in self.science.items()],
            publication_authorized=False,installed_router_consumes_this_overlay=False,
            global_reservation_collision='HOLD_UNTIL_REVIEWED_SHARED_ALLOCATION_RESOLVER',original_proposal_unchanged=True)
        self.decisions_path=save(root/'engine/local-decisions.json',{'synthetic_fixture_only':True})
        self.local_path=r/self.ns['LOCAL_BINDING_NAME']
        self.local=dict(standard='VRS-LOCAL-RELEASE-BINDING-AUTHORIZATION-1',run_id='Run-183',approved_ledger_row=148,
            license='cc-by-4.0',authority=dict(path=str(self.decisions_path),sha256=digest(self.decisions_path.read_bytes())),
            original_approved_proposal=copy.deepcopy(self.overlay['original_proposal']),promotion_authorized=False,
            publication_authorized=False,publication_status='HOLD_EXACT_PUBLICATION_AUTHORIZATION',
            row_correction_authority=copy.deepcopy(self.overlay['authority']),scientific_evidence=copy.deepcopy(self.overlay['scientific_evidence']),
            source_manifest_unchanged=True)
        save(self.local_path,self.local)
        self.reseal()

    def reseal(self):
        save(self.overlay_path,self.overlay)
        self.binding={'path':str(self.overlay_path),'sha256':digest(self.overlay_path.read_bytes())}
        self.install_pins(self.ns)

    def install_pins(self, target):
        target.update(ORIGINALS=copy.deepcopy(self.proposals),SCIENCE=copy.deepcopy(self.science),
            OVERLAY_SHA256=digest(self.overlay_path.read_bytes()),AUTHORITY_SHA256=digest(self.authority_path.read_bytes()),
            LINKED_PROPOSAL_SHA256=digest(self.linked.read_bytes()),LOCAL_BINDING_SHA256=digest(self.local_path.read_bytes()),
            LOCAL_DECISIONS_SHA256=digest(self.decisions_path.read_bytes()))

    def resolve(self, *, correction=True, expected=None):
        return self.ns['resolve'](self.finalized,self.surface,correction=self.binding if correction else None,
            ledger_path=self.ledger,expected_ledger_sha256=(expected or digest(self.ledger.read_bytes()))if correction else None)

    def row148(self, *, identity='MCSL', run='Run-183', status='🔒 HELD; DO NOT PUBLISH'):
        self.ledger.write_text('| 142 | date | historical | old | source | scope | route | held | — |\n'+
            f'| 148 | date | **{identity} — {self.title}** | nightly {run} | science | local only | methods | {status} | — |\n')

    def install_review_tree(self):
        manifest=json.loads((BUNDLE/'PATCH_MANIFEST.json').read_bytes())
        for name,row in manifest['sources'].items():
            target=self.pipeline/name;raw=(BUNDLE/'before'/(name+'.txt')).read_bytes()
            assert digest(raw)==row['before_sha256'];target.write_bytes(raw)
        (self.pipeline/'effective_allocation.py').write_bytes(RESOLVER.read_bytes())
        subprocess.run(['git','init','-q',str(self.root)],check=True,capture_output=True)
        for name,row in manifest['sources'].items():
            patch=BUNDLE/'patches'/(name+'.patch')
            subprocess.run(['git','apply','--check',str(patch)],cwd=self.root,check=True,capture_output=True)
            subprocess.run(['git','apply',str(patch)],cwd=self.root,check=True,capture_output=True)
            assert digest((self.pipeline/name).read_bytes())==row['after_sha256']
        return {name:module(self.pipeline/name)for name in manifest['sources']}

    @contextmanager
    def test_pins_in_real_loader(self, consumer):
        real=consumer.load_effective_allocation
        def load():
            ns=real();self.install_pins(ns);return ns
        with mock.patch.object(consumer,'load_effective_allocation',side_effect=load):yield

    def options(self):
        return dict(allocation_correction=self.binding,expected_ledger_sha256=digest(self.ledger.read_bytes()))


def stage_inputs(f, run='Run-183', abbreviation='MCSL', row=148):
    r=f.finalized/run
    if run!='Run-183':
        r.mkdir(parents=True,exist_ok=True)
        save(r/'PAPER_PACKAGE_MANIFEST.json',dict(title='Title '+run,run_id=run,
            release_metadata=dict(abbreviation=abbreviation,description='d',version='1',license=None,
            series_route='methods',spine_gate='NOT_ADMITTED',spine_reason='r',notes='n',keywords=['a','b','c'],ledger_row=None,spine_admitted=False),
            artifacts={'paper_pdf':'paper.pdf'}))
        save(r/'FINALIZED_PACKAGE.json',dict(status='FINALIZED',external_mutation=False,run_id=run))
        save(r/'POST_ARISTOTLE_REVIEW.json',{'verdict':'pass'});(r/'paper.pdf').write_bytes(b'fixture '+run.encode())
        (r/'X.lean').write_text('-- test');(r/'summary.md').write_text('summary')
        save(r/'RELEASE_BINDING_PROPOSAL.json',dict(standard='VRS-RELEASE-BINDING-PROPOSAL-1',status='READY_FOR_EXACT_AUTHORIZATION',
            run_id=run,title='Title '+run,abbreviation=abbreviation,proposed_ledger_row=row,proposed_license='cc-by-4.0'))
    save(f.pipeline/'nightly_packages'/run/'QUALITY_GATE.json',dict(quality_verdict='PASS',saturday_status='CANDIDATE_FOR_LEDGER_G0_G9'))
    save(f.pipeline/'viridisos_kernel_packages'/run/'VIRIDISOS_KERNEL_PACKAGE.json',dict(standard='VRS-VIRIDISOS-KERNEL-PACKAGE-1',
        run_id=run,status='NO_RUNTIME_KERNEL',external_mutation=False,admission_review=dict(g7_verdict='PASS',complete_pdf_review=True,
        runtime_verdict='NO_RUNTIME_KERNEL',lean_zero_sorry_certificate_sha256='0'*64)))


def route_inputs(f):
    r=f.finalized/'Run-191';r.mkdir()
    save(r/'PAPER_PACKAGE_MANIFEST.json',dict(run_id='Run-191',title='New route',release_metadata=dict(spine_admitted=False,
         abbreviation='NEW',series_route='methods'),viridisos_kernel_candidate=dict(status='NO_RUNTIME_KERNEL',reason='none')))
    save(r/'POST_ARISTOTLE_REVIEW.json',dict(verdict='pass',spine_admission=dict(admitted=False)))
    save(r/'FINALIZED_PACKAGE.json',dict(run_id='Run-191'));(r/'paper.pdf').write_bytes(b'x')
    save(r/'LEAN_ZERO_SORRY_CERTIFICATE.json',{'fixture':True})
    return ['--run','191']


def reconcile_inputs(f):
    receipt=save(f.root/'releases/2026-10-17.json',dict(status='verified',repository='jdhart81/viridis-canon',branch='main',
        spine_changed=False,commit_sha='a'*40,verified_at_utc='2026-10-17T12:00:00+00:00',
        bundles=[dict(abbreviation='MCSL',run_id='Run-183',doi='10.5281/zenodo.99999999')]))
    save(f.root/'ViridisOS/runtime/research_intake.json',{'records':[],'lockstep_receipts':[]})
    f.row148(status='✅ OK')
    return ['--receipt',str(receipt),'--apply']


@contextmanager
def assembler_helpers(a):
    with mock.patch.object(a,'load_lockstep',return_value=SimpleNamespace(load_post_aristotle_review=lambda *x:None)),mock.patch.object(a,'load_coherence',return_value=SimpleNamespace(unassigned_rights_notice=lambda title:'Unassigned')):
        yield


def cli(a, argv):
    out=io.StringIO();err=io.StringIO()
    with mock.patch.object(sys,'argv',['consumer',*argv]),redirect_stdout(out),redirect_stderr(err):
        try:rc=a.main()
        except Exception as exc:return -1,{'uncaught':type(exc).__name__+': '+str(exc)}
    raw=out.getvalue() or err.getvalue()
    return rc,json.loads(raw)


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f=Fixture(Path(self.temp.name).resolve());self.hold=self.f.ns['AllocationHold']

    def test_production_pins_are_exact_and_not_environment_selected(self):
        ns=namespace()
        self.assertEqual(ns['OVERLAY_SHA256'],'9a25d095f1fecbf591e1f26e91af9fc5856f9b62e76296a09ddd2773d19da921')
        self.assertEqual(ns['AUTHORITY_SHA256'],'d0429a8b2885d6716db80d8981f9758ee3cfd53cb35d80d7fc9d89045ca88ee0')
        self.assertEqual(ns['LOCAL_BINDING_SHA256'],'53eefdfcb2b242f02a83564b895721e8bbc180ee4c1df11fb02c56afd7d4982f')
        self.assertEqual(ns['LOCAL_DECISIONS_SHA256'],'5c0ff7e4bf6d563266455fa8ab0df158a42baa8056dd5678198585b5a04a5af2')
        self.assertEqual(ns['ORIGINALS']['Run-183'],'3c6c883796aab54c14062f9e905c375fd705faa547779a18c2930692a6ddbe1d')
        self.assertEqual(ns['ORIGINALS']['Run-177'],'290860184267124c6bc7f716e3a8ef591836c832c89a02047886ad4eef4856ae')

    def test_default_no_overlay_keeps_original_global_collision_hold(self):
        with self.assertRaisesRegex(self.hold,'APPROVED_183_OVERLAY_REQUIRED'):self.f.resolve(correction=False)
        save(self.f.finalized/'Run-191/RELEASE_BINDING_PROPOSAL.json',{'run_id':'Run-191','status':'READY_FOR_EXACT_AUTHORIZATION','proposed_ledger_row':148})
        with self.assertRaisesRegex(self.hold,'GLOBAL_RESERVATION_COLLISION'):self.f.resolve()

    def test_exact_overlay_projects_only183_and_preserves_both_original_bytes(self):
        old={run:(self.f.finalized/run/'RELEASE_BINDING_PROPOSAL.json').read_bytes()for run in self.f.proposals}
        view=self.f.resolve()
        self.assertEqual(view.proposal('Run-177')['proposed_ledger_row'],147)
        self.assertEqual(view.proposal('Run-183')['proposed_ledger_row'],148)
        self.assertEqual(view.original_proposal('Run-183')['proposed_ledger_row'],147)
        self.assertEqual(view.proposal_rows,(147,148))
        for run,raw in old.items():self.assertEqual((self.f.finalized/run/'RELEASE_BINDING_PROPOSAL.json').read_bytes(),raw)
        receipt=view.receipt();self.assertFalse(receipt['publication_authorized']);self.assertFalse(receipt['license_authorized']);self.assertFalse(receipt['certifies'])
        changed=view.proposal('Run-183');changed['proposed_ledger_row']=999
        self.assertEqual(view.proposal('Run-183')['proposed_ledger_row'],148)

    def test_bound_row148_has_same_receipt_binding_schema_and_identity(self):
        unoccupied=self.f.resolve().receipt()['correction']['original_proposal']
        self.f.row148();occupied=self.f.resolve().receipt()['correction']['original_proposal']
        self.assertEqual(occupied,unoccupied);self.assertEqual(set(occupied),{'path','sha256','exists'})
        for identity,run in [('OTHER','Run-183'),('MCSL','Run-184'),('MCSL extra','Run-183')]:
            self.f.row148(identity=identity,run=run)
            with self.assertRaisesRegex(self.hold,'ROW148_SAME_SCIENTIFIC_IDENTITY'):self.f.resolve()

    def test_overlay_requires_explicit_exact_pin_and_current_ledger_cas(self):
        for binding in [None,{'path':str(self.f.overlay_path),'sha256':'0'*64},
                        {**self.f.binding,'unknown':True}]:
            with self.subTest(binding=binding),self.assertRaises(self.hold):
                self.f.ns['resolve'](self.f.finalized,self.f.surface,correction=binding,
                    ledger_path=self.f.ledger,expected_ledger_sha256=digest(self.f.ledger.read_bytes()))
        with self.assertRaisesRegex(self.hold,'CURRENT_LEDGER_CAS_REQUIRED'):
            self.f.ns['resolve'](self.f.finalized,self.f.surface,correction=self.f.binding)
        with self.assertRaisesRegex(self.hold,'EXACT_INPUT_HASH'):self.f.resolve(expected='0'*64)

    def test_ledger_and_public_reservation_inputs_have_fixed_root_roles(self):
        other=save(self.f.root/'lookalike.json',{'records':[],'authoritative_ledger_max_row_observed':0})
        with self.assertRaisesRegex(self.hold,'RECONCILIATION_SURFACE_ROLE'):
            self.f.ns['resolve'](self.f.finalized,other,correction=self.f.binding,ledger_path=self.f.ledger,expected_ledger_sha256=digest(self.f.ledger.read_bytes()))
        other.write_bytes(self.f.ledger.read_bytes())
        with self.assertRaisesRegex(self.hold,'CURRENT_ROOT_LEDGER_ROLE'):
            self.f.ns['resolve'](self.f.finalized,self.f.surface,correction=self.f.binding,ledger_path=other,expected_ledger_sha256=digest(other.read_bytes()))

    def test_only183147to148_local_only_and_closed_overlay_fields(self):
        for key,value in [('run_id','Run-177'),('old_proposed_row',146),('approved_local_row',149),
            ('approved_local_row',True),('run177_row_unchanged',148),('publication_authorized',True),
            ('installed_router_consumes_this_overlay',True),('original_proposal_unchanged',False),
            ('global_reservation_collision','PASS'),('unknown',True)]:
            with self.subTest(key=key,value=value):
                original=copy.deepcopy(self.f.overlay);self.f.overlay[key]=value;self.f.reseal()
                with self.assertRaises(self.hold):self.f.resolve()
                self.f.overlay=original;self.f.reseal()

    def test_authority_scope_and_exact_linked_hash_are_enforced_after_hash_admission(self):
        for key,value in [('approved',False),('run183_row',149),('run177_row',148),
            ('publication_authorized',True),('scientific_evidence_changes_authorized',True),
            ('original_packets_preserved',False),('source_text','Approve anything'),('unknown',True)]:
            with self.subTest(key=key):
                original=copy.deepcopy(self.f.authority);self.f.authority[key]=value;save(self.f.authority_path,self.f.authority)
                self.f.overlay['authority']['sha256']=digest(self.f.authority_path.read_bytes())
                self.f.local['row_correction_authority']=copy.deepcopy(self.f.overlay['authority']);save(self.f.local_path,self.f.local);self.f.reseal()
                with self.assertRaises(self.hold):self.f.resolve()
                self.f.authority=original;save(self.f.authority_path,original)
                self.f.overlay['authority']['sha256']=digest(self.f.authority_path.read_bytes())
                self.f.local['row_correction_authority']=copy.deepcopy(self.f.overlay['authority']);save(self.f.local_path,self.f.local);self.f.reseal()
        self.f.linked.write_bytes(b'tamper')
        with self.assertRaisesRegex(self.hold,'EXACT_INPUT_HASH'):self.f.resolve()

    def test_every_original_science_authority_and_overlay_tamper_holds(self):
        paths=[self.f.overlay_path,self.f.authority_path,self.f.linked,self.f.local_path,self.f.decisions_path,
               *(self.f.finalized/run/'RELEASE_BINDING_PROPOSAL.json'for run in self.f.proposals),
               *(self.f.finalized/'Run-183'/name for name,h in self.f.science.values())]
        for path in paths:
            with self.subTest(name=path.name):
                raw=path.read_bytes();path.write_bytes(raw+b' ')
                with self.assertRaisesRegex(self.hold,'EXACT_INPUT_HASH'):self.f.resolve()
                path.write_bytes(raw)

    def test_companion_local_binding_is_closed_local_only_and_matches_same_authorities(self):
        for key,value in [('approved_ledger_row',149),('publication_authorized',True),('promotion_authorized',True),
            ('license','other'),('source_manifest_unchanged',False),('row_correction_authority',{}),('unknown',True)]:
            with self.subTest(key=key):
                original=copy.deepcopy(self.f.local);self.f.local[key]=value;save(self.f.local_path,self.f.local);self.f.reseal()
                with self.assertRaises(self.hold):self.f.resolve()
                self.f.local=original;save(self.f.local_path,original);self.f.reseal()

    def test_duplicate_science_roles_and_unknown_science_fields_hold(self):
        for change in [lambda rows:rows.__setitem__(1,copy.deepcopy(rows[0])),lambda rows:rows[0].update(unknown=True)]:
            original=copy.deepcopy(self.f.overlay);change(self.f.overlay['scientific_evidence']);self.f.reseal()
            with self.assertRaises(self.hold):self.f.resolve()
            self.f.overlay=original;self.f.reseal()

    def test_boolean_rows_and_duplicate_global_public_or_effective_reservations_hold(self):
        save(self.f.surface,{'authoritative_ledger_max_row_observed':142,'records':[{'proposed_ledger_row':True}]})
        with self.assertRaisesRegex(self.hold,'POSITIVE_INTEGER_ROW'):self.f.resolve()
        for rows in [[148],[89,89],[147]]:
            save(self.f.surface,{'authoritative_ledger_max_row_observed':142,'records':[{'proposed_ledger_row':x}for x in rows]})
            with self.assertRaisesRegex(self.hold,'GLOBAL_RESERVATION_COLLISION'):self.f.resolve()
        save(self.f.surface,{'authoritative_ledger_max_row_observed':142,'records':[]})
        p=self.f.finalized/'Run-191/RELEASE_BINDING_PROPOSAL.json'
        save(p,{'run_id':'Run-191','status':'READY_FOR_EXACT_AUTHORIZATION','proposed_ledger_row':True})
        with self.assertRaisesRegex(self.hold,'POSITIVE_INTEGER_ROW'):self.f.resolve()
        save(p,{'run_id':'Run-191','status':'READY_FOR_EXACT_AUTHORIZATION','proposed_ledger_row':148})
        with self.assertRaisesRegex(self.hold,'GLOBAL_RESERVATION_COLLISION'):self.f.resolve()

    def test_duplicate_target_ledger_rows_and_malformed_json_hold(self):
        self.f.row148();self.f.ledger.write_bytes(self.f.ledger.read_bytes()*2)
        with self.assertRaisesRegex(self.hold,'UNIQUE_CURRENT_ROW148'):self.f.resolve()
        for raw in (b'{"same":1,"same":2}',b'{"bad":NaN}',b'[]'):
            with self.subTest(raw=raw),self.assertRaises(self.hold):self.f.ns['document'](raw)

    def test_regular_inputs_reject_leaf_and_ancestor_links(self):
        for path in [self.f.overlay_path,self.f.authority_path,self.f.finalized/'Run-183/paper.pdf']:
            with self.subTest(path=path.name):
                raw=path.read_bytes();target=self.f.root/'saved';target.write_bytes(raw);path.unlink();path.symlink_to(target)
                with self.assertRaisesRegex(self.hold,'REGULAR_PATH'):self.f.resolve()
                path.unlink();path.write_bytes(raw);target.unlink()
        run=self.f.finalized/'Run-183';target=self.f.finalized/'saved183';run.rename(target);run.symlink_to(target,target_is_directory=True)
        with self.assertRaisesRegex(self.hold,'REGULAR_PATH'):self.f.resolve()

    def test_bytes_frames_and_proposal_inventory_are_rechecked_before_use(self):
        targets=[self.f.surface,self.f.ledger,self.f.overlay_path,self.f.authority_path,self.f.finalized/'Run-183/paper.pdf']
        for path in targets:
            with self.subTest(name=path.name):
                view=self.f.resolve();raw=path.read_bytes()
                try:
                    path.write_bytes(raw+b' ')
                    with self.assertRaisesRegex(self.hold,'INPUT_RACE'):view.revalidate()
                finally:
                    path.write_bytes(raw)
        view=self.f.resolve();save(self.f.finalized/'Run-191/RELEASE_BINDING_PROPOSAL.json',{'run_id':'Run-191'})
        with self.assertRaisesRegex(self.hold,'RESERVATION_SET_RACE'):view.revalidate()

    def test_owned_ledger_afterimage_checks_every_other_input_and_keeps_original_cas(self):
        view=self.f.resolve();before_hash=digest(self.f.ledger.read_bytes());after=b'owned reconciler afterimage\n';self.f.ledger.write_bytes(after)
        self.assertEqual(view.revalidate_after_ledger_write(after)['input_sha256'][str(self.f.ledger)],before_hash)
        with self.assertRaisesRegex(self.hold,'INPUT_RACE'):view.revalidate_after_ledger_write(b'wrong')
        self.f.authority_path.write_bytes(self.f.authority_path.read_bytes()+b' ')
        with self.assertRaisesRegex(self.hold,'INPUT_RACE'):view.revalidate_after_ledger_write(after)

    def test_regular_double_read_detects_mid_read_and_same_byte_aba_changes(self):
        path=self.f.finalized/'Run-183/paper.pdf';original_read=self.f.ns['os'].read;changed=[]
        def read(fd,size):
            value=original_read(fd,size)
            if value and not changed:
                path.write_bytes(path.read_bytes()+b' changed');changed.append(True)
            return value
        with mock.patch.object(self.f.ns['os'],'read',side_effect=read),self.assertRaisesRegex(self.hold,'READ_RACE'):
            self.f.ns['regular'](path)
        # Restore exact bytes before acquiring a view, then rewrite the same
        # bytes: inode time frames still prevent an ABA from passing admission.
        path.write_bytes(b'synthetic fixture bytes; never used as scientific evidence')
        view=self.f.resolve();raw=path.read_bytes();path.write_bytes(raw)
        with self.assertRaisesRegex(self.hold,'INPUT_RACE'):view.revalidate()


class PatchedConsumerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f=Fixture(Path(self.temp.name).resolve());self.modules=self.f.install_review_tree()

    def test_patches_reproduce_exact_before_and_after_source_hashes(self):
        subprocess.run([sys.executable,'-B',str(BUNDLE/'build_patches.py'),'--check'],check=True,capture_output=True)
        manifest=json.loads((BUNDLE/'PATCH_MANIFEST.json').read_bytes())
        self.assertFalse(manifest['active']);self.assertEqual(manifest['resolver_source_sha256'],digest(RESOLVER.read_bytes()))
        for name,row in manifest['sources'].items():self.assertEqual(digest((self.f.pipeline/name).read_bytes()),row['after_sha256'])

    def test_all_three_consumers_share_effective_rows_with_explicit_binding(self):
        router=self.modules['canon_product_router.py'];assembler=self.modules['assemble_saturday_candidate.py'];reconciler=self.modules['reconcile_publication_receipt.py']
        for consumer in (router,assembler,reconciler):
            with self.f.test_pins_in_real_loader(consumer):
                view=consumer.effective_allocation_view(self.f.finalized,self.f.surface,ledger_path=self.f.ledger,**self.f.options())
                self.assertEqual(view.proposal('Run-183')['proposed_ledger_row'],148);self.assertEqual(view.proposal('Run-177')['proposed_ledger_row'],147)
        with self.f.test_pins_in_real_loader(router):
            maximum,public,proposed,surfaces=router.reserved_ledger_state(self.f.finalized,self.f.surface,ledger_path=self.f.ledger,**self.f.options())
            self.assertEqual(proposed,[147,148]);self.assertIn(self.f.overlay_path.relative_to(self.f.root).as_posix(),surfaces)
        with self.f.test_pins_in_real_loader(reconciler):
            values=reconciler.proposal_map(self.f.finalized,ledger_path=self.f.ledger,**self.f.options())
            self.assertEqual(values['MCSL']['proposed_ledger_row'],148);self.assertEqual(values['TAAA']['proposed_ledger_row'],147)

    def test_no_overlay_and_partial_cli_options_hold_in_every_consumer(self):
        for consumer in self.modules.values():
            with self.subTest(consumer=consumer.__name__),self.f.test_pins_in_real_loader(consumer):
                view=consumer.effective_allocation_view(self.f.finalized,self.f.surface)
                self.assertEqual(view.proposal('Run-183')['proposed_ledger_row'],148)
                with self.assertRaises(Exception):consumer.explicit_allocation_options(str(self.f.overlay_path),None,None)

    def test_hash_bound_loader_rejects_tampered_source_symlinks_and_ambient_module(self):
        consumer=self.modules['canon_product_router.py'];path=self.f.pipeline/'effective_allocation.py';raw=path.read_bytes()
        path.write_bytes(raw+b'\n# drift')
        with self.assertRaisesRegex(consumer.RouteError,'MODULE_PIN'):consumer.load_effective_allocation()
        path.write_bytes(raw);target=self.f.root/'resolver-copy.py';target.write_bytes(raw);path.unlink();path.symlink_to(target)
        with self.assertRaisesRegex(consumer.RouteError,'MODULE_PATH'):consumer.load_effective_allocation()
        path.unlink();path.write_bytes(raw)
        with mock.patch.dict(sys.modules,{'effective_allocation':SimpleNamespace(resolve=lambda *a,**k: self.fail('ambient resolver used'),OVERLAY_SHA256='AMBIENT_IMPORT_WAS_USED')}):
            actual=consumer.load_effective_allocation()
        self.assertEqual(actual['OVERLAY_SHA256'],'9a25d095f1fecbf591e1f26e91af9fc5856f9b62e76296a09ddd2773d19da921')

    def test_staged_projection_retains_original147_and_proposes148_without_assigning_rights(self):
        a=self.modules['assemble_saturday_candidate.py'];f=self.f
        save(f.pipeline/'nightly_packages/Run-183/QUALITY_GATE.json',{'quality_verdict':'PASS','saturday_status':'CANDIDATE_FOR_LEDGER_G0_G9'})
        save(f.pipeline/'viridisos_kernel_packages/Run-183/VIRIDISOS_KERNEL_PACKAGE.json',dict(standard='VRS-VIRIDISOS-KERNEL-PACKAGE-1',run_id='Run-183',status='NO_RUNTIME_KERNEL',external_mutation=False,
             admission_review=dict(g7_verdict='PASS',complete_pdf_review=True,runtime_verdict='NO_RUNTIME_KERNEL',lean_zero_sorry_certificate_sha256=f.science['lean_zero_sorry_certificate_sha256'][1])))
        with f.test_pins_in_real_loader(a),mock.patch.object(a,'load_lockstep',return_value=SimpleNamespace(load_post_aristotle_review=lambda *args:None)),mock.patch.object(a,'load_coherence',return_value=SimpleNamespace(unassigned_rights_notice=lambda title:'Unassigned test rights')):
            result=a.stage_candidate('183','2026-10-17',finalized_root=f.finalized,package_root=f.pipeline/'nightly_packages',staging_root=f.pipeline/'staging',ledger_path=f.ledger,**f.options())
        manifest=json.loads((Path(result['bundle'])/'BUNDLE_MANIFEST.json').read_bytes());projection=manifest['release_binding_proposal']
        self.assertEqual(projection['original_proposed_ledger_row'],147);self.assertEqual(projection['proposed_ledger_row'],148)
        self.assertEqual(projection['sha256'],f.proposals['Run-183']);self.assertEqual(projection['effective_allocation_receipt']['correction']['overlay'],f.binding)
        self.assertIsNone(manifest['ledger_row']);self.assertEqual(result['ledger']['state'],'HOLD_LEDGER')
        self.assertEqual(json.loads((Path(result['bundle'])/'zenodo_metadata.json').read_bytes())['metadata']['license'],'unassigned')
        f.row148()
        with self.assertRaisesRegex(a.AssemblyError,'not Justin-cleared'):
            a.bind_ledger('183','2026-10-17',148,justin_authorized=True,staging_root=f.pipeline/'staging',ledger_path=f.ledger)
        f.row148(status='✅ OK')
        bound=a.bind_ledger('183','2026-10-17',148,justin_authorized=True,staging_root=f.pipeline/'staging',ledger_path=f.ledger)
        self.assertEqual(bound['status'],'LEDGER_BOUND')
        self.assertEqual(json.loads((f.finalized/'Run-183/RELEASE_BINDING_PROPOSAL.json').read_bytes())['proposed_ledger_row'],147)

    def test_router_allocates_next149_and_stale_reservations_prevent_route_write(self):
        a=self.modules['canon_product_router.py'];f=self.f;r=f.finalized/'Run-191';r.mkdir()
        save(r/'PAPER_PACKAGE_MANIFEST.json',dict(run_id='Run-191',title='Synthetic new route',release_metadata=dict(spine_admitted=False,abbreviation='NEW',series_route='methods'),viridisos_kernel_candidate=dict(status='NO_RUNTIME_KERNEL',reason='Test declares no runtime')))
        save(r/'POST_ARISTOTLE_REVIEW.json',dict(verdict='pass',spine_admission=dict(admitted=False)))
        save(r/'FINALIZED_PACKAGE.json',dict(run_id='Run-191'));(r/'paper.pdf').write_bytes(b'fixture');save(r/'LEAN_ZERO_SORRY_CERTIFICATE.json',{'fixture':True})
        with f.test_pins_in_real_loader(a):
            result=a.seal_route_and_proposal('191',finalized_root=f.finalized,reconciliation_surface=f.surface,ledger_path=f.ledger,**f.options())
        self.assertEqual(result['proposed_ledger_row'],149)
        p=json.loads((r/'RELEASE_BINDING_PROPOSAL.json').read_bytes());self.assertEqual(p['ledger_basis']['effective_allocation_projection']['original_rows']['Run-183'],147)
        self.assertEqual(p['ledger_basis']['effective_allocation_projection']['effective_rows']['Run-183'],148)
        view=f.resolve();self.assertEqual(max(view.authoritative_max,*view.public_rows,*view.proposal_rows)+1,150)

    def test_verified_receipt_selects148_and_keeps_legacy_ledger_authorization(self):
        a=self.modules['reconcile_publication_receipt.py'];f=self.f
        receipt=save(f.root/'releases/2026-10-17.json',dict(status='verified',repository='jdhart81/viridis-canon',branch='main',spine_changed=False,commit_sha='a'*40,verified_at_utc='2026-10-17T12:00:00+00:00',bundles=[dict(abbreviation='MCSL',run_id='Run-183',doi='10.5281/zenodo.99999999')]))
        intake=save(f.root/'ViridisOS/runtime/research_intake.json',{'records':[],'lockstep_receipts':[]})
        f.row148()
        with f.test_pins_in_real_loader(a),self.assertRaisesRegex(a.ReconciliationError,'not authorized'):
            a.reconcile(receipt,apply=False,root=f.root,**f.options())
        f.row148(status='✅ OK')
        with f.test_pins_in_real_loader(a):result=a.reconcile(receipt,apply=True,root=f.root,**f.options())
        self.assertEqual(result['ledger_rows_changed'],[148]);self.assertEqual(result['effective_allocation_projection']['original_rows']['Run-183'],147)
        self.assertIn('PUBLISHED',f.ledger.read_text());self.assertEqual(json.loads(intake.read_bytes())['records'][0]['run_id'],'Run-183')
        self.assertEqual(json.loads((f.finalized/'Run-183/RELEASE_BINDING_PROPOSAL.json').read_bytes())['proposed_ledger_row'],147)

    def test_reconciler_uses_captured_ledger_bytes_instead_of_an_unbound_second_read(self):
        a=self.modules['reconcile_publication_receipt.py'];f=self.f
        receipt=save(f.root/'releases/2026-10-17.json',dict(status='verified',repository='jdhart81/viridis-canon',branch='main',spine_changed=False,commit_sha='a'*40,verified_at_utc='2026-10-17T12:00:00+00:00',bundles=[dict(abbreviation='MCSL',run_id='Run-183',doi='10.5281/zenodo.99999999')]))
        save(f.root/'ViridisOS/runtime/research_intake.json',{'records':[],'lockstep_receipts':[]});f.row148(status='✅ OK')
        real_read=Path.read_text
        def unbound(path,*args,**kwargs):
            text=real_read(path,*args,**kwargs)
            return text.replace('✅ OK','HELD transient bytes')if path==f.ledger else text
        with f.test_pins_in_real_loader(a),mock.patch.object(Path,'read_text',unbound):
            try:result=a.reconcile(receipt,apply=False,root=f.root,**f.options())
            except a.ReconciliationError:result={'status':'HOLD'}
        self.assertEqual(result['status'],'DRY_RUN');self.assertEqual(result['ledger_rows_changed'],[148])

    def test_router_revalidates_the_snapshot_before_writing_any_new_route(self):
        a=self.modules['canon_product_router.py'];f=self.f;r=f.finalized/'Run-191';r.mkdir()
        save(r/'PAPER_PACKAGE_MANIFEST.json',dict(run_id='Run-191',title='Synthetic route',release_metadata=dict(spine_admitted=False,abbreviation='NEW'),viridisos_kernel_candidate=dict(status='NO_RUNTIME_KERNEL',reason='Fixture only')))
        save(r/'POST_ARISTOTLE_REVIEW.json',dict(verdict='pass',spine_admission=dict(admitted=False)))
        save(r/'FINALIZED_PACKAGE.json',dict(run_id='Run-191'));(r/'paper.pdf').write_bytes(b'fixture');save(r/'LEAN_ZERO_SORRY_CERTIFICATE.json',{'fixture':True})
        real_factory=a.effective_allocation_view
        def factory(*args,**kwargs):
            view=real_factory(*args,**kwargs);receipt=view.receipt
            def changed():
                value=receipt();f.ledger.write_bytes(f.ledger.read_bytes()+b' ');return value
            view.receipt=changed;return view
        with f.test_pins_in_real_loader(a),mock.patch.object(a,'effective_allocation_view',side_effect=factory):
            with self.assertRaisesRegex(a.RouteError if hasattr(a,'RouteError')else a.AssemblyError if hasattr(a,'AssemblyError')else a.ReconciliationError,'INPUT_RACE'):
                a.seal_route_and_proposal('191',finalized_root=f.finalized,reconciliation_surface=f.surface,ledger_path=f.ledger,**f.options())
        self.assertFalse((r/'CANON_PRODUCT_ROUTE.json').exists());self.assertFalse((r/'RELEASE_BINDING_PROPOSAL.json').exists())

    def test_assembler_revalidates_after_review_before_creating_candidate_files(self):
        a=self.modules['assemble_saturday_candidate.py'];f=self.f
        save(f.pipeline/'nightly_packages/Run-183/QUALITY_GATE.json',{'quality_verdict':'PASS','saturday_status':'CANDIDATE_FOR_LEDGER_G0_G9'})
        save(f.pipeline/'viridisos_kernel_packages/Run-183/VIRIDISOS_KERNEL_PACKAGE.json',dict(standard='VRS-VIRIDISOS-KERNEL-PACKAGE-1',run_id='Run-183',status='NO_RUNTIME_KERNEL',external_mutation=False,
             admission_review=dict(g7_verdict='PASS',complete_pdf_review=True,runtime_verdict='NO_RUNTIME_KERNEL',lean_zero_sorry_certificate_sha256=f.science['lean_zero_sorry_certificate_sha256'][1])))
        def load():
            f.authority_path.write_bytes(f.authority_path.read_bytes()+b' ')
            return SimpleNamespace(load_post_aristotle_review=lambda *args:None)
        with f.test_pins_in_real_loader(a),mock.patch.object(a,'load_lockstep',side_effect=load),mock.patch.object(a,'load_coherence',return_value=SimpleNamespace(unassigned_rights_notice=lambda title:'Unassigned')):
            with self.assertRaisesRegex(a.RouteError if hasattr(a,'RouteError')else a.AssemblyError if hasattr(a,'AssemblyError')else a.ReconciliationError,'INPUT_RACE'):
                a.stage_candidate('183','2026-10-17',finalized_root=f.finalized,package_root=f.pipeline/'nightly_packages',staging_root=f.pipeline/'staging',ledger_path=f.ledger,**f.options())
        self.assertFalse((f.pipeline/'staging').exists())

    def test_reconciler_revalidates_before_first_write_and_after_its_owned_ledger_write(self):
        a=self.modules['reconcile_publication_receipt.py'];f=self.f
        receipt=save(f.root/'releases/2026-10-17.json',dict(status='verified',repository='jdhart81/viridis-canon',branch='main',spine_changed=False,commit_sha='a'*40,verified_at_utc='2026-10-17T12:00:00+00:00',bundles=[dict(abbreviation='MCSL',run_id='Run-183',doi='10.5281/zenodo.99999999')]))
        intake=save(f.root/'ViridisOS/runtime/research_intake.json',{'records':[],'lockstep_receipts':[]});f.row148(status='✅ OK')
        before_ledger=f.ledger.read_bytes();before_intake=intake.read_bytes();before_authority=f.authority_path.read_bytes()
        def route(*args):
            f.authority_path.write_bytes(before_authority+b' ');return {'product_line':'test'}
        with f.test_pins_in_real_loader(a),mock.patch.object(a,'route_for',side_effect=route):
            with self.assertRaisesRegex(a.RouteError if hasattr(a,'RouteError')else a.AssemblyError if hasattr(a,'AssemblyError')else a.ReconciliationError,'INPUT_RACE'):a.reconcile(receipt,apply=True,root=f.root,**f.options())
        self.assertEqual(f.ledger.read_bytes(),before_ledger);self.assertEqual(intake.read_bytes(),before_intake)
        f.authority_path.write_bytes(before_authority);real_write=a.write_text_atomic
        def write(path,value):
            real_write(path,value)
            if path==f.ledger:f.authority_path.write_bytes(before_authority+b' ')
        with f.test_pins_in_real_loader(a),mock.patch.object(a,'write_text_atomic',side_effect=write):
            with self.assertRaisesRegex(a.RouteError if hasattr(a,'RouteError')else a.AssemblyError if hasattr(a,'AssemblyError')else a.ReconciliationError,'INPUT_RACE'):a.reconcile(receipt,apply=True,root=f.root,**f.options())
        self.assertIn('PUBLISHED',f.ledger.read_text());self.assertEqual(intake.read_bytes(),before_intake)


    def test_real_argparse_cli_all_three_with_path_flags_and_automatic_defaults(self):
        for mode in ('flags','automatic'):
            for name in ('canon_product_router.py','assemble_saturday_candidate.py','reconcile_publication_receipt.py'):
                with self.subTest(mode=mode,consumer=name),tempfile.TemporaryDirectory() as temp:
                    f=Fixture(Path(temp).resolve());a=f.install_review_tree()[name]
                    if name.startswith('canon'):argv=route_inputs(f)
                    elif name.startswith('assemble'):
                        stage_inputs(f);argv=['--run','183','--date','2026-10-17']
                    else:argv=reconcile_inputs(f)
                    if mode=='flags':argv+=['--allocation-correction',str(f.overlay_path),'--allocation-correction-sha256',f.binding['sha256'],'--expected-ledger-sha256',digest(f.ledger.read_bytes())]
                    with ExitStack() as stack:
                        stack.enter_context(f.test_pins_in_real_loader(a))
                        if name.startswith('assemble'):stack.enter_context(assembler_helpers(a))
                        rc,result=cli(a,argv)
                        self.assertEqual(rc,0,result)
                        self.assertIn(result['status'],('READY_FOR_EXACT_AUTHORIZATION','STAGED_CANDIDATE','APPLIED'))
                        if name.startswith('canon'):
                            self.assertEqual(result['proposed_ledger_row'],149)
                            self.assertTrue((f.finalized/'Run-191/CANON_PRODUCT_ROUTE.json').is_file())
                            self.assertTrue((f.finalized/'Run-191/RELEASE_BINDING_PROPOSAL.json').is_file())
                        elif name.startswith('assemble'):
                            self.assertFalse(any((f.pipeline/'saturday_candidates/2026-10-17').glob('.*.tmp')))
                            self.assertEqual(cli(a,argv)[1]['status'],'ALREADY_STAGED')
                        else:
                            self.assertIn('PUBLISHED',f.ledger.read_text());self.assertEqual(result['ledger_rows_changed'],[148])

    def test_receipt_serialization_failure_precedes_every_consumer_write(self):
        for name in ('canon_product_router.py','assemble_saturday_candidate.py','reconcile_publication_receipt.py'):
            with self.subTest(consumer=name),tempfile.TemporaryDirectory() as temp:
                f=Fixture(Path(temp).resolve());a=f.install_review_tree()[name]
                if name.startswith('canon'):argv=route_inputs(f)
                elif name.startswith('assemble'):stage_inputs(f);argv=['--run','183','--date','2026-10-17']
                else:argv=reconcile_inputs(f)
                real=a.effective_allocation_view
                def factory(*args,**kwargs):
                    view=real(*args,**kwargs)
                    if name.startswith('assemble'):
                        call=view.run_receipt
                        view.run_receipt=lambda run:{**call(run),'unserializable':object()}
                    else:
                        call=view.receipt
                        view.receipt=lambda:{**call(),'unserializable':object()}
                    return view
                before={str(p):p.read_bytes() for p in f.root.rglob('*') if p.is_file()}
                with ExitStack() as stack:
                    stack.enter_context(f.test_pins_in_real_loader(a));stack.enter_context(mock.patch.object(a,'effective_allocation_view',side_effect=factory))
                    if name.startswith('assemble'):stack.enter_context(assembler_helpers(a))
                    writes=stack.enter_context(mock.patch.object(a,'write_json_atomic',wraps=a.write_json_atomic))
                    rc,result=cli(a,argv)
                self.assertEqual(rc,2,result);self.assertIn('SERIALIZATION',result.get('error',''))
                self.assertEqual(writes.call_count,0)
                self.assertEqual(before,{str(p):p.read_bytes() for p in f.root.rglob('*') if p.is_file()})
                self.assertFalse((f.pipeline/'saturday_candidates').exists())

    def test_path_overlay_receipt_is_frozen_as_json_string(self):
        binding={**self.f.binding,'path':self.f.overlay_path}
        view=self.f.ns['resolve'](self.f.finalized,self.f.surface,correction=binding,ledger_path=self.f.ledger,
            expected_ledger_sha256=digest(self.f.ledger.read_bytes()))
        self.assertEqual(json.loads(json.dumps(view.receipt()))['correction']['overlay'],self.f.binding)

    def test_no_overlay_never_falls_back_when_original177_removed_or_not_ready(self):
        f=self.f;p=f.finalized/'Run-177/RELEASE_BINDING_PROPOSAL.json';raw=p.read_bytes();f.row148()
        for removed in (False,True):
            if removed:p.unlink()
            else:save(p,{**json.loads(raw),'status':'BOUND_LOCAL'})
            with self.assertRaisesRegex(f.ns['AllocationHold'],'APPROVED_183_OVERLAY_REQUIRED'):f.resolve(correction=False)
            p.write_bytes(raw)

    def test_no_overlay_cannot_accept_ledger_cas_even_without183(self):
        f=self.f;(f.finalized/'Run-183/RELEASE_BINDING_PROPOSAL.json').unlink()
        with self.assertRaisesRegex(f.ns['AllocationHold'],'EXPLICIT_OVERLAY_REQUIRED'):
            f.ns['resolve'](f.finalized,f.surface,ledger_path=f.ledger,expected_ledger_sha256=digest(f.ledger.read_bytes()))

    def test_every_occupied_effective_proposal_row_requires_exact_same_identity(self):
        f=self.f;stage_inputs(f,'Run-180','AAA',144)
        for title,run in [('Title Run-180','Run-180'),('Other title','Run-180'),('Title Run-180','Run-181')]:
            f.ledger.write_text(f'| 144 | d | **AAA — {title}** | nightly {run} | s | scope | route | HELD | — |\n')
            if run=='Run-180' and title=='Title Run-180':self.assertEqual(f.resolve().proposal('Run-180')['proposed_ledger_row'],144)
            else:
                with self.assertRaisesRegex(f.ns['AllocationHold'],'OCCUPIED_PROPOSAL_IDENTITY'):f.resolve()

    def test_historical_published_short_title_still_requires_exact_run_abbreviation_and_doi(self):
        f=self.f;stage_inputs(f,'Run-180','AAA',144)
        def line(abbreviation='AAA',run='Run-180',status='🌐 PUBLISHED — CC-BY-4.0',doi='`10.5281/zenodo.999`'):
            return f'| 144 | date | **{abbreviation} — Historical short title** | nightly {run} | evidence | scope | route | {status} | {doi} |\n'
        f.ledger.write_text(line());self.assertEqual(f.resolve().proposal('Run-180')['proposed_ledger_row'],144)
        for kwargs in ({'abbreviation':'AAA extra'},{'run':'Run-181'},{'doi':'pending'},{'status':'HELD'}):
            f.ledger.write_text(line(**kwargs))
            with self.assertRaisesRegex(f.ns['AllocationHold'],'OCCUPIED_PROPOSAL_IDENTITY'):f.resolve()

    def test_no_overlay_branch_crosschecks_ledger_and_uses_its_maximum(self):
        f=self.f;(f.finalized/'Run-183/RELEASE_BINDING_PROPOSAL.json').unlink()
        f.ledger.write_text('| 147 | d | **OTHER — another** | nightly Run-190 | s | scope | route | HELD | — |\n')
        with self.assertRaisesRegex(f.ns['AllocationHold'],'OCCUPIED_PROPOSAL_IDENTITY'):f.resolve(correction=False)
        f.ledger.write_text('| 150 | d | historical | old | s | scope | route | HELD | — |\n')
        self.assertEqual(f.resolve(correction=False).authoritative_max,150)

    def test_staging_idempotency_after_unrelated_inputs_and_legacy_unaffected_bundle(self):
        a=self.modules['assemble_saturday_candidate.py'];f=self.f;stage_inputs(f,'Run-180','AAA',144)
        kw=dict(finalized_root=f.finalized,package_root=f.pipeline/'nightly_packages',staging_root=f.pipeline/'staging',ledger_path=f.ledger)
        def replay():
            try:return a.stage_candidate('180','2026-10-17',**kw)['status']
            except Exception as exc:return 'UNEXPECTED '+type(exc).__name__+': '+str(exc)
        with f.test_pins_in_real_loader(a),assembler_helpers(a):
            first=a.stage_candidate('180','2026-10-17',**kw);self.assertEqual(first['status'],'STAGED_CANDIDATE')
            manifest=Path(first['bundle'])/'BUNDLE_MANIFEST.json';original=manifest.read_bytes()
            for edit in ('ledger','proposal'):
                if edit=='ledger':f.ledger.write_text(f.ledger.read_text()+'| 150 | d | **ZZZ — unrelated** | nightly Run-150 | s | scope | r | HELD | — |\n')
                else:save(f.finalized/'Run-191/RELEASE_BINDING_PROPOSAL.json',dict(run_id='Run-191',status='READY_FOR_EXACT_AUTHORIZATION',proposed_ledger_row=149))
                self.assertEqual(replay(),'ALREADY_STAGED')
                self.assertEqual(manifest.read_bytes(),original)
            legacy=json.loads(original);legacy['release_binding_proposal'].pop('effective_allocation_receipt')
            save(manifest,legacy)
            self.assertEqual(replay(),'ALREADY_STAGED')
            legacy['release_binding_proposal']['proposed_ledger_row']=145;save(manifest,legacy)
            with self.assertRaisesRegex(a.AssemblyError,'existing staged bundle differs'):a.stage_candidate('180','2026-10-17',**kw)

    def test_same_run_stable_receipt_changes_only_when_its_inputs_change(self):
        f=self.f;stage_inputs(f,'Run-180','AAA',144)
        before={run:f.resolve().run_receipt(run) for run in ('Run-180','Run-183')}
        f.row148();save(f.finalized/'Run-191/RELEASE_BINDING_PROPOSAL.json',dict(run_id='Run-191',status='READY_FOR_EXACT_AUTHORIZATION',proposed_ledger_row=149))
        for run in before:self.assertEqual(f.resolve().run_receipt(run),before[run])
        p=f.finalized/'Run-180/RELEASE_BINDING_PROPOSAL.json';save(p,{**json.loads(p.read_bytes()),'proposed_license':'different'})
        self.assertNotEqual(f.resolve().run_receipt('Run-180'),before['Run-180'])

    def test_scan_records_one_late_allocation_hold_and_continues(self):
        a=self.modules['assemble_saturday_candidate.py'];f=self.f
        stage_inputs(f);stage_inputs(f,'Run-180','AAA',144);stage_inputs(f,'Run-181','BBB',145)
        real_stage=a.stage_candidate;active={'run':None}
        def stage(run,*args,**kwargs):
            active['run']=run
            return real_stage(run,*args,**kwargs)
        def lockstep():
            if active['run']=='Run-180':f.ledger.write_bytes(f.ledger.read_bytes()+b' ')
            return SimpleNamespace(load_post_aristotle_review=lambda *args:None)
        with f.test_pins_in_real_loader(a),assembler_helpers(a),mock.patch.object(a,'load_lockstep',side_effect=lockstep),mock.patch.object(a,'stage_candidate',side_effect=stage):
            try:result=a.scan('2026-10-17',finalized_root=f.finalized)
            except Exception as exc:result={'scan_aborted':type(exc).__name__+': '+str(exc)}
        self.assertIn('holds',result,result)
        self.assertEqual([v['run_id'] for v in result['holds']],['Run-180'])
        self.assertIn('INPUT_RACE',result['holds'][0]['reason'])
        self.assertIn('Run-181',[v['run_id'] for v in result['staged']])

    def test_bind_and_promotion_cli_never_gain_authority_from_overlay(self):
        a=self.modules['assemble_saturday_candidate.py'];f=self.f
        flags=['--allocation-correction',str(f.overlay_path),'--allocation-correction-sha256',f.binding['sha256'],'--expected-ledger-sha256',digest(f.ledger.read_bytes())]
        for argv in (['--bind-ledger','183','--row','148','--justin-authorized'],['--promote-ledger-cleared']):
            with mock.patch.object(a,'bind_ledger') as bind,mock.patch.object(a,'promote_ledger_cleared') as promote:
                rc,result=cli(a,[*argv,'--date','2026-10-17',*flags])
            self.assertEqual(rc,2);self.assertIn('does not authorize',result['error']);bind.assert_not_called();promote.assert_not_called()

    def test_router_second_cas_removes_only_its_owned_route_on_race(self):
        a=self.modules['canon_product_router.py'];f=self.f;route_inputs(f);real=a.write_json_atomic
        def write(path,value):
            real(path,value)
            if path.name=='CANON_PRODUCT_ROUTE.json':f.ledger.write_bytes(f.ledger.read_bytes()+b' ')
        with f.test_pins_in_real_loader(a),mock.patch.object(a,'write_json_atomic',side_effect=write):
            rc,result=cli(a,['--run','191'])
        self.assertEqual(rc,2);self.assertIn('INPUT_RACE',result['error'])
        self.assertFalse((f.finalized/'Run-191/CANON_PRODUCT_ROUTE.json').exists())
        self.assertFalse((f.finalized/'Run-191/RELEASE_BINDING_PROPOSAL.json').exists())

    def test_automatic_overlay_missing_or_stale_pin_holds_closed(self):
        pins={key:copy.deepcopy(self.f.ns[key]) for key in ('ORIGINALS','SCIENCE','OVERLAY_SHA256','AUTHORITY_SHA256',
            'LINKED_PROPOSAL_SHA256','LOCAL_BINDING_SHA256','LOCAL_DECISIONS_SHA256')}
        for a in self.modules.values():
            real=a.load_effective_allocation
            def load():
                ns=real();ns.update(pins);return ns
            raw=self.f.overlay_path.read_bytes();self.f.overlay_path.unlink()
            with mock.patch.object(a,'load_effective_allocation',side_effect=load),self.assertRaisesRegex(Exception,'REGULAR_INPUT'):
                a.effective_allocation_view(self.f.finalized,self.f.surface)
            self.f.overlay_path.write_bytes(raw+b' ')
            with mock.patch.object(a,'load_effective_allocation',side_effect=load),self.assertRaisesRegex(Exception,'EXACT_INPUT_HASH'):
                a.effective_allocation_view(self.f.finalized,self.f.surface)
            self.f.overlay_path.write_bytes(raw)


if __name__=='__main__':unittest.main()
