"""Explicit default entry: fresh profile, PDF gate, science/ownership controller.

The default CLI is read-only. --go requires a hash-bound controller config and
uses its existing credential loader in memory. It never installs a profile.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

import packaging_runtime as runtime


def preflight(root, profile_binding, config_binding):
    root = Path(root).resolve(strict=True)
    _, _, config = runtime.object_at(root, config_binding)
    runtime.need(config.get('packaging_profile') == profile_binding, 'CONFIG_PROFILE_BINDING')
    with runtime.session(root, profile_binding) as profile:
        controller = importlib.import_module('digest_controller_v2')
        runtime.need(config.get('controller') == {
            'path': str(Path(controller.__file__).resolve(strict=True)),
            'sha256': hashlib.sha256(Path(controller.__file__).read_bytes()).hexdigest()}, 'CONFIG_CONTROLLER_BINDING')
        runtime.need(config.get('source_pins') == profile['source_pins']
                     and config.get('access_registry') == profile['access_registry'], 'CONFIG_COMPLETE_SOURCE_AND_ACCESS_BINDINGS')
        package = controller.config_value(root, config)
        digest = importlib.import_module('methods_digest_v2')
        manifest, publication = digest.require_publication_bound(package, root)
        scope = controller.obj(root, config['release_scope'])
        controller.require_cohort(scope, [n['run_id'] for n in manifest['notes']])
        runtime.need(manifest['release_week'] == scope['release_week'], 'EXACT_RELEASE_WEEK')
        files = controller.approved_inventory(package, manifest)
        gate = importlib.import_module('manuscript_pdf_gate')
        manuscripts = gate.require_local(package, [Path(row['path']) for row in files.values()])
        return {'status': 'ACTUAL_V2_DIGEST_DEFAULT_PREFLIGHT_PASS_NOT_EXECUTED',
                'profile': profile_binding, 'config': config_binding,
                'uploads': sorted(files), 'standalone_pdf_preflight': manuscripts,
                'certifies': False, 'ssot_writes': 0, 'zenodo_writes': 0}


def execute(root, profile_binding, config_binding, output, memory_token, *, rehearse=False, **kwargs):
    preflight(root, profile_binding, config_binding)
    with runtime.session(root, profile_binding):
        controller = importlib.import_module('digest_controller_v2')
        # The controller retains genuine own creation, causal native GET/PUBLISH,
        # complete journal accounting and exact note authority at every boundary.
        operation = controller.rehearse if rehearse else controller.execute
        result, terminal_binding = operation(config_binding, output, memory_token, **kwargs)
        runtime.need(result.get('source_session_exit_succeeded') is True
                     and result.get('status') == ('REHEARSED_DRAFT_DELETED' if rehearse else 'PUBLISHED_STRICT_READBACK_PASS')
                     and (not rehearse or result.get('published') is False), 'CONTROLLER_TERMINAL_READBACK')
    return result, terminal_binding


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--expected-profile-sha256', required=True)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--expected-config-sha256', required=True)
    p.add_argument('--go', action='store_true')
    p.add_argument('--output', type=Path)
    p.add_argument('--rehearse', action='store_true')
    args = p.parse_args()
    profile = {'path': str(args.profile.resolve(strict=True)), 'sha256': args.expected_profile_sha256}
    config = {'path': str(args.config.resolve(strict=True)), 'sha256': args.expected_config_sha256}
    token = ''
    try:
        runtime.need('VIRIDIS_ZENODO_API_BASE' not in os.environ, 'API_BASE_OVERRIDE_FORBIDDEN')
        runtime.need(not args.rehearse or args.go, 'REHEARSAL_REQUIRES_GO')
        checked = preflight(args.root, profile, config)
        if args.go:
            runtime.need(args.output is not None, 'CANONICAL_OUTPUT_REQUIRED')
            with runtime.session(args.root, profile):
                # This is the same existing loader used by the current publisher.
                # The token is never accepted via command-line or serialized.
                publisher = importlib.import_module('publish_dated_bundles_guarded')
                token = publisher.token()
            result, terminal = execute(args.root, profile, config, args.output, token, rehearse=args.rehearse)
            print(json.dumps({'controller_result': result, 'terminal': terminal}, sort_keys=True, indent=2))
        else:
            print(json.dumps(checked, sort_keys=True, indent=2))
        return 0
    except Exception as exc:
        detail = str(exc).replace(token, '***') if token else str(exc)
        print('HOLD_STANDALONE_PDF_RUNTIME: ' + detail, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
