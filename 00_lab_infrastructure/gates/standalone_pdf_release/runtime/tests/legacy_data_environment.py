"""PRIVATE TEST ONLY real legacy99 validator DATA environment builder.

All executable source comes from exact public tracked blobs. Synthetic provider,
authority, path and hash DATA never represent real installation or science.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_source_chain import REPO, encoded, sha, gitblob
LEGACY_SHA='b52ad25d05298a6b3c166669e178df1f6f460665a9cc52816c899e1b28b88317'
CLOSE_SHA='c975a6e9a94ee2e17c2df806b103fc5bcf15b1e2ae62de625d4c163d75f30a98'

FIXTURE_DIR=Path(__file__).resolve().parent
SOURCE_SEED_SHA='cc516e4855e20ff0d10b43a1d174eb2c06a6e880d321bca04a675b2900ae8f2e'
G='RESEARCH_PIPELINE_v2/verification_coverage_gates/'


def read_anchor(name,digest):
    raw=(FIXTURE_DIR/name).read_bytes()
    assert sha(raw)==digest,(name,sha(raw))
    return raw


def get_fixture(root):
    path=REPO/'00_lab_infrastructure/gates/standalone_pdf_release/runtime/tests/w42_portable_fixture.py'
    spec=importlib.util.spec_from_file_location('_private_full_w42_science_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.PortableFixture(root)


def deduplicate_large_immutable_data(root,blob_root):
    """Reuse large synthetic JSON DATA bytes; no public repository hardlinks."""
    root=Path(root).resolve(strict=True);blob_root=Path(blob_root)
    assert blob_root.resolve().is_relative_to(root.parent)
    blob_root.mkdir(exist_ok=True)
    files=[p for p in root.rglob('*.json')if p.is_file()and not p.is_symlink()and p.stat().st_size>256*1024]
    for path in files:
        raw=path.read_bytes();digest=sha(raw);blob=blob_root/(digest+'.json')
        if not blob.exists():blob.write_bytes(raw)
        assert blob.read_bytes()==raw
        if path.stat().st_ino==blob.stat().st_ino:continue
        path.unlink();os.link(blob,path)
        assert path.read_bytes()==raw


def build_legacy_environment(root,loader):
    root=Path(root).resolve(strict=True)
    assert root==loader.root/'canonical-root'
    seed=json.loads(read_anchor('legacy_public_source_seed.json',SOURCE_SEED_SHA))
    assert seed['fixture_only']is True and seed['authority']is False
    original_rows=seed['source_rows']
    assert len(original_rows)==130 and len(seed['legacy_names'])==99
    source_provenance=[]
    for row in original_rows:
        public=REPO/row['git_path'];raw=public.read_bytes()
        assert sha(raw)==row['sha256'] and gitblob(raw)==row['git_blob_sha'],row['name']
        relative=Path(row['relative'])
        assert not relative.is_absolute() and '..'not in relative.parts
        source_provenance.append({'name':row['name'],'relative':str(relative),
            'git_path':row['git_path'],'production_sha256':sha(raw),'raw':raw})
    fixture=get_fixture(root)
    # Place only the measured130 public source layout, keeping the previously
    # disclosed literal trust-DATA suffixes in the three science fixture files.
    for row in source_provenance:
        path=root/row['relative'];path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes().startswith(row['raw']):continue
        path.write_bytes(row['raw'])
    fixture.put('RESEARCH_PIPELINE_v2/aristotle_forge_state.json',{
        'fixture_only':True,'authorizes':False,'status':'SYNTHETIC_PATH_INPUT_ONLY'})
    for digest,name,value in (
        ('a15ef655091ebd72910a060cdef1d0f727d18b7a7223dcbbc2192c18e39fe57c','CONTROL_ROOT',root),
        ('b63c3866db0e3538f6462ca32f0bbf916a6e80081d1bdf74514b1fa6c7dc2b06','LIVE_ROOT',fixture.gen),
    ):
        loader.remaps.setdefault(digest,{})[name]='Path('+repr(str(value))+')'
    # Complete the four real archival bodies. The current fixture policy uses
    # synthetic trust DATA and therefore gets its own derived test-only hash.
    current_catalog=json.loads(fixture.read('synthetic-trust/CATALOG.json'))
    current_entry=current_catalog['versions'][0]
    versions=[]
    for old_entry in fixture.seed['versions'][:-1]:
        identity=old_entry['execution_consumer_sha256'];files=[];prfiles=[]
        for row in old_entry['files']:
            raw=fixture.source(row['source']);relative=G+'policy_versions/'+identity+'/'+row['name']
            fixture.write(relative,raw)
            git='00_lab_infrastructure/gates/policy_versions/'+identity+'/'+row['name']
            files.append({'name':row['name'],'binding':fixture.relbound(relative),'git_path':git})
            prfiles.append({'path':git,'sha':gitblob(raw)})
        pr=fixture.put('synthetic-trust/archive-'+identity+'.json',fixture.pr(991+len(versions),prfiles))
        versions.append({'execution_consumer_sha256':identity,'files':files,
            'pull_request_readback':fixture.relbound(pr['path'])})
    versions.append(current_entry)
    # Original919 directory would create no extra normal pins (archives are
    # only read from the catalog); preserve it as raw public provenance only.
    catalog=fixture.put('synthetic-trust/CATALOG.json',{
        **current_catalog,'versions':versions})
    update=json.loads(fixture.read('synthetic-trust/CURRENT_RUNTIME.json'))
    flat_names={Path(row['path']).name for row in fixture.seed['current']['additional_modules']
                if '/policy_versions/'not in row['path']}
    additional=[];prfiles=[]
    archive_paths=[row['binding']['path']for entry in versions for row in entry['files']]
    for relative in sorted([G+n for n in flat_names]+archive_paths):
        raw=fixture.read(relative)
        capture=fixture.write('synthetic-trust/current-source/'+relative,raw)
        additional.append({'path':relative,'sha256':sha(raw),'source':fixture.relbound(capture)})
        prfiles.append({'path':'00_lab_infrastructure/gates/'+relative[len(G):],
                        'sha':gitblob(raw)})
    assert len(additional)==59
    for row in update['runtime_targets']:
        raw=fixture.read(row['path'])
        prfiles.append({'path':'00_lab_infrastructure/gates/'+Path(row['path']).name,
                        'sha':gitblob(raw)})
    merged=fixture.put('synthetic-trust/CURRENT_PR.json',fixture.pr(999,list({r['path']:r for r in prfiles}.values())))
    update.update(additional_modules=additional,policy_version_catalog=fixture.relbound(catalog['path']),
                  pull_request_readback=fixture.relbound(merged['path']))
    update_b=fixture.put('synthetic-trust/CURRENT_RUNTIME.json',update)
    original=json.loads(fixture.read(update['original_activation']['path']))
    wrapper=fixture.put('synthetic-trust/ACTIVATION.json',{
        **original,'authorized_runtime_update':fixture.relbound(update_b['path'])})
    fixture.ledger['enforcement_activation']=fixture.relbound(wrapper['path'])
    fixture.put('RESEARCH_PIPELINE_v2/corpus_ledger.json',fixture.ledger)
    # Historical JSON values are synthetic, hash-bound DATA. The inline close
    # receipt alone is original byteexact captured DATA and is never edited.
    previous=fixture.put('synthetic-trust/HISTORICAL_RUNTIME.json',{
        'fixture_only':True,'policy_version_catalog':fixture.relbound(catalog['path'])})
    prior_closure=fixture.put('synthetic-trust/HISTORICAL_CLOSURE.json',{
        'fixture_only':True,'historical_registration_recovery':{'fixture_only':True,'authorizes':False}})
    close=fixture.put('synthetic-trust/EXACT_HISTORICAL_CLOSE.json',
                      read_anchor('INSTALL_RECEIPT_c975a6e9.json',CLOSE_SHA))
    loader.remaps[LEGACY_SHA]['PRIOR_RUNTIME_SHA']=repr(previous['sha256'])
    loader.remaps[LEGACY_SHA]['PRIOR_CLOSURE_SHA']=repr(prior_closure['sha256'])
    # Keep the exact historical helper at its canonical synthetic report path.
    # Only its top-level path DATA differs at execution, never its source bytes.
    by_name={row['name']:row for row in source_provenance}
    builder_path=root/by_name['prepare_first_seven_plan.py']['relative']
    loader.register_source(builder_path,builder_path.read_bytes())
    for digest,remaps in loader.remaps.items():
        if 'BUILDER'in remaps:remaps['BUILDER']='Path('+repr(str(builder_path))+')'
    consumer_path=root/by_name['runtime_successor.py']['relative']
    loader.register_source(consumer_path,consumer_path.read_bytes())
    consumer=loader.load(consumer_path)
    output=root/'synthetic-trust/current-legacy-closure';output.mkdir()
    materials={name:fixture.read(G+name)for name in consumer.MATERIAL_NAMES}
    head='8'*40;commit='9'*40;tree_id='7'*40
    gitfiles=[{'path':'00_lab_infrastructure/gates/'+name,'sha':gitblob(raw)}for name,raw in sorted(materials.items())]
    pr=fixture.pr(997,gitfiles,commit);pr['headRefOid']=head
    tree={'sha':tree_id,'truncated':False,'tree':[dict(row,type='blob',mode='100644')for row in gitfiles]}
    merger={'sha':commit,'tree':{'sha':tree_id}}
    files=consumer.merged(pr,head,commit,merger,tree)
    proof=consumer.u.source_proof(files,materials)
    normalized=copy.deepcopy(pr);normalized['files']=[{k:row[k]for k in ('path','sha')}for row in proof]
    for name,value in {
        'CONFIG.json':{'predecessor_runtime':fixture.relbound(previous['path']),
            'predecessor_closure':fixture.relbound(prior_closure['path']),
            'predecessor_close':fixture.relbound(close['path']),
            'expected_head_sha':head,'expected_merge_commit':commit,
            'source_hashes':{name:sha(raw)for name,raw in materials.items()}},
        'RAW_PR_MERGED_READBACK.json':pr,'MERGED_COMMIT.json':merger,
        'COMPLETE_MERGED_TREE.json':tree,'PR_MERGED_READBACK.json':normalized,
        'SOURCE_ORIGIN_PROOF.json':{'status':'FULL_ACTUAL_MERGED_TREE_SOURCE_PROOF_NOT_INSTALLATION','files':proof},
        'POLICY_VERSION_CATALOG.json':json.loads(fixture.read(catalog['path'])),
    }.items():fixture.put(output/name,value)
    builder=consumer.load_builder()
    _,_,_,legacy_pins,edges,duplicates=consumer.pin_table(builder)
    production_by_hash={row['production_sha256']:row['raw']for row in source_provenance}
    for row in legacy_pins:
        path=Path(row['path']);raw=path.read_bytes()
        original=production_by_hash.get(sha(raw))
        if original is None:
            name=path.name
            original=fixture.original_source_bytes.get(name)
            assert original is not None and raw.startswith(original),(name,sha(raw))
            declared=fixture.constant_overrides[name]
        else:declared=None
        loader.register_source(path,raw,original_raw=original,declared_data_suffix=declared)
    actual=consumer.current_closure(output,update['protected_readback'])
    assert actual['source_pins']==legacy_pins and actual['source_pin_count']==99
    closure_b=fixture.put(output/'CURRENT_RUNTIME_CLOSURE.json',actual)
    assert consumer.read_bound_closure(fixture.relbound(closure_b['path']))==actual
    original_base_names=set(seed['legacy_names'])
    extra_rows=[]
    for row in source_provenance:
        if row['name']in original_base_names:continue
        path=root/row['relative'];raw=path.read_bytes()
        loader.register_source(path,raw)
        extra_rows.append({'name':row['name'],'path':str(path),'sha256':sha(raw)})
    base_pins=sorted([*legacy_pins,*extra_rows],key=lambda row:row['name'])
    assert len(base_pins)==130 and len({r['name']for r in base_pins})==130
    source_rows=[]
    for row in base_pins:
        original_row=by_name.get(row['name'])
        if original_row is not None:git=original_row['git_path']
        else:
            relative=str(Path(row['path']).relative_to(root))
            assert relative.startswith(G+'policy_versions/')
            git='00_lab_infrastructure/gates/'+relative[len(G):]
        source_rows.append({**row,'git_path':git,'git_blob_sha':gitblob(Path(row['path']).read_bytes())})
    origin_pr=fixture.pr(996,[{'path':r['git_path'],'sha':r['git_blob_sha']}for r in source_rows],commit)
    origin_pr['headRefOid']=head
    origin={
        'merged_pr':fixture.put('synthetic-trust/PURPOSE_PR.json',origin_pr),
        'merged_commit':fixture.put('synthetic-trust/PURPOSE_COMMIT.json',merger),
        'merged_tree':fixture.put('synthetic-trust/PURPOSE_TREE.json',{
            'sha':tree_id,'truncated':False,'tree':[{'path':r['git_path'],'type':'blob',
                'mode':'100644','sha':r['git_blob_sha']}for r in source_rows]}),
        'source_rows':source_rows,
    }
    builder_b={'path':str(builder_path),'sha256':sha(builder_path.read_bytes())}
    consumer_b={'path':str(consumer_path),'sha256':sha(consumer_path.read_bytes())}
    scope_b=fixture.put('synthetic-trust/CURRENT_SOURCE_SCOPE.json',{
        'standard':seed['scope_standard'],'canonical_root':str(root),
        'current_runtime_closure':closure_b,'runtime_consumer':consumer_b,
        'source_session_consumer':builder_b,'purpose_source_pins':base_pins,
        'source_origin':origin,'external_mutation':False,'new_run_ids':[],
        'source_material_inputs':[],
    })
    deduplicate_large_immutable_data(root,loader.root/'synthetic-large-data-blobs')
    return {'root':root,'science_fixture':fixture,'legacy_consumer_module':consumer,
        'closure_output':output,'protected_readback':update['protected_readback'],
        'legacy_pins':legacy_pins,'legacy_edges':edges,'legacy_duplicates':duplicates,
        'legacy_closure':closure_b,'legacy_scope':scope_b,'legacy_consumer':consumer_b,
        'session_consumer':builder_b,'base_pins':base_pins,'original_origin':origin,
        'actual_legacy_closure':actual,
        'original_source_control_provenance':seed['source_control_provenance'],
        'source_provenance':source_provenance,'data_declarations':{
            'historical_runtime_hash':previous['sha256'],'historical_closure_hash':prior_closure['sha256'],
            'byteexact_historical_close_sha256':CLOSE_SHA,'catalog_versions':len(versions),
            'runtime_targets':len(update['runtime_targets']),'additional_modules':len(additional)}}


def negative_probes(result):
    consumer=result['legacy_consumer_module'];output=result['closure_output']
    config_path=output/'CONFIG.json';config_raw=config_path.read_bytes()
    config=json.loads(config_raw);root=result['root'];out=[]
    def require_hold(name,expected):
        try:consumer.current_closure(output,result['protected_readback'])
        except ValueError as error:
            assert expected in str(error),(name,str(error))
            out.append({'probe':name,'result':'HOLD','intended_cause':expected,'observed':str(error)})
        else:raise AssertionError(name+' incorrectly admitted')
    # Refresh the outer binding to make the original inline SHA comparison,
    # rather than a merely stale binding, reject the synthetic close bytes.
    close_path=root/config['predecessor_close']['path'];close_raw=close_path.read_bytes()
    try:
        close_path.write_bytes(encoded({'fixture_only':True,'authorizes':False,'withdrawn':True}))
        changed=copy.deepcopy(config);changed['predecessor_close']['sha256']=sha(close_path.read_bytes())
        config_path.write_bytes(encoded(changed))
        require_hold('historical_close_with_fresh_outer_binding','HISTORICAL_BOUND_INPUT_CHANGED:predecessor_close')
    finally:close_path.write_bytes(close_raw);config_path.write_bytes(config_raw)
    source=root/G/'phase7_runtime_update.py';before=source.read_bytes()
    try:
        source.write_bytes(before+b'\n# source withdrawal negative\n')
        require_hold('actual_source_withdrawal','CURRENT_SOURCE_DIFFERS_FROM_MERGE:phase7_runtime_update.py')
    finally:source.write_bytes(before)
    provider=output/'RAW_PR_MERGED_READBACK.json';provider_raw=provider.read_bytes()
    try:
        changed=json.loads(provider_raw);changed['state']='OPEN';provider.write_bytes(encoded(changed))
        require_hold('historical_merged_provider_withdrawal','EXACT_OWN_MERGED_PR')
    finally:provider.write_bytes(provider_raw)
    assert consumer.current_closure(output,result['protected_readback'])==result['actual_legacy_closure']
    return out


def scientific_provider_negatives(fixture):
    certificate=Path(fixture.certificate['path']);original_certificate=certificate.read_bytes()
    base=json.loads(original_certificate)
    cloud=Path(base['bindings']['independent_cloud_receipt']['path']);original_cloud=cloud.read_bytes()
    cases=[
        ('wrong_comparator_provider',lambda c:c.update(provider='UNTRUSTED_TEST_PROVIDER'),
         'Comparator raw receipt contract failed'),
        ('missing_required_witness_export',lambda c:c['provider_response'].update(theoremNames=['bounded']),
         'missing a required theorem or nonvacuity witness export'),
        ('withdrawn_raw_verification_type',lambda c:c['provider_response'].update(type='verification-failed'),
         'does not establish dual-kernel acceptance'),
    ]
    observed=[]
    try:
        for name,change,cause in cases:
            value=json.loads(original_cloud);change(value)
            value['provider_response_sha256']=sha((json.dumps(value['provider_response'],sort_keys=True,separators=(',',':'))+'\n').encode())
            cloud.write_bytes(encoded(value))
            changed=copy.deepcopy(base)
            changed['bindings']['independent_cloud_receipt']['sha256']=sha(cloud.read_bytes())
            certificate.write_bytes(encoded(changed))
            with fixture.context(),sys.modules['nightly_manuscript_access'].frozen_sources(fixture.root)as load:
                result=load('certificate_inspection').inspect_certificate(certificate,fixture.root)
            reasons='; '.join(result['reasons'])
            assert result['valid']is False and cause in reasons,(name,reasons)
            assert 'hash-mismatched binding'not in reasons,(name,reasons)
            observed.append({'probe':name,'result':'HOLD','intended_cause':cause,'observed':reasons,
                'all_outer_provider_and_certificate_bindings_refreshed':True})
    finally:cloud.write_bytes(original_cloud);certificate.write_bytes(original_certificate)
    return observed


def main():
    from closed_data_loader import ClosedDataLoader
    loader=ClosedDataLoader(sys.argv[1]);sys.addaudithook(loader.audit)
    result=build_legacy_environment(loader.root/'canonical-root',loader)
    negatives=negative_probes(result)
    fixture=result['science_fixture'];builder=result['legacy_consumer_module'].load_builder()
    with builder.source_session(result['root'],result['base_pins']):
        note_path=fixture.base_note()
        with fixture.context(),sys.modules['nightly_manuscript_access'].frozen_sources(fixture.root)as load:
            note=load('phase7_audit_policy').require_note_publication_bound(note_path,fixture.root,fixture.authority)
        provider_negatives=scientific_provider_negatives(fixture)
        builder.verify_loaded(result['base_pins'],result['root'])
    assert note['status']=='PUBLICATION_BOUND',note.get('status')
    science_structure=fixture.structural_readback()
    report={
        'standard':'VRS-PRIVATE-W42-GENUINE-LEGACY99-PURPOSE130-DATA-CONTROL-1',
        'fixture_only':True,'production_admission':False,'source_review_verdict':False,
        'actual_legacy_current_closure_completed':True,'legacy_source_count':len(result['legacy_pins']),
        'purpose_source_count':len(result['base_pins']),'data_declarations':result['data_declarations'],
        'genuine_original_sourcefinder_and_old_default_science':{
            'status':note['status'],'note_path':str(note_path),
            'renderer_provider_and_authority_are_simulated':True,
            'all_science_validator_bodies_executed':True},
        'legacy_bindings':{k:result[k]for k in ('legacy_closure','legacy_scope','legacy_consumer','session_consumer')},
        'original_public_provenance':[dict((k,v)for k,v in row.items()if k!='raw')for row in result['source_provenance']],
        'negative_probes':negatives,
        'scientific_provider_negative_probes':provider_negatives,
        'closed_loader_source_body_equivalence':loader.receipts,
        'scientific_original_source_body_equivalence':{
            'source_rows':science_structure['source_rows'],
            'provider_original_selection_source':'Full exact original130 nightly_proof_track.py blob; not the earlier four-function subset',
            'platform_mapping':science_structure['platform_mapping'],
            'installed_access_copy_used_for_this_component':False,
            'modern_session_join_must_restore_exact_installed_access_and_use_declared_platform_DATA':True,
        },
        'actual_core_reads_execution_writes':0,'blocked_path_attempts':loader.blocked,
        'mocked_validate_current_closure_pass_or_digest':False,
        'session_contextvar_mints':0,'ambient_canonical_module_aliases':False,
        'full_modern_packaging_runtime_session_claim':False,
        'remaining_join':'Modern genuine runtime.session/current20+1/predecessors/nomination validation is owned by source-profile author; this packet supplies the real99/130 closure and original scientific DEFAULT control.',
    }
    out=Path(sys.argv[2]);out.write_bytes(encoded(report))
    print(json.dumps({'report':str(out),'sha256':sha(out.read_bytes()),'legacy99':99,'purpose130':130,
                      'old_default_status':note['status'],'negative_probes':len(negatives),
                      'core_open_attempts':len(loader.blocked)}))


if __name__=='__main__':main()
