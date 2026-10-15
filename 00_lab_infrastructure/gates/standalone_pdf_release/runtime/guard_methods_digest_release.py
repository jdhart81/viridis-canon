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

ROOT = Path(os.environ.get('VIRIDIS_CORE_ROOT', str(Path(__file__).resolve().parent.parent.parent)))
INSTALLED = ROOT / '_ZENODO_DEPOSITS/standalone_pdf_runtime'
PROFILE = INSTALLED / 'CURRENT_PACKAGING_PROFILE.json'
NOMINATION = INSTALLED / 'INSTALLATION_NOMINATION.json'
# Exact 19-module successor source set, fixed before source freeze and review.
SOURCE_HASHES = {
    'digest_controller_v2.py':
        # SHA-256 of reviewed source bytes; not a credential
        '331105b8f557cecd50b4824da5ba07b77ae6aec62efcbebdef712334c1a72282',
    'install_packaging_runtime.py':
        # SHA-256 of reviewed source bytes; not a credential
        '96088caa1f784d86f3768f71a519d926eb2be2a0f2ccd56467ee5a5d30469e68',
    'invoke_digest_v2.py':
        # SHA-256 of reviewed source bytes; not a credential
        '932afcb894fb8581ee9718ec1894d3ca38520efa3fbcbe34e34e706226befaa3',
    'manuscript_access_correction.py':
        # SHA-256 of reviewed source bytes; not a credential
        'c56b402f663a390ee442115cd7a3262ec513521d6191a117061436994657b563',
    'manuscript_access_registry.py':
        # SHA-256 of reviewed source bytes; not a credential
        '167d82b849a750edf2b0cfa92188931c9170db1a59c50eff4ba88ba48a5af2b8',
    'manuscript_pdf_gate.py':
        # SHA-256 of reviewed source bytes; not a credential
        '3ca55bf1e3e25e920ce9b79a5363e8d17138183ad592675d6fc058996fa41d0d',
    'methods_digest_registration_v3.py':
        # SHA-256 of reviewed source bytes; not a credential
        '1542b85fab50b686354075914ea461536db5da7b7bd3fee3b290eb7815d7e200',
    'methods_digest_v2.py':
        # SHA-256 of reviewed source bytes; not a credential
        'e3e8b5be4b99a9991066f49a60630c2a8d63eafd3c09b9b0ed85b50748706f39',
    'nightly_checkpoint_guarded.py':
        # SHA-256 of reviewed source bytes; not a credential
        'b01598e2223b7fe2ee77c3f7f89086fed899925621c9862dc4c504b5c16aad95',
    'owner_content_worker.py':
        # SHA-256 of reviewed source bytes; not a credential
        'e0af909495fe4ef14309b62b3037cec4a1cde3b9bfa1b124484719f180fa0080',
    'packaging_catalog.py':
        # SHA-256 of reviewed source bytes; not a credential
        '30a3e49d919fbf97b100a07f45222d86f8565443f019916758dde3748f43bc1b',
    'packaging_nightly.py':
        # SHA-256 of reviewed source bytes; not a credential
        '98aad9c41d0f70442bab7299cc5b3a39b171d418c9c942e3c2d2a9508e2bd2f7',
    'packaging_nightly_coverage.py':
        # SHA-256 of reviewed source bytes; not a credential
        'f1df587d5966ae71d98d6282375f1d5fb4cb99e14ec0f77ce6d704b4c00fbdf6',
    'packaging_nightly_intake.py':
        # SHA-256 of reviewed source bytes; not a credential
        '2739cf071710f83a867176e5fa3171096fe0ac2f26a3805ff4bc3ad6622e7cd8',
    'packaging_run_flow.py':
        # SHA-256 of reviewed source bytes; not a credential
        'cd4169d3cc2c3af02829d20ce363908a9edb914501f134dc341dd8d085567014',
    'packaging_runtime.py':
        # SHA-256 of reviewed source bytes; not a credential
        '5499b8572df26ecfba3fec728136708fc74a213d3233550617d319b10b0e02b2',
    'publish_dated_bundles_guarded.py':
        # SHA-256 of reviewed source bytes; not a credential
        '38a9752d9c686312acab087955cc9ccecd2e18fdabc13d54275ace2994486698',
    'publish_successor_wave_guarded.py':
        # SHA-256 of reviewed source bytes; not a credential
        'b754a9c09d4a98dcfb9add0fab2c714ab52d80b56a35d85d2c5572916b1527d3',
    'scientific_registration_worker.py':
        # SHA-256 of reviewed source bytes; not a credential
        'b995b5e99de7a4d270bb23ea5e9f453b4243c0af394a6411b961eaa7d02ef97d',
}
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


def child_command(checked, config_sha, *, go=False, output=None, rehearse=False):
    command = [sys.executable, '-B', str(INSTALLED / 'invoke_digest_v2.py'),
               '--root', str(ROOT), '--profile', str(PROFILE),
               '--expected-profile-sha256', checked['profile_binding']['sha256'],
               '--config', checked['config_path'], '--expected-config-sha256', config_sha]
    if go:
        need(output is not None, 'private controller output required for --go')
        path = Path(output).absolute()
        engine = os.environ.get('VIRIDIS_ENGINE_ROOT')
        scope = Path(engine).resolve(strict=True) / 'rehearsals' if rehearse and engine else ROOT / 'reports'
        need(not rehearse or bool(engine), 'rehearsal engine root required')
        need('..' not in path.parts and path.is_relative_to(scope)
             and not any(p.is_symlink() for p in (path, *path.parents)),
             'private controller output must remain in canonical reports')
        command.extend(['--go', '--output', str(path)])
        if rehearse:
            command.append('--rehearse')
    return command


def run_child(checked, config_sha, *, go=False, output=None, rehearse=False):
    command = child_command(checked, config_sha, go=go, output=output, rehearse=rehearse)
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
    parser.add_argument('--rehearse', action='store_true')
    args = parser.parse_args(argv)
    try:
        need(bool(os.environ.get('VIRIDIS_CORE_ROOT')), 'HOLD_CORE_ROOT_REQUIRED: set VIRIDIS_CORE_ROOT explicitly')
        need('VIRIDIS_ZENODO_API_BASE' not in os.environ, 'API base override is forbidden')
        need(not args.rehearse or args.go, 'rehearsal requires --go')
        options = {'rehearse': True} if args.rehearse else {}
        # Validate output before the first child. This guard never chooses a
        # controller or executes caller-provided source from a configuration.
        checked = context(args.config, args.expected_config_sha256)
        if args.go:
            child_command(checked, args.expected_config_sha256, go=True, output=args.output, **options)
        result = run_child(checked, args.expected_config_sha256)
        if result or not args.go:
            return result
        # A new ordinary child freshly repeats every downstream gate. A
        # successful preflight cannot supply a cached scientific admission.
        checked = context(args.config, args.expected_config_sha256)
        return run_child(checked, args.expected_config_sha256, go=True, output=args.output, **options)
    except (GuardHold, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
