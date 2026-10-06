"""O01–O20 approved amendment OAI cases. Offline fixtures never make API calls."""
from copy import deepcopy
import base64
import zlib
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import amendment_oai as oai
from publication_preservation import managed_pid_payload
from server_managed_fields import transport_contract_sha256, require_pids
from zenodo_transport import TransportHold


# Portable exact historical helper fixture: own draft metadata/file identities,
# no credential or verifier raw diagnostics. Decode hash is the reviewed418eaed body.
_HISTORICAL_21968301_REPAIR_ZLIB_B64 = (
    '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'
)

def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()


def source_validator(stage, actual, expected, context):
    """Independent fixture validator: no PID exemption beyond caller projection."""
    left, right = deepcopy(actual), deepcopy(expected)
    if stage == 'INITIAL_EDIT':
        for field in ('is_draft', 'is_published', 'revision_id', 'expires_at'):
            left.pop(field, None); right.pop(field, None)
    if left != right:
        raise TransportHold('INDEPENDENT_SOURCE_MISMATCH:' + stage)
    return {'status': 'SOURCE_VALIDATION_PASS'}


class Fixture:
    def __init__(self, parent, name, *, host='sandbox.zenodo.org', route=oai.ROUTE_A,
                 failure_ref=None, final_pid_exact=True, sandbox_doi_external=False):
        self.host = host; self.rid = '1001'; self.route = route
        self.out = Path(parent, name); self.out.mkdir()
        self.seq = 0
        self.original = {'id': self.rid, 'is_draft': False, 'is_published': True,
            'revision_id': 1, 'expires_at': None,
            'metadata': {'title': 'Exact original title', 'description': 'Original claim',
                'subjects': [{'subject': 'science'}], 'rights': [{'id': 'cc-by-4.0'}],
                'related_identifiers': [{'identifier': '10.5281/zenodo.77', 'relation_type': {'id': 'isderivedfrom'}}]},
            'pids': {'doi': {'identifier': ('10.5072' if host == 'sandbox.zenodo.org' else '10.5281') + '/zenodo.1001',
                'provider': 'datacite', 'client': 'zenodo'},
                'oai': {'identifier': 'oai:zenodo.org:1001', 'provider': 'oai'},
                'other': {'identifier': 'original', 'provider': 'local'}},
            'parent': {'id': '77', 'pids': {'doi': {'identifier': '10.5281/zenodo.77', 'provider': 'datacite'}}},
            'versions': {'index': 1, 'is_latest': True}, 'custom_fields': {},
            'access': {'record': 'public', 'files': 'public'},
            'files': {'entries': {f'f{i}.txt': {'key': f'f{i}.txt', 'id': str(i),
                'checksum': 'md5:' + f'{i:032x}', 'size': i + 1, 'metadata': {'exact': True}}
                for i in range(5)}}}
        self.initial = deepcopy(self.original)
        self.initial.update(is_draft=True, is_published=False, revision_id=2, expires_at='2026-10-06T00:00:00Z')
        self.payload = {'metadata': {'title': self.original['metadata']['title'],
            'doi': self.original['pids']['doi']['identifier'],
            'description': 'UNCERTIFIED exact reviewed description', 'keywords': ['science', 'uncertified']}}
        self.body_ref = self.file_ref('metadata-body.json', self.payload)
        self.after = deepcopy(self.initial)
        self.after['metadata'].update(description=self.payload['metadata']['description'],
            subjects=[{'subject': word} for word in self.payload['metadata']['keywords']])
        self.after['pids'].pop('oai')
        if sandbox_doi_external:
            self.after['pids']['doi'] = {'identifier': self.original['pids']['doi']['identifier'], 'provider': 'external'}
        self.final = deepcopy(self.original)
        self.final['metadata'] = deepcopy(self.after['metadata'])
        if not final_pid_exact:
            self.final['pids'].pop('oai')
        self.receipts = {}
        self.receipts['create'] = self.receipt('POST', '/api/deposit/depositions',
            {'id': self.rid, 'state': 'unsubmitted', 'submitted': False})
        self.receipts['initial_publish'] = self.receipt('POST', self.deposit+'/actions/publish', {'id': self.rid}, body=b'{}')
        self.receipts['original_native'] = self.receipt('GET', self.record, self.original, native=True)
        self.receipts['edit'] = self.receipt('POST', self.deposit+'/actions/edit',
            {'id': self.rid, 'state': 'inprogress', 'submitted': True}, body=b'{}')
        self.receipts['initial_edit_native'] = self.receipt('GET', self.record+'/draft', self.initial, native=True)
        self.receipts['metadata_put'] = self.receipt('PUT', self.deposit, {'id': self.rid}, body=Path(self.body_ref['path']).read_bytes())
        self.receipts['after_put_native'] = self.receipt('GET', self.record+'/draft', self.after, native=True)
        if route == oai.ROUTE_B:
            self.restored = deepcopy(self.after); self.restored['pids'] = deepcopy(self.original['pids'])
            self.restore_body_ref = self.file_ref('restore-body.json', managed_pid_payload(self.original, self.after))
            self.receipts['restore'] = self.receipt('PUT', self.record+'/draft', {'id': self.rid}, native=True,
                body=Path(self.restore_body_ref['path']).read_bytes())
            self.receipts['after_restore_native'] = self.receipt('GET', self.record+'/draft', self.restored, native=True)
        self.receipts['publish'] = self.receipt('POST', self.deposit+'/actions/publish', {'id': self.rid}, body=b'{}')
        self.receipts['final_native'] = self.receipt('GET', self.record, self.final, native=True)
        self.proof = {'schema': oai.SCHEMA, 'route': route, 'host': host, 'record_id': self.rid,
            'transport_contract_sha256': transport_contract_sha256(), 'receipts': self.receipts,
            'metadata_put_body': self.body_ref}
        if route == oai.ROUTE_B:
            self.proof.update(restore_body=self.restore_body_ref, route_a_failure=failure_ref)
        self.proof_ref = self.file_ref('proof.json', self.proof)

    @property
    def deposit(self): return '/api/deposit/depositions/' + self.rid
    @property
    def record(self): return '/api/records/' + self.rid

    def file_ref(self, name, value):
        path = self.out/name; path.write_bytes(encode(value))
        return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def receipt(self, method, path, response, *, native=False, body=None):
        self.seq += 1; name = f'{self.seq:03d}_{method}.json'
        value = {'method': method, 'url': 'https://' + self.host + path, 'environment': self.host,
            'accept': oai.NATIVE if native else 'application/json',
            'status': 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE', 'http_status': 200,
            'request_body_sha256': hashlib.sha256(body).hexdigest() if body is not None else None,
            'response_sha256': hashlib.sha256(encode(response)).hexdigest(), 'response': deepcopy(response)}
        path = self.out/name; path.write_bytes(encode(value))
        return {'receipt_path': str(path), 'receipt_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'transport_contract_sha256': transport_contract_sha256()}

    def change_receipt(self, name, mutation, *, refresh=True):
        ref = self.receipts[name]; path = Path(ref['receipt_path']); value = json.loads(path.read_bytes())
        mutation(value); path.write_bytes(encode(value))
        if refresh:
            ref['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.refresh_proof()

    def refresh_proof(self):
        self.proof_ref = self.file_ref('proof.json', self.proof)

    def transition(self):
        return {**{name: self.receipts[name] for name in ('original_native','edit','initial_edit_native',
            'metadata_put','after_put_native')}, 'metadata_put_body': self.body_ref}

    def qualify(self):
        return oai.qualify_sandbox_route(self.proof_ref, source_validator=source_validator)

    def definite_rejection(self):
        def reject(r):
            r.pop('response',None);r.pop('response_sha256',None)
            r.update(status='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY',http_status=400,error_type='HTTPError',
                error_response={'status':400,'message':'A validation error occurred.','errors':[{
                    'field':'pids.doi','messages':["The prefix '10.5072' is managed by Zenodo. Please supply an external DOI or select 'No' to have a DOI generated for you."]}]})
        self.change_receipt('publish',reject)
        self.change_receipt('final_native',lambda r:r.__setitem__('response',deepcopy(self.original)))
        self.receipts['post_failure_draft_native']=self.receipt('GET',self.record+'/draft',self.after,native=True)
        self.proof['failure_kind']='DEFINITE_HTTP400_MANAGED_DOI_REJECTION'
        self.refresh_proof()
        return self.proof_ref


class AmendmentOAICases(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.count = 0
        self.sandbox = self.fixture()
        self.qualified = self.sandbox.qualify()
        self.production = self.fixture(host='zenodo.org')

    def fixture(self, **kwargs):
        self.count += 1
        return Fixture(self.temp.name, 'fixture-' + str(self.count), **kwargs)

    def classify(self, fixture=None, **extra):
        f = fixture or self.production
        context = dict(host=f.host, record_id=f.rid, transition_evidence=f.transition(),
            qualification=self.qualified, source_validator=source_validator,
            current_public=deepcopy(f.original))
        context.update(extra)
        return oai.classify_own_draft(deepcopy(f.after), deepcopy(f.original), **context)

    def assert_hold(self, callback):
        with self.assertRaises(TransportHold): callback()

    def test_O01_sandbox_route_A_and_route_B_exact_public_proofs(self):
        self.assertEqual(self.qualified.route, oai.ROUTE_A)
        failure = self.fixture(final_pid_exact=False, sandbox_doi_external=True)
        self.assert_hold(failure.qualify)
        b = self.fixture(route=oai.ROUTE_B, failure_ref=failure.proof_ref, sandbox_doi_external=True)
        self.assertEqual(b.qualify().route, oai.ROUTE_B)
        definite=self.fixture(sandbox_doi_external=True);definite.definite_rejection()
        b=self.fixture(route=oai.ROUTE_B,failure_ref=definite.proof_ref,sandbox_doi_external=True)
        self.assertEqual(b.qualify().route,oai.ROUTE_B)
        state = self.classify()
        self.assertEqual(state.status, 'TRANSIENT_OAI_ROUTE_A_READY')
        self.assertTrue(oai.require_publish_ready(state, state.current_draft)['publication_allowed'])
        q=b.qualify();pending=self.classify(qualification=q)
        f=self.production;restored=deepcopy(f.after);restored['pids']=deepcopy(f.original['pids'])
        body=f.file_ref('prod-exact-restore.json',managed_pid_payload(f.original,f.after))
        put=f.receipt('PUT',f.record+'/draft',{'id':f.rid},native=True,body=Path(body['path']).read_bytes())
        get=f.receipt('GET',f.record+'/draft',restored,native=True)
        ready=oai.require_exact_restoration(pending,restored,restore_evidence=put,
            restore_body_reference=body,restored_native_evidence=get,host=f.host,
            record_id=f.rid,source_validator=source_validator)
        self.assertTrue(oai.require_publish_ready(ready,restored)['publication_allowed'])

    def test_O02_real_saved_21968301_helper_body_exact_offline(self):
        raw=zlib.decompress(base64.b64decode(_HISTORICAL_21968301_REPAIR_ZLIB_B64))
        repair=json.loads(raw)
        original={'id':'21968301','pids':deepcopy(repair['pids'])}
        edit=deepcopy(repair);edit['id']='21968301'
        after=deepcopy(edit);after['pids'].pop('oai')
        oai._omission(original,edit,after,'21968301')
        self.assertEqual(managed_pid_payload(original,after),repair)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'418eaedb89a4eae4e897367e0758eb6770dee10e4ead20dd180ce4fa40066630')
        self.assertEqual(len(after['files']['entries']),24)
        self.assertEqual(after['files'],edit['files'])

    def test_O03_initial_edit_omission_or_missing_PUT_blocks(self):
        f = self.fixture(host='zenodo.org')
        f.change_receipt('initial_edit_native', lambda r: r['response']['pids'].pop('oai'))
        self.assert_hold(lambda: self.classify(f))
        f = self.fixture(host='zenodo.org'); evidence=f.transition(); evidence.pop('metadata_put')
        self.assert_hold(lambda: self.classify(f, transition_evidence=evidence))

    def test_O04_original_oai_must_have_exact_namespace_id_provider_shape(self):
        variants = [None, {}, {'identifier':'oai:sandbox.zenodo.org:1001','provider':'oai'},
            {'identifier':'oai:zenodo.org:1002','provider':'oai'},
            {'identifier':'oai:zenodo.org:1001','provider':'external'},
            {'identifier':'oai:zenodo.org:1001','provider':'oai','unknown':True}]
        for variant in variants:
            with self.subTest(variant=variant):
                f=self.fixture(host='zenodo.org')
                f.change_receipt('original_native', lambda r,v=variant:r['response']['pids'].__setitem__('oai',v))
                self.assert_hold(lambda:self.classify(f))

    def test_O05_every_other_PID_change_is_rejected_in_production(self):
        for field in ('identifier','provider','client','other','new','remove'):
            with self.subTest(field=field):
                f=self.fixture(host='zenodo.org')
                if field in ('identifier','provider','client'): f.after['pids']['doi'][field]='changed'
                elif field=='other':f.after['pids']['other']['identifier']='changed'
                elif field=='new':f.after['pids']['new']={'identifier':'new','provider':'local'}
                else:f.after['pids'].pop('doi')
                f.change_receipt('after_put_native',lambda r:r.__setitem__('response',deepcopy(f.after)))
                self.assert_hold(lambda:self.classify(f))
        f=self.fixture(host='zenodo.org',sandbox_doi_external=True)
        self.assert_hold(lambda:self.classify(f))

    def test_O06_missing_tampered_reversed_failed_foreign_receipts(self):
        for kind in ('tampered','non2xx','foreign','body','transport','reversed','missing'):
            with self.subTest(kind=kind):
                f=self.fixture(host='zenodo.org'); evidence=f.transition()
                if kind=='tampered':f.change_receipt('edit',lambda r:r.__setitem__('http_status',201),refresh=False)
                elif kind=='non2xx':f.change_receipt('metadata_put',lambda r:r.__setitem__('http_status',500))
                elif kind=='foreign':f.change_receipt('edit',lambda r:r.__setitem__('url','https://zenodo.org/api/deposit/depositions/1002/actions/edit'))
                elif kind=='body':f.change_receipt('metadata_put',lambda r:r.__setitem__('request_body_sha256','0'*64))
                elif kind=='transport':evidence['edit']['transport_contract_sha256']='0'*64
                elif kind=='reversed':evidence['edit'],evidence['metadata_put']=evidence['metadata_put'],evidence['edit']
                else:evidence.pop('edit')
                self.assert_hold(lambda:self.classify(f,transition_evidence=evidence))

    def test_O07_unreviewed_metadata_changes_never_hidden_by_oai_projection(self):
        for field in ('title','description','subjects','rights','related_identifiers'):
            with self.subTest(field=field):
                f=self.fixture(host='zenodo.org');f.after['metadata'][field]='changed'
                f.change_receipt('after_put_native',lambda r:r.__setitem__('response',deepcopy(f.after)))
                self.assert_hold(lambda:self.classify(f))

    def test_O08_every_main_file_field_and_count_remains_checked(self):
        for field in ('key','id','checksum','size','metadata','count'):
            with self.subTest(field=field):
                f=self.fixture(host='zenodo.org')
                if field=='count':f.after['files']['entries'].pop('f0.txt')
                else:f.after['files']['entries']['f0.txt'][field]='changed'
                f.change_receipt('after_put_native',lambda r:r.__setitem__('response',deepcopy(f.after)))
                self.assert_hold(lambda:self.classify(f))

    def test_O09_custom_parent_version_prior_unknown_source_changes_fail(self):
        for field in ('custom_fields','parent','versions','unknown'):
            with self.subTest(field=field):
                f=self.fixture(host='zenodo.org');f.after[field]={'changed':True}
                f.change_receipt('after_put_native',lambda r:r.__setitem__('response',deepcopy(f.after)))
                self.assert_hold(lambda:self.classify(f))

    def test_O10_public_changes_before_publish_hard_stop(self):
        for kind in ('oai','doi','content','file'):
            with self.subTest(kind=kind):
                public=deepcopy(self.production.original)
                if kind=='oai':public['pids'].pop('oai')
                elif kind=='doi':public['pids']['doi']['identifier']='changed'
                elif kind=='content':public['metadata']['description']='changed'
                else:public['files']['entries']['f0.txt']['checksum']='changed'
                self.assert_hold(lambda:self.classify(current_public=public))

    def test_O11_restore_body_extra_field_wrong_PID_SHA_or_stale_snapshot_fails(self):
        failure=self.fixture(final_pid_exact=False);b=self.fixture(route=oai.ROUTE_B,failure_ref=failure.proof_ref)
        for kind in ('extra','pid','sha','stale'):
            with self.subTest(kind=kind):
                body=managed_pid_payload(b.original,b.after)
                if kind=='extra':body['unknown']=True
                elif kind=='pid':body['pids']['oai']['identifier']='changed'
                elif kind=='stale':body['metadata']['title']='stale'
                ref=b.file_ref('bad-restore-'+kind+'.json',body)
                if kind=='sha':ref['sha256']='0'*64
                proof=deepcopy(b.proof);proof['restore_body']=ref
                bad=b.file_ref('bad-proof-'+kind+'.json',proof)
                self.assert_hold(lambda:oai.qualify_sandbox_route(bad,source_validator=source_validator))
        state=self.classify()
        self.assert_hold(lambda:oai.require_exact_restoration(state,state.current_draft,restore_evidence={},
            restore_body_reference={},restored_native_evidence={},host='zenodo.org',record_id='1001',source_validator=source_validator))

    def test_O12_proof_host_route_transport_id_sequence_and_routeA_failure_bound(self):
        for key,value in (('host','zenodo.org'),('route','UNKNOWN'),('record_id','1002'),('transport_contract_sha256','0'*64)):
            proof=deepcopy(self.sandbox.proof);proof[key]=value;ref=self.sandbox.file_ref('bad-'+key+'.json',proof)
            self.assert_hold(lambda:oai.qualify_sandbox_route(ref,source_validator=source_validator))
        proof=deepcopy(self.sandbox.proof);proof['receipts'].pop('publish');ref=self.sandbox.file_ref('missing-publish.json',proof)
        self.assert_hold(lambda:oai.qualify_sandbox_route(ref,source_validator=source_validator))
        self.assert_hold(lambda:oai.qualify_sandbox_route(self.sandbox.proof_ref,source_validator=None))
        self.assert_hold(lambda:oai.qualify_sandbox_route(self.sandbox.proof_ref,
            source_validator=lambda*args:{'status':'HOLD'}))
        b=self.fixture(route=oai.ROUTE_B,failure_ref=self.sandbox.proof_ref)
        self.assert_hold(b.qualify)
        for kind in ('timeout','pending','foreign','wrongerror','publicPIDloss','draftchange'):
            with self.subTest(definite_failure=kind):
                a=self.fixture(sandbox_doi_external=True);a.definite_rejection()
                if kind=='timeout':a.change_receipt('publish',lambda r:r.update(error_type='TimeoutError',http_status=None))
                elif kind=='pending':a.change_receipt('publish',lambda r:r.update(http_status=202))
                elif kind=='foreign':a.change_receipt('publish',lambda r:r.__setitem__('url','https://sandbox.zenodo.org/api/deposit/depositions/1002/actions/publish'))
                elif kind=='wrongerror':a.change_receipt('publish',lambda r:r['error_response']['errors'][0].__setitem__('field','metadata.title'))
                elif kind=='publicPIDloss':a.change_receipt('final_native',lambda r:r['response']['pids'].pop('oai'))
                else:a.change_receipt('post_failure_draft_native',lambda r:r['response']['metadata'].__setitem__('title','changed'))
                b=self.fixture(route=oai.ROUTE_B,failure_ref=a.proof_ref,sandbox_doi_external=True)
                self.assert_hold(b.qualify)

    def test_O13_native_restore_rejection_ambiguity_or_timeout_cannot_qualify(self):
        failure=self.fixture(final_pid_exact=False)
        for kind in ('http','uncertain','wrongid'):
            b=self.fixture(route=oai.ROUTE_B,failure_ref=failure.proof_ref)
            if kind=='http':b.change_receipt('restore',lambda r:r.__setitem__('http_status',500))
            elif kind=='uncertain':b.change_receipt('restore',lambda r:r.__setitem__('status','HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'))
            else:b.change_receipt('restore',lambda r:r['response'].__setitem__('id','1002'))
            self.assert_hold(b.qualify)

    def test_O14_missing_null_wrong_or_unlisted_restored_PID_blocks_publish(self):
        failure=self.fixture(final_pid_exact=False)
        for kind in ('missing','null','wrong','extra'):
            b=self.fixture(route=oai.ROUTE_B,failure_ref=failure.proof_ref)
            def mutate(r):
                if kind=='missing':r['response']['pids'].pop('oai')
                elif kind=='null':r['response']['pids']['oai']=None
                elif kind=='wrong':r['response']['pids']['oai']['identifier']='wrong'
                else:r['response']['pids']['unknown']={'identifier':'unknown','provider':'local'}
            b.change_receipt('after_restore_native',mutate)
            self.assert_hold(b.qualify)

    def test_O15_restore_changes_description_subjects_source_or_files_fail(self):
        failure=self.fixture(final_pid_exact=False)
        for field in ('description','subjects','title','access','files'):
            b=self.fixture(route=oai.ROUTE_B,failure_ref=failure.proof_ref)
            def mutate(r):
                if field in ('description','subjects','title'):r['response']['metadata'][field]='changed'
                else:r['response'][field]={'changed':True}
            b.change_receipt('after_restore_native',mutate)
            self.assert_hold(b.qualify)

    def test_O16_final_public_every_original_PID_exact_absolute_hard_stop(self):
        for kind in ('missing','null','wrong','doi','other'):
            f=self.fixture()
            def mutate(r):
                if kind=='missing':r['response']['pids'].pop('oai')
                elif kind=='null':r['response']['pids']['oai']=None
                elif kind=='wrong':r['response']['pids']['oai']['provider']='wrong'
                elif kind=='doi':r['response']['pids']['doi']['client']='wrong'
                else:r['response']['pids']['other']['identifier']='wrong'
            f.change_receipt('final_native',mutate)
            self.assert_hold(f.qualify)

    def test_O17_exact_original_PIDs_use_normal_path_no_extra_native_write(self):
        f=self.production;actual=deepcopy(f.after);actual['pids']=deepcopy(f.original['pids'])
        state=oai.classify_own_draft(actual,f.original,host='zenodo.org',record_id='1001')
        self.assertEqual(state.status,'NORMAL_EXACT_PIDS');self.assertIsNone(state.route)
        self.assertTrue(oai.require_publish_ready(state,actual)['publication_allowed'])

    def test_O18_newversion_prior_published_absentnull_exemption_never_applies(self):
        for extra in ({'operation':'NEW_VERSION'},{'operation':'PRIOR_VERSION'},{'phase':'PUBLISHED'}):
            self.assert_hold(lambda:self.classify(**extra))
        actual=deepcopy(self.production.original);actual['pids'].pop('oai')
        self.assert_hold(lambda:require_pids(actual,self.production.original,host='zenodo.org',record_id='1001'))
        actual['pids']['oai']=None
        self.assert_hold(lambda:require_pids(actual,self.production.original,host='zenodo.org',record_id='1001'))
        forged=oai.RouteQualification(oai.ROUTE_A,self.qualified.proof_path,self.qualified.proof_sha256,
            self.qualified.transport_sha256,self.qualified.references)
        self.assert_hold(lambda:self.classify(qualification=forged))

    def test_O19_foreign_record_draft_or_stale_current_state_fails(self):
        for kind in ('id','is_draft','metadata','pid'):
            f=self.fixture(host='zenodo.org')
            if kind=='id':f.after['id']='1002'
            elif kind=='is_draft':f.after['is_draft']=False
            elif kind=='metadata':f.after['metadata']['title']='stale'
            else:f.after['pids']['doi']['identifier']='foreign'
            self.assert_hold(lambda:self.classify(f))
        state=self.classify();changed=deepcopy(state.current_draft);changed['revision_id']=999
        self.assert_hold(lambda:oai.require_publish_ready(state,changed))

    def test_O20_publish_blocked_unproven_or_B_pending_and_proof_tamper(self):
        calls=[]
        self.assert_hold(lambda:self.classify(qualification=None))
        failure=self.fixture(final_pid_exact=False)
        b=self.fixture(route=oai.ROUTE_B,failure_ref=failure.proof_ref);q=b.qualify()
        state=self.classify(qualification=q)
        self.assertEqual(state.status,'DRAFT_PID_REPAIR_REQUIRED')
        try:
            oai.require_publish_ready(state,state.current_draft);calls.append('publish')
        except TransportHold:pass
        self.assertEqual(calls,[])
        ready=self.classify()
        Path(self.sandbox.proof_ref['path']).write_text('{}')
        self.assert_hold(lambda:oai.require_publish_ready(ready,ready.current_draft))


if __name__ == '__main__':
    unittest.main()
