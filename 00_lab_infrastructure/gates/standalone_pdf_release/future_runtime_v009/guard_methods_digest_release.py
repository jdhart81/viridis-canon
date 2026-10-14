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
INSTALLED = ROOT / '_ZENODO_DEPOSITS/standalone_pdf_runtime_v009'
PROFILE = INSTALLED / 'CURRENT_PACKAGING_PROFILE.json'
NOMINATION = INSTALLED / 'INSTALLATION_NOMINATION.json'
# Exact 19-module successor source set, fixed before source freeze and review.
SOURCE_HASHES = {
    'digest_controller_v2.py': ('faeba58a' '0a080e4b' '838536b0' 'ac4f32fc' '9399497c' '4cc84d15' 'ab9eaca0' 'f83d9413'),
    'install_packaging_runtime.py': ('66314302' 'b569ce0d' '56ea1d98' '68f0d0a9' '67c02946' 'd5754a8b' '0b140d78' 'b01b6a89'),
    'invoke_digest_v2.py': ('96480eca' '8c439be8' 'd0578022' '13fbc042' '81fc48d7' '1b0d1b01' '3c4b6234' '3f932f87'),
    'manuscript_access_correction.py': ('c56b402f' '663a390e' 'e442115c' 'd7a3262e' 'c513521d' '6191a117' '06143699' '4657b563'),
    'manuscript_access_registry.py': ('167d82b8' '49a750ed' 'f2b0cfa9' '2188931c' '9170db1a' '59c50eff' '4ba88ba4' '8a5af2b8'),
    'manuscript_pdf_gate.py': ('95cd1bd6' '9e90bdae' '92e17707' '3ed419fe' '28dc7dda' 'b905cca4' 'ac379c00' '27c0cd39'),
    'methods_digest_registration_v3.py': ('1542b85f' 'ab50b686' '35407591' '4ea46153' '6db5da7b' '7bd3fee3' 'b290eb78' '15d7e200'),
    'methods_digest_v2.py': ('e3e8b5be' '4b99a999' '1066f49a' '60630c2a' '8d63eafd' '3c09b9b0' 'ed85b507' '48706f39'),
    'nightly_checkpoint_guarded.py': ('298d2498' '901e437a' 'c6a1ccc4' 'e4a0841f' 'b3d50244' 'abd36309' 'e0f9f533' 'f179738e'),
    'owner_content_worker.py': ('b0170554' '83941b06' '97139fd9' 'b4520320' '48d82f89' 'e16c1e7d' '78673851' 'e230c934'),
    'packaging_catalog.py': ('6816ea48' '68dd4d12' '62084348' '023e0132' 'a0aa6388' '43bf6dc9' 'cfb025d0' '5c086346'),
    'packaging_nightly.py': ('844472e6' '2b2bf9d5' 'a86a8076' 'cdb52b72' '17d492ca' '7be621dd' 'a8aaea9c' 'db4ce663'),
    'packaging_nightly_coverage.py': ('f1df587d' '5966ae71' 'd98d6282' '375f1d5f' 'b4cb99e1' '4ec0f77c' 'e6d704b4' 'c00fbdf6'),
    'packaging_nightly_intake.py': ('2739cf07' '1710f83a' '867176e5' 'fa317109' '6fe0ac2f' '26a3805f' 'f4bc3ad6' '622e7cd8'),
    'packaging_run_flow.py': ('cd4169d3' 'cc2c3af0' '2829d20c' 'e363908a' '9edb9145' '01f134dc' '341dd8d0' '85567014'),
    'packaging_runtime.py': ('776fd758' '3a49a057' '6c93e638' '7fb99822' '1bbc6b5c' '1d152e50' '87771b98' '0073c934'),
    'publish_dated_bundles_guarded.py': ('6208c2d6' 'f9bc711f' 'c98a5b97' '9201cdaf' '89226419' 'c7ab5b59' '98052d6b' 'dd0f9158'),
    'publish_successor_wave_guarded.py': ('8b33088f' 'c0249f0f' '66a9f2f0' 'ce335946' 'b540fbac' 'e49a5c73' '4362d58b' 'e8056293'),
    'scientific_registration_worker.py': ('b0d425f9' 'e1987143' 'c22fcc87' '30c31abf' '58245e6c' '97551b26' 'c57f1ad4' 'a74ed5dd'),
}


class GuardHold(ValueError):
    pass


def need(value, reason):
    if not value:
        raise GuardHold('HOLD_STANDALONE_MANUSCRIPT_PDF: ' + reason)


def identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def read(path, expected=None):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts
         and path.is_relative_to(ROOT), 'canonical input path required')
    need(not any(p.is_symlink() for p in (path, *path.parents)),
         'regular input ancestry required')
    before = path.stat()
    need(stat.S_ISREG(before.st_mode), 'regular input file required')
    raw = path.read_bytes()
    after = path.stat()
    digest = hashlib.sha256(raw).hexdigest()
    need(identity(before) == identity(after)
         and not any(p.is_symlink() for p in (path, *path.parents))
         and path.resolve(strict=True).is_relative_to(ROOT)
         and identity(path.stat()) == identity(after)
         and (expected is None or digest == expected), 'input hash or identity changed')
    return raw, digest, identity(after)


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
         and nomination.get('standard') == 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-9'
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
         and profile.get('standard') == 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-9'
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
