"""Nominated additive checkpoint/coverage/intake entry over preserved science.

The source profile is consumed before any historical or candidate operational
module is imported. All registry reads use explicit real owner observations.
No generation, proof execution, certificate issuance or Zenodo write occurs.
"""
from __future__ import annotations
import argparse
import datetime as dt
import importlib
import json
from pathlib import Path
import sys
import uuid

import packaging_runtime as runtime

ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    runtime.need(args and args[0] in {'checkpoint','cycle','health','intake'}, 'CLOSED_NIGHTLY_ROUTE')
    mode, rest = args[0], args[1:]
    root = ROOT.resolve(strict=True)
    profile = runtime.nominated_binding(root)
    with runtime.session(root, profile):
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
        publisher = importlib.import_module('publish_dated_bundles_guarded')
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
        output = root/'reports/verification-coverage'/stamp/('packaging-owner-'+uuid.uuid4().hex)
        context = catalog.owner_context(root, profile, publisher.token(), output)
        with catalog.operation_scope(root, profile, context):
            if mode == 'health':
                parser = argparse.ArgumentParser(description='Fresh full-population packaging/activation health; GET-only')
                parser.parse_args(rest)
                canonical = root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
                previous = json.loads(canonical.read_bytes())
                ledger = catalog.build(root, root/'RESEARCH_PIPELINE_v2/lean_certificates', previous,
                                       profile, registry_context=context)
                runtime.need(ledger.get('enforcement_activation') == previous.get('enforcement_activation')
                             and ledger.get('premise_declaration_cutover_run') == previous.get('premise_declaration_cutover_run'),
                             'HEALTH_ORIGINAL_ACTIVATION')
                coverage = importlib.import_module('packaging_nightly_coverage')
                activation = coverage.load_enforcement_activation(root)
                audit = catalog.augment_audit(root, ledger, profile, registry_context=context)
                labels = catalog.public_label_readback(root, audit, profile, registry_context=context)
                result = {'status':'FRESH_DEFAULT_FULL_POPULATION_HEALTH_READBACK',
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
                print(json.dumps({'status':'HOLD' if failed else 'FRESH_DEFAULT_FULL_POPULATION_READBACK_PASS',
                                  'receipt':str(path), 'sha256':runtime.sha(path.read_bytes()),
                                  'public_counts':labels['counts'], 'certifies':False,
                                  'ssot_writes':0, 'zenodo_writes':0}, sort_keys=True))
                return 2 if failed else 0
            module = importlib.import_module({'checkpoint':'nightly_checkpoint_guarded',
                                             'cycle':'packaging_run_flow',
                                             'intake':'packaging_nightly_intake'}[mode])
            before = sys.argv
            try:
                sys.argv = [str(Path(module.__file__)), *rest]
                return module.main()
            finally:
                sys.argv = before


if __name__ == '__main__':
    raise SystemExit(main())
