"""Inspect existing issuer evidence using the canonical pipeline's validators.

This module performs no transport, elaboration, issuance, or certificate repair.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

PINNED_TOOLCHAIN = 'leanprover/lean4:v4.28.0'
PINNED_MATHLIB = '8f9d9cff6bd728b17a24e163c9402775d9e6a365'


def pipeline_modules(root):
    pipeline = root / 'RESEARCH_PIPELINE_v2'
    if str(pipeline) not in sys.path:
        sys.path.insert(0, str(pipeline))
    # Load exactly the canonical modules, never use a snapshot copy.
    modules = []
    for name in ('nightly_proof_track', 'issue_lean_zero_sorry_certificate'):
        spec = importlib.util.spec_from_file_location('coverage_' + name, pipeline / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    return modules


def resolve_binding(binding, root):
    if not isinstance(binding, dict) or not isinstance(binding.get('path'), str):
        raise ValueError('missing path/hash binding')
    path = Path(binding['path'])
    choices = [path] if path.is_absolute() else [root / path, root / 'RESEARCH_PIPELINE_v2' / path]
    if any(not p.resolve().is_relative_to(root.resolve()) for p in choices):
        raise ValueError('certificate binding outside mirror/certification root: ' + binding['path'])
    matching = [p.resolve() for p in choices if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == binding.get('sha256')]
    if not matching:
        raise ValueError('missing/hash-mismatched binding: ' + binding['path'])
    if len(set(matching)) != 1:
        raise ValueError('ambiguous binding base: ' + binding['path'])
    return matching[0]


def inspect_certificate(path, tree_root):
    root = Path(tree_root).resolve()
    path = Path(path).resolve()
    result = {'path': str(path), 'valid': False, 'reasons': [], 'bindings': [],
              'certified_theorems': [], 'nonvacuity': [], 'sealed_paper_inputs': {}}
    try:
        if not path.is_relative_to(root):
            raise ValueError("certificate outside mirror/certification root")
        cert = json.loads(path.read_text())
        def check_locations(value):
            if isinstance(value, dict):
                if "path" in value:
                    resolve_binding(value, root)
                else:
                    for child in value.values():
                        check_locations(child)
        check_locations(cert.get("bindings", {}))
        proof_track, issuer = pipeline_modules(root)
        result.update(run_id=cert.get('run_id'), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), recorded_certificate_current=False)
        result['candidate_sha256'] = cert.get('bindings', {}).get('candidate_proof', {}).get('sha256')
        if not re.fullmatch(r'Run-\d+', str(cert.get('run_id', ''))):
            raise ValueError('invalid run identity')
        # Use the existing control-plane acceptance path, including its recorded
        # relative-path convention and historical sealed-input contracts.
        accepted = proof_track.current_certificate(root, cert['run_id'])
        if accepted and accepted[0].resolve() == path:
            result['recorded_certificate_current'] = True
        else:
            # Deposits can contain immutable upgraded certificates while the main
            # run store retains the original. Consume their own exact bindings,
            # never inherit certification by run ID or copied title.
            if cert.get('standard') != 'VRS-LEAN-ZERO-SORRY-CERTIFICATE-1' or cert.get('status') != 'LEAN_ZERO_SORRY_CERTIFIED':
                raise ValueError('existing certificate standard/status rejected')
            if not path.is_relative_to(root):
                raise ValueError('certificate outside canonical tree')
        for name in ('allowed_axioms_only', 'zero_sorries_or_admits', 'nonvacuity_witnesses', 'frozen_statement_and_candidate_hash_bound', 'independent_cloud_kernel_verification', 'comparator_lean_kernel', 'comparator_nanoda_kernel', 'comparator_statement_identity'):
            if cert.get('gates', {}).get(name) is not True:
                raise ValueError('certificate missing required gate: ' + name)
        if cert.get('gates', {}).get('local_lean_execution') is not False:
            raise ValueError('certificate no-local-Lean invariant missing')
        bindings = cert['bindings']
        for name in ('request', 'independent_cloud_receipt', 'candidate_proof', 'formal_statement'):
            if not proof_track.binding_is_current(bindings.get(name), root):
                raise ValueError('existing binding_is_current consumer rejected: ' + name)
        if not bindings.get('sealed_paper_inputs'):
            raise ValueError('missing sealed paper bindings')
        def visit(value, label):
            if not isinstance(value, dict):
                return
            if 'path' in value or 'sha256' in value:
                bound = resolve_binding(value, root)
                result['bindings'].append({'label': label, 'recorded_path': value['path'],
                    'resolved_path': str(bound), 'sha256': value['sha256'], 'matches': True})
            else:
                for key, child in value.items():
                    visit(child, label + '.' + key)
        visit(bindings, 'bindings')
        request_path = resolve_binding(bindings['request'], root)
        cloud_path = resolve_binding(bindings['independent_cloud_receipt'], root)
        request, cloud = json.loads(request_path.read_text()), json.loads(cloud_path.read_text())
        # Hash-valid files must belong to this same immutable envelope. A clean
        # unrelated candidate cannot inherit a genuine cloud receipt.
        for label, cloud_key in (('request', 'request'), ('candidate_proof', 'candidate'), ('formal_statement', 'formal_statement')):
            if bindings[label].get('sha256') != cloud.get(cloud_key, {}).get('sha256'):
                raise ValueError('certificate/cloud hash binding mismatch: ' + label)
            if resolve_binding(bindings[label], root) != resolve_binding(cloud.get(cloud_key), root):
                raise ValueError('certificate/cloud path binding mismatch: ' + label)
        normalized = re.fullmatch(r'Run-(\d+)(?:[_-].*)?', str(request.get('source_run', '')))
        if normalized is None or f'Run-{int(normalized[1]):03d}' != cert['run_id']:
            raise ValueError('certificate/request source run mismatch')
        if cert.get('candidate_id') != request.get('candidate_id') or cloud.get('contract', {}).get('candidate_id') != request.get('candidate_id'):
            raise ValueError('certificate/request/cloud candidate identity mismatch')
        if cloud.get('contract', {}).get('expected_theorem_names') != request.get('expected_theorem_names'):
            raise ValueError('cloud/request theorem contract mismatch')
        inputs = request.get('input_sha256')
        if not isinstance(inputs, dict):
            raise ValueError('request input hash map missing')
        for label in ('candidate_proof', 'formal_statement'):
            proof_path = resolve_binding(bindings[label], root)
            if inputs.get(proof_path.name) != bindings[label]['sha256']:
                raise ValueError('request/certificate source hash mismatch: ' + label)
        sealed_names = {'SEALED_paper.pdf','SEALED_paper.tex','SEALED_CLAIM_INVENTORY.json','SEALED_RUN_MANIFEST.json'}
        expected_sealed = {name: value for name, value in inputs.items() if name in sealed_names}
        sealed = bindings['sealed_paper_inputs']
        if set(sealed) != set(expected_sealed) or not {'SEALED_paper.pdf','SEALED_paper.tex'}.issubset(sealed):
            raise ValueError('certificate/request sealed input contract mismatch')
        for name, value in sealed.items():
            if value.get('sha256') != expected_sealed[name] or resolve_binding(value, root) != (request_path.parent / name).resolve():
                raise ValueError('certificate/request sealed input mismatch: ' + name)
        if request.get('toolchain') != PINNED_TOOLCHAIN or request.get('mathlib_rev') != PINNED_MATHLIB:
            raise ValueError('toolchain/Mathlib pin mismatch')
        if cert.get('verification_standard') != 'VRS-COMPARATOR-DUAL-KERNEL-1':
            raise ValueError('Comparator verifier-of-record evidence missing')
        if (cloud.get('provider') != 'VIRIDIS_COMPARATOR_CLOUD' or cloud.get('status') != 'VERIFIED'
                or cloud.get('project') != 'viridis-lean-4.28'
                or cloud.get('contract', {}).get('permitted_axioms') != issuer.PERMITTED_AXIOMS
                or cloud.get('local_lean_execution') is not False
                or any(cloud.get('checks', {}).get(k) is not True for k in issuer.COMPARATOR_CHECKS if k != 'targeted_export_complete')
                or cloud.get('checks', {}).get('targeted_export_complete') is False):
            raise ValueError('Comparator raw receipt contract failed')
        issuer.validate_comparator_witness_evidence(request, cloud)
        result['targeted_export_evidence'] = 'RAW_RESPONSE_VALIDATED_BY_UNCHANGED_ISSUER_HELPER'
        result['legacy_targeted_export_summary_missing'] = 'targeted_export_complete' not in cloud.get('checks', {})
        # Historical certificates are consumed under their original contract;
        # new Track B requests must use all four sealed inputs (v2.4).
        result.update(valid=True, candidate_sha256=bindings['candidate_proof']['sha256'],
            candidate_path=str(resolve_binding(bindings['candidate_proof'], root)),
            certified_theorems=request['expected_theorem_names'], nonvacuity=request['nonvacuity_obligations'],
            sealed_paper_inputs=bindings['sealed_paper_inputs'], source_run=request.get('source_run'),
            sealed_input_contract='CURRENT_FOUR_INPUTS' if len(bindings['sealed_paper_inputs']) == 4 else 'HISTORICAL_ISSUED_CONTRACT')
    except Exception as exc:
        result['reasons'].append(type(exc).__name__ + ': ' + str(exc))
    return result
