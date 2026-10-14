#!/usr/bin/env python3
"""Methods Digest outer PDF guard and ordinary reviewed-successor dispatcher.

The same guard owns preflight and --go dispatch. Each child uses the complete
installed source/profile, PDF, science and publication-authorization gates.
The parent never imports scientific modules or consumes a credential.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import importlib.machinery

ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
INSTALLED = ROOT / '_ZENODO_DEPOSITS/standalone_pdf_runtime_v012'
PROFILE = INSTALLED / 'CURRENT_PACKAGING_PROFILE.json'
NOMINATION = INSTALLED / 'INSTALLATION_NOMINATION.json'
# Exact 19-module successor source set, fixed before source freeze and review.
SOURCE_HASHES = {'digest_controller_v2.py': 'faeba58a0a080e4b838536b0ac4f32fc9399497c4cc84d15ab9eaca0f83d9413', 'install_packaging_runtime.py': '319542b4f467d8c90f6dbfd9c664d4a3e723737aed6222a324b9c2622f94d753', 'invoke_digest_v2.py': '96480eca8c439be8d057802213fbc04281fc48d71b0d1b013c4b62343f932f87', 'manuscript_access_correction.py': 'c56b402f663a390ee442115cd7a3262ec513521d6191a117061436994657b563', 'manuscript_access_registry.py': '167d82b849a750edf2b0cfa92188931c9170db1a59c50eff4ba88ba48a5af2b8', 'manuscript_pdf_gate.py': '710478f0b7483928a82edd893338575bdf35c4772ce74727a866a5b784e37274', 'methods_digest_registration_v3.py': '1542b85fab50b686354075914ea461536db5da7b7bd3fee3b290eb7815d7e200', 'methods_digest_v2.py': 'e3e8b5be4b99a9991066f49a60630c2a8d63eafd3c09b9b0ed85b50748706f39', 'nightly_checkpoint_guarded.py': '298d2498901e437ac6a1ccc4e4a0841fb3d50244abd36309e0f9f533f179738e', 'owner_content_worker.py': '4368e184eda9e00acc19dab6b6df7a31525a73cfbb251683338da7d40899a140', 'packaging_catalog.py': '30a3e49d919fbf97b100a07f45222d86f8565443f019916758dde3748f43bc1b', 'packaging_nightly.py': '844472e62b2bf9d5a86a8076cdb52b7217d492ca7be621dda8aaea9cdb4ce663', 'packaging_nightly_coverage.py': 'f1df587d5966ae71d98d6282375f1d5fb4cb99e14ec0f77ce6d704b4c00fbdf6', 'packaging_nightly_intake.py': '2739cf071710f83a867176e5fa3171096fe0ac2f26a3805ff4bc3ad6622e7cd8', 'packaging_run_flow.py': 'cd4169d3cc2c3af02829d20ce363908a9edb914501f134dc341dd8d085567014', 'packaging_runtime.py': '4a4f49191996d21e97a1672428c81796f2c47a6d878246ec58ae8bf24b90e1cd', 'publish_dated_bundles_guarded.py': '85eb057f5eac7fd4d2218091cdda077030be67d35ea930a34b0fc3a3cfc0f4e3', 'publish_successor_wave_guarded.py': 'f9541bb40b91c479ddcb19c2dcd31104042a70305751100084581f9309e5b618', 'scientific_registration_worker.py': 'a6fe4f076470e2ae2e97c59a10b2c19c650aeb4059fb42570371aa3b3fba717b'}
SHARED_INPUT_NAME = 'stable_input_identity.py'
SHARED_INPUT_SHA256 = '7e6c204993f0ba65650c58ad50a71073d803522d31fa08b93b7ce35054fa5eda'
SHARED_INPUT_GIT_PATH = '00_lab_infrastructure/gates/standalone_pdf_release/common/stable_input_identity.py'


class GuardHold(ValueError):
    pass


def need(value, reason):
    if not value:
        raise GuardHold('HOLD_STANDALONE_MANUSCRIPT_PDF: ' + reason)


def identity(value):
    # Content identity excludes status-change time; mode is a separate
    # security observation and is still required to remain unchanged.
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns)


def read(path, expected=None):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts
         and path.is_relative_to(ROOT), 'canonical input path required')
    need(not any(p.is_symlink() for p in (path, *path.parents)),
         'regular input ancestry required')
    before = path.stat()
    need(stat.S_ISREG(before.st_mode), 'regular input file required')
    raw = path.read_bytes()
    readback = path.read_bytes()
    after = path.stat()
    digest = hashlib.sha256(raw).hexdigest()
    need(identity(before) == identity(after) and raw == readback
         and not any(p.is_symlink() for p in (path, *path.parents))
         and path.resolve(strict=True).is_relative_to(ROOT)
         and identity(path.stat()) == identity(after)
         and (expected is None or digest == expected), 'input hash or identity changed')
    content_identity = (digest, after.st_size, after.st_mtime_ns, after.st_ino, after.st_dev)
    return raw, digest, (content_identity, after.st_mode)


def context(config_path, config_sha):
    need(isinstance(SOURCE_HASHES, dict) and len(SOURCE_HASHES) == 19,
         'actual reviewed successor source set required')
    need(sys.pycache_prefix is None,'external current-code import cache prefix present')
    artifacts=[INSTALLED/'__pycache__']
    for name in sorted(SOURCE_HASHES):
        artifacts.extend(INSTALLED/(name[:-3]+suffix) for suffix in
            ('','.pyc','.pyo',*importlib.machinery.EXTENSION_SUFFIXES))
    need(all(not path.exists() and not path.is_symlink() for path in artifacts),
         'alternate current-code import artifact present')
    need(isinstance(config_sha, str) and re.fullmatch('[0-9a-f]{64}', config_sha),
         'exact configuration SHA-256 required')
    config_path = Path(config_path).absolute()
    raw, _, frame = read(config_path, config_sha)
    config = json.loads(raw)
    need(isinstance(config, dict) and config.get('canonical_root') == str(ROOT),
         'exact configuration canonical root required')
    nomination_raw, _, nomination_frame = read(NOMINATION)
    nomination = json.loads(nomination_raw)
    need(isinstance(nomination, dict)
         and nomination.get('standard') == 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-12'
         and nomination.get('status') == 'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING',
         'exact installed successor nomination required')
    profile_binding = nomination.get('profile')
    need(isinstance(profile_binding, dict) and set(profile_binding) == {'path', 'sha256'}
         and profile_binding['path'] == str(PROFILE)
         and re.fullmatch('[0-9a-f]{64}', str(profile_binding['sha256']))
         and config.get('packaging_profile') == profile_binding,
         'configuration must nominate the installed successor profile')
    profile_raw, _, profile_frame = read(PROFILE, profile_binding['sha256'])
    profile = json.loads(profile_raw)
    need(isinstance(profile, dict)
         and profile.get('standard') == 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-12'
         and profile.get('status') == 'INSTALLED_EXACT_ADDITIVE_SOURCE_READBACK_PASS'
         and profile.get('canonical_root') == str(ROOT), 'exact installed successor profile required')
    modules = profile.get('modules')
    need(isinstance(modules, list) and len(modules) == 19
         and all(isinstance(row, dict) for row in modules)
         and {row.get('name') for row in modules} == set(SOURCE_HASHES),
         'complete exact successor source table required')
    sources = {}
    for row in modules:
        name = row['name']
        target = INSTALLED / name
        need(row.get('path') == str(target) and row.get('sha256') == SOURCE_HASHES[name],
             'installed source differs from reviewed successor: ' + name)
        sources[name] = read(target, SOURCE_HASHES[name])
    shared_path = INSTALLED / 'common' / SHARED_INPUT_NAME
    expected_shared = [{'name': SHARED_INPUT_NAME, 'path': str(shared_path),
                        'sha256': SHARED_INPUT_SHA256, 'git_path': SHARED_INPUT_GIT_PATH}]
    need(profile.get('shared_dependencies') == expected_shared,
         'exact reviewed shared source dependency required')
    sources[SHARED_INPUT_NAME] = read(shared_path, SHARED_INPUT_SHA256)
    return {'config_path': str(config_path), 'config_raw': raw, 'config_frame': frame,
            'nomination_raw': nomination_raw, 'nomination_frame': nomination_frame,
            'profile_raw': profile_raw, 'profile_frame': profile_frame,
            'profile_binding': profile_binding, 'sources': sources}


def child_command(checked, config_sha, *, go=False, output=None):
    command = [sys.executable, '-B', str(INSTALLED / 'invoke_digest_v2.py'),
               '--root', str(ROOT), '--profile', str(PROFILE),
               '--expected-profile-sha256', checked['profile_binding']['sha256'],
               '--config', checked['config_path'], '--expected-config-sha256', config_sha]
    if go:
        need(output is not None, 'private controller output required for --go')
        path = Path(output).absolute()
        need('..' not in path.parts and path.is_relative_to(ROOT / 'reports')
             and not any(p.is_symlink() for p in (path, *path.parents)),
             'private controller output must remain in canonical reports')
        command.extend(['--go', '--output', str(path)])
    return command


def run_child(checked, config_sha, *, go=False, output=None):
    command = child_command(checked, config_sha, go=go, output=output)
    completed = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL)
    need(context(checked['config_path'], config_sha) == checked,
         'source, profile or configuration changed during child execution')
    return completed.returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--expected-config-sha256', required=True)
    parser.add_argument('--go', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        # Validate output before the first child. This guard never chooses a
        # controller or executes caller-provided source from a configuration.
        checked = context(args.config, args.expected_config_sha256)
        if args.go:
            child_command(checked, args.expected_config_sha256, go=True, output=args.output)
        result = run_child(checked, args.expected_config_sha256)
        if result or not args.go:
            return result
        # A new ordinary child freshly repeats every downstream gate. A
        # successful preflight cannot supply a cached scientific admission.
        checked = context(args.config, args.expected_config_sha256)
        return run_child(checked, args.expected_config_sha256, go=True, output=args.output)
    except (GuardHold, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
