#!/usr/bin/env python3
"""Cause-specific A2 artifact-label mutants in an isolated copied checkout.

Numeric unittest failures are required. Import/fixture/runtime errors never
count as a kill; each named test must first pass against unmodified source.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE=Path(__file__).resolve().parents[1]
RUNTIME=Path('00_lab_infrastructure/gates/standalone_pdf_release/runtime')
ACCESS=RUNTIME/'nightly_manuscript_access.py'
DIGEST=RUNTIME/'methods_digest_v2.py'
REGISTRAR=RUNTIME/'methods_digest_registration_v3.py'
TESTS=RUNTIME/'tests'
MUTANTS=[
    ('A17_no_certified_artifact_registration',REGISTRAR,[(" if labelled:\n  group.update(status='UNCERTIFIED'", " if False:\n  group.update(status='UNCERTIFIED'")],'a2_labelled_artifact_envelope_test.LabelledRegistrationOutputTests.test_current_artifact_rows_are_never_certified_or_bare_certificate_bound',[]),
    ('A18_no_certified_artifact_evaluation',REGISTRAR,[("  if expected.get('artifact_label')==d.ARTIFACT_LABEL:", '  if False:')],'a2_labelled_artifact_envelope_test.LabelledRegistrationOutputTests.test_delivery_integrity_pass_never_promotes_group_or_note_pdf',[]),
    ('A19_statement_evidence_preservation',REGISTRAR,[("'note_ids','certifies','artifact_label','statement_certificate_evidence'):", "'note_ids','certifies','artifact_label'):")],'a2_labelled_artifact_envelope_test.LabelledRegistrationOutputTests.test_statement_evidence_drift_is_held_by_preserve_and_evaluate',[]),
    ('A20_truthful_public_label',REGISTRAR,[("  if labelled:\n   result.update(public_verification_status='UNCERTIFIED'", "  if False:\n   result.update(public_verification_status='UNCERTIFIED'")],'a2_labelled_artifact_envelope_test.LabelledRegistrationOutputTests.test_public_label_output_names_uncertified_artifact_and_keeps_scoped_evidence',[]),
    ('A21_no_bare_artifact_certificate',REGISTRAR,[("result[-1].update(certificate=None,artifact_label=", "result[-1].update(artifact_label=")],'a2_labelled_artifact_envelope_test.LabelledRegistrationOutputTests.test_child_receipt_keeps_issuer_only_under_exact_statement_evidence',[]),
    ('A16_no_missing_glyph_waiver',ACCESS,[("need(b'Missing character:'not in raw and b'could not represent character'not in raw,","need(True,")],'a2_labelled_native_render_test.LabelledNativeRenderTests.test_missing_glyph_in_each_retained_channel_is_rejected_even_when_child_succeeds',[]),
    ('A01_exact_approved_text',ACCESS,[("LABEL_TEXT = 'UNCERTIFIED — no issuer-produced", "LABEL_TEXT = 'CERTIFIED — no issuer-produced")],'a2_artifact_label_tokens_test.ArtifactLabelTokenTests.test_exact_approved_unicode_label_is_not_reworded',[]),
    ('A02_historical_N1_unchanged',ACCESS,[('    if historical:\n        require_self_contained_original(original)', '    if False:\n        require_self_contained_original(original)'), ('    if historical:\n        require_self_contained_original(result)', '    if False:\n        require_self_contained_original(result)')],'a2_artifact_label_tokens_test.ArtifactLabelTokenTests.test_historical_file_readers_macro_aliases_and_cache_escape_hold',[]),
    ('A03_unique_active_title',ACCESS,[('and len(titles)==1 and documents[0][2]', 'and len(titles)>=1 and documents[0][2]')],'a2_artifact_label_tokens_test.ArtifactLabelTokenTests.test_duplicate_active_titles_hold_in_both_modes',[]),
    ('A04_binary_before_spawn',ACCESS,[('need(d.digest(binary_before)==policy.RENDERER_SHA and d.digest(manifest_raw)==policy.RENDERER_CACHE_SHA,', 'need(True,')],'a2_labelled_native_render_test.LabelledNativeRenderTests.test_changed_binary_is_rejected_before_any_spawn',[]),
    ('A05_cache_before_spawn',ACCESS,[("expected=cache_snapshot(cache);need(expected==manifest['files'],'all pinned renderer assets before execution')", "expected=cache_snapshot(cache);need(True,'all pinned renderer assets before execution')")],'a2_labelled_native_render_test.LabelledNativeRenderTests.test_changed_cache_asset_is_rejected_before_any_spawn',[]),
    ('A06_afterimage_cache_source_closure',ACCESS,[("'cache_and_binary_exact_after':closure,", "'cache_and_binary_exact_after':True,"), ("need(process.returncode==0 and closure,'native renderer failed or input closure changed')", "need(process.returncode==0,'native renderer failed or input closure changed')")],'a2_labelled_native_render_test.LabelledNativeRenderTests.test_cache_drift_after_spawn_cannot_clear_provenance',[]),
    ('A07_parent_exit_child_group_kill',ACCESS,[("        (os.killpg if reservation['isolated'] else os.kill)(reservation['pid'], sig)", "        if sig != signal.SIGKILL: (os.killpg if reservation['isolated'] else os.kill)(reservation['pid'], sig)  # MUTANT omits final descendant kill")],'a2_labelled_native_render_test.LabelledNativeRenderTests.test_group_cleanup_kills_owned_descendant_after_parent_exit',[]),
    ('A08_separate_later_artifact_review',ACCESS,[("need(review_invocation not in {previous['current_invocation'],previous['source_selection_invocation']},", 'need(True,'), ("and pb['review_invocation']not in{prior_review['current_invocation'],prior_review['source_selection_invocation']},", 'and True,')],'a2_labelled_artifact_envelope_test.LabelledArtifactEnvelopeTests.test_original_review_invocation_cannot_be_reused',[]),
    ('A09_binding_has_no_science_authority',ACCESS,[("and pb['certifies']is False and pb['publication_authorized']is False,'exact distinct labelled artifact binding')", "and True,'exact distinct labelled artifact binding')")],'a2_labelled_artifact_envelope_test.LabelledArtifactEnvelopeTests.test_binding_cannot_claim_scientific_or_publication_authority',[]),
    ('A10_fresh_exact_labelled_manifest',ACCESS,[("need(actual==manifest,'fresh exact labelled artifact identity')", "need(True,'fresh exact labelled artifact identity')")],'a2_labelled_artifact_envelope_test.LabelledArtifactEnvelopeTests.test_extra_claim_or_certified_role_cannot_clear',[]),
    ('A11_actual_later_binding_chronology',ACCESS,[("need(max(load('nightly_minimal_policy').time(base_pb['issued_at_utc']),", "need(True or max(load('nightly_minimal_policy').time(base_pb['issued_at_utc']),")],'a2_labelled_artifact_envelope_test.LabelledArtifactEnvelopeTests.test_future_or_naive_binding_and_predated_render_hold',[]),
    ('A12_no_ambient_wrapper_provenance',DIGEST,[('current_access=_current_access(root)', "current_access=importlib.import_module('nightly_manuscript_access')")],'a2_labelled_native_render_test.LabelledNativeRenderTests.test_ambient_access_module_cannot_supply_wrapper_provenance',[]),
    ('A13_new_write_requires_labelled_format',DIGEST,[("if manifest.get('standard')!=LABELLED_STANDARD:raise DigestHold('new publication requires the labelled artifact envelope')", 'return  # MUTANT permits old unlabelled publication')],'a2_labelled_native_render_test.LabelledPublicationFormatTests.test_new_publication_rejects_archival_or_unlabelled_digest',[]),
    ('A14_W42_only_wording_authority',DIGEST,[("if week!='2026-W42':raise DigestHold('artifact wording authority is scoped to 2026-W42')", "if False:raise DigestHold('artifact wording authority is scoped to 2026-W42')")],'a2_labelled_native_render_test.LabelledPublicationFormatTests.test_approved_wording_does_not_silently_extend_to_w43_or_mixed_notes',[]),
    ('A15_labelled_historical_standalone',DIGEST,[("if 'manuscripts'in note:", 'if False:')],'a2_labelled_native_render_test.LabelledPublicationFormatTests.test_labelled_top_copy_selection_keeps_both_exact_admitted_names',[]),
]

HARNESS=r'''import json,sys,unittest
sys.dont_write_bytecode=True
sys.path[:0]=[sys.argv[1]]
suite=unittest.defaultTestLoader.loadTestsFromName(sys.argv[2])
r=unittest.TextTestRunner(verbosity=2).run(suite)
print('VRS_NUMERIC_UNITTEST_RESULT='+json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),'assertion_failures':[text for _,text in r.failures]}))
sys.exit(0 if r.wasSuccessful()else 1)
'''

def sha(raw):return hashlib.sha256(raw).hexdigest()
def run(root,test,timeout):
    p=subprocess.run([sys.executable,'-B','-c',HARNESS,str(root/TESTS),test],cwd=root,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
    lines=[x.split('=',1)[1]for x in p.stdout.splitlines()if x.startswith('VRS_NUMERIC_UNITTEST_RESULT=')]
    return p,json.loads(lines[-1])if lines else None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--timeout',type=int,default=120);parser.add_argument('--only',action='append')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False);results=[]
    with tempfile.TemporaryDirectory(prefix='a2-artifact-mutants-')as tmp:
        root=Path(tmp)/'checkout';shutil.copytree(BASE,root,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc','*.pyo'))
        for name,path,replacements,test,extra in MUTANTS:
            if args.only and name not in args.only:continue
            source=(root/path).read_text();control,control_result=run(root,test,args.timeout)
            (args.output/(name+'-control.log')).write_text(control.stdout)
            if control.returncode!=0 or control_result is None or control_result['tests']<1 or control_result['failures']or control_result['errors']:
                results.append({'name':name,'status':'INVALID_CONTROL','test':test,'control':control_result});continue
            mutated=source
            for before,after in replacements+extra:
                expected=1
                if mutated.count(before)!=expected:raise ValueError('unique closed mutation sites required: '+name+' '+repr(before))
                mutated=mutated.replace(before,after)
            (root/path).write_text(mutated)
            try:p,result=run(root,test,args.timeout)
            finally:(root/path).write_text(source)
            (args.output/(name+'-mutant.log')).write_text(p.stdout)
            killed=result is not None and result['tests']>=1 and result['failures']>=1 and result['errors']==0
            results.append({'name':name,'status':'KILLED_ASSERTION'if killed else'INVALID_ERROR'if result is None or result['errors']else'SURVIVED',
                'test':test,'source':str(path),'source_before_sha256':sha(source.encode()),'source_mutant_sha256':sha(mutated.encode()),
                'control':control_result,'mutant':result,'control_log_sha256':sha(control.stdout.encode()),'mutant_log_sha256':sha(p.stdout.encode())})
            print(name,results[-1]['status'],flush=True)
    summary={'standard':'VRS-A2-ARTIFACT-CAUSE-SPECIFIC-MUTATIONS-1','python':sys.version,'results':results,
        'killed':sum(r['status']=='KILLED_ASSERTION'for r in results),'total':len(results),
        'errors_credited':0,'all_killed':all(r['status']=='KILLED_ASSERTION'for r in results)}
    (args.output/'RESULT.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    return 0 if summary['all_killed']else 1

if __name__=='__main__':raise SystemExit(main())
