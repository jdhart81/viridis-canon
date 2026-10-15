"""Nominated additive checkpoint/coverage/intake entry over preserved science.

The source profile is consumed before any historical or candidate operational
module is imported. All registry reads use explicit real owner observations.
No generation, proof execution, certificate issuance or Zenodo write occurs.
Exact missing legacy transient source recovery is separately receipted.
"""
from __future__ import annotations
import os
import argparse
import datetime as dt
import importlib
import importlib.machinery
import json
from pathlib import Path
import sys
import uuid

def _current_namespace_artifacts():
    if sys.pycache_prefix is not None:raise ValueError('CURRENT_NIGHTLY_NAMESPACE_IMPORT_ARTIFACT:EXTERNAL_CACHE_PREFIX')
    directory=Path(__file__).absolute().parent
    names={'packaging_runtime','invoke_digest_v2','digest_controller_v2','methods_digest_v2',
        'methods_digest_registration_v3','manuscript_access_registry','manuscript_access_correction',
        'manuscript_pdf_gate','publish_dated_bundles_guarded','publish_successor_wave_guarded',
        'packaging_catalog','install_packaging_runtime','packaging_nightly','nightly_checkpoint_guarded',
        'packaging_run_flow','packaging_nightly_coverage','packaging_nightly_intake',
        'scientific_registration_worker','owner_content_worker'}
    probes=[directory/'__pycache__']
    for stem in sorted(names):
        probes.extend(directory/(stem+suffix)for suffix in('', '.pyc','.pyo',*importlib.machinery.EXTENSION_SUFFIXES))
    for path in probes:
        if path.exists()or path.is_symlink():raise ValueError('CURRENT_NIGHTLY_NAMESPACE_IMPORT_ARTIFACT:'+str(path))


if __name__=='__main__':
    _current_namespace_artifacts()

import packaging_runtime as runtime

if not os.environ.get("VIRIDIS_CORE_ROOT"):
    raise RuntimeError("HOLD_CORE_ROOT_REQUIRED: set VIRIDIS_CORE_ROOT explicitly")
ROOT = Path(os.environ["VIRIDIS_CORE_ROOT"])


def _main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    runtime.need(args and args[0] in {'checkpoint','cycle','health','intake'}, 'CLOSED_NIGHTLY_ROUTE')
    mode, rest = args[0], args[1:]
    root = ROOT.resolve(strict=True)
    profile = runtime.nominated_binding(root)
    health_summary=None;health_exit=None
    with runtime.session(root, profile)as source_admission:
        # Begin only records the unchanged foundry observation; it does not
        # need public registry observations or a network transport.
        if mode == 'checkpoint' and '--begin' in rest:
            module = importlib.import_module('nightly_checkpoint_guarded')
            before = sys.argv
            try:
                sys.argv = [str(Path(module.__file__)), *rest]
                return module.main()
            finally:
                sys.argv = before
        catalog = importlib.import_module('packaging_catalog')
        # IPC/process libraries import before the active original-read observer.
        science_worker = importlib.import_module('scientific_registration_worker') if mode == 'health' else None
        publisher = importlib.import_module('publish_dated_bundles_guarded')
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
        output = root/'reports/verification-coverage'/stamp/('packaging-owner-'+uuid.uuid4().hex)
        context = catalog.owner_context(root, profile, publisher.token(), output)
        with catalog.operation_scope(root, profile, context):
            if mode == 'health':
                parser = argparse.ArgumentParser(description='Fresh full-population health; network GETs only, declared startup source recovery')
                parser.parse_args(rest)
                canonical = root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
                previous = json.loads(canonical.read_bytes())
                catalog.prime_scientific_data(root, root/'RESEARCH_PIPELINE_v2/lean_certificates', previous,
                                              profile, registry_context=context)
                batch = science_worker.ScienceBatch(root, profile, context, previous,
                                                    catalog.scientific_data(root).scan_data, output)
                complete = False
                try:
                    batch.prepare()
                    prepare_owner = getattr(context, 'prepare_owner_prefetch', None)
                    runtime.need(callable(prepare_owner), 'REVIEWED_COMPLETE_OWNER_PREFETCH_REQUIRED')
                    prepare_owner()
                    with batch.stage('build'):
                        ledger = catalog.build(root, root/'RESEARCH_PIPELINE_v2/lean_certificates', previous,
                                               profile, registry_context=context)
                    runtime.need(ledger.get('enforcement_activation') == previous.get('enforcement_activation')
                                 and ledger.get('premise_declaration_cutover_run') == previous.get('premise_declaration_cutover_run'),
                                 'HEALTH_ORIGINAL_ACTIVATION')
                    coverage = importlib.import_module('packaging_nightly_coverage')
                    with batch.stage('activation_current_preserve'):
                        activation = coverage.load_enforcement_activation(root)
                    with batch.stage('doi'):
                        audit = catalog.augment_audit(root, ledger, profile, registry_context=context)
                    labels = catalog.public_label_readback(root, audit, profile, registry_context=context)
                    complete = True
                finally:
                    batch.close(complete=complete)
                result = {'status':'FRESH_DEFAULT_FULL_POPULATION_HEALTH_READBACK',
                          'startup_source_admission':source_admission,
                          'live_original_scientific_calls':batch.summary(),
                          'ledger':ledger, 'doi_audit':audit, 'labels':labels,
                          'enforcement_activation':activation['binding'], 'observation_timing':context.observation_timing(), 'certifies':False,
                          'ssot_writes':0, 'zenodo_writes':0}
                catalog.observation_guard(context)
                path = output/'DEFAULT_HEALTH_READBACK.json'
                with path.open('x') as stream:
                    json.dump(result, stream, sort_keys=True, indent=2, ensure_ascii=False);stream.write('\n')
                failed = (ledger.get('publication_registration_enforcement_acceptable') is not True
                          or bool(ledger.get('errors')) or bool(ledger.get('mirror_drift'))
                          or labels['counts']['unavailable'] or labels['counts']['label_disagreements'])
                health_summary={'status':'HOLD' if failed else 'FRESH_DEFAULT_FULL_POPULATION_READBACK_PASS',
                                'receipt':str(path),'sha256':runtime.sha(path.read_bytes()),
                                'public_counts':labels['counts'],'certifies':False,
                                'ssot_writes':0,'zenodo_writes':0,
                                'startup_transient_source_writes':(source_admission or{}).get('transient_source_readback',{}).get('transient_source_writes',0)}
                health_exit=2 if failed else 0
            else:
                module = importlib.import_module({'checkpoint':'nightly_checkpoint_guarded',
                                                 'cycle':'packaging_run_flow',
                                                 'intake':'packaging_nightly_intake'}[mode])
                before = sys.argv
                try:
                    sys.argv = [str(Path(module.__file__)), *rest]
                    return module.main()
                finally:
                    sys.argv = before
    # No successful health summary escapes before owner/input retention and
    # the fresh source/helper exit validation have both completed.
    print(json.dumps(health_summary,sort_keys=True))
    return health_exit


def main(argv=None):
    args=list(sys.argv[1:]if argv is None else argv)
    if args and args[0]=='health':
        # The tightened internal2940 alarm leaves60 seconds for ordinary
        # worker and original source cleanup inside the unchanged outer3000.
        # Its BaseException abort cannot be swallowed as a scientific HOLD by
        # the original fold. Other operational entry semantics are unchanged.
        with runtime.health_supervision_scope():
            return _main(args)
    return _main(args)


if __name__ == '__main__':
    raise SystemExit(main())
