#!/usr/bin/env python3
"""Offline presentation gate: every completion-report link names a Cowork file.

This does not validate certification, change receipt authority, or rewrite files.
The closed rendered-link grammar covers the receipt report writer's inline links;
unrecognized/reference/automatic link forms fail rather than evade inventory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

DEFAULT_ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
INLINE = re.compile(r'!?\[[^\]\n]*\]\((?:<[^>\n]*>|[^)\n]*)\)')
SCHEME = re.compile(r'^[A-Za-z][A-Za-z0-9+.-]*:')
LINE = re.compile(r'^(.*):([1-9][0-9]*)$')


def _visible(text: str) -> str:
    # Code examples are not rendered hyperlinks. Preserve lengths/newlines so
    # every actual link keeps its own offset and report line number.
    text = re.sub(r'(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$',
                  lambda m: re.sub(r'[^\n]', ' ', m.group()), text)
    return re.sub(r'(`+)([^`]*?)\1', lambda m: ' ' * len(m.group()), text)


def inventory(text: str) -> list[dict]:
    visible = _visible(text)
    matches = list(INLINE.finditer(visible))
    rest = INLINE.sub(lambda m: ' ' * len(m.group()), visible)
    if '](' in rest or re.search(r'!?\[[^\]\n]+\]\s*\[|^\s*\[[^\]\n]+\]:', rest, re.M):
        raise ValueError('Unrecognized or reference-style Markdown link')
    if re.search(r'<(?:[A-Za-z][A-Za-z0-9+.-]*:|/)[^>\n]+>', rest):
        raise ValueError('Automatic links are outside the closed report grammar')
    if re.search(r'(?i)<\s*(?:a|img)\b|\b[A-Za-z][A-Za-z0-9+.-]*://|\bwww\.', rest):
        raise ValueError('HTML and bare automatic links are outside the closed report grammar')
    rows = []
    for m in matches:
        target = m.group()[m.group().find('](') + 2:-1]
        if target.startswith('<') and target.endswith('>'):
            target = target[1:-1]
        elif any(c.isspace() for c in target):
            raise ValueError('Whitespace-bearing paths require angle delimiters')
        if not target or target != target.strip() or '\x00' in target or '\\' in target:
            raise ValueError('Invalid literal link target')
        rows.append({'target': target, 'line': text.count('\n', 0, m.start()) + 1})
    if not rows:
        raise ValueError('Completion report must contain evidence links')
    return rows


def _resolve(target: str, root: Path, report_dir: Path) -> Path:
    if SCHEME.match(target) or target.startswith('//'):
        raise ValueError('Every completion link must be a local Cowork file')
    if '?' in target or '#' in target:
        raise ValueError('Queries and fragments are not literal local file targets')
    p = Path(target)
    if not p.is_absolute():
        p = report_dir / p
    # Permit the editor's :positive-line suffix only when the full literal target
    # is not an existing file; it cannot alter containment or make a directory pass.
    if not p.exists():
        line = LINE.fullmatch(str(p))
        if line:
            p = Path(line[1])
    try:
        resolved = p.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError('Link is missing or resolves outside Cowork: ' + target) from exc
    if not resolved.is_file():
        raise ValueError('Evidence link must resolve to a regular file: ' + target)
    return resolved


def validate(text: str, root: Path = DEFAULT_ROOT, report_dir: Path | None = None) -> dict:
    root = Path(root)
    if not root.is_absolute() or not root.is_dir():
        raise ValueError('Existing absolute Cowork root required')
    root = root.resolve(strict=True)
    base = root if report_dir is None else Path(report_dir).resolve(strict=True)
    try:
        base.relative_to(root)
    except ValueError as exc:
        raise ValueError('Report directory outside Cowork') from exc
    rows = inventory(text)
    for row in rows:
        row['resolved'] = str(_resolve(row['target'], root, base))
    return {'standard': 'VRS-COMPLETION-LOCAL-LINKS-1',
            'status': 'COMPLETION_LINKS_CONTAINED_READONLY_PASS',
            'cowork_root': str(root), 'link_count': len(rows),
            'distinct_targets': len({r['target'] for r in rows}),
            'distinct_resolved_files': len({r['resolved'] for r in rows}),
            'links': rows, 'network_writes': 0, 'canonical_writes': 0}


def validate_file(report: Path, root: Path = DEFAULT_ROOT) -> dict:
    report = Path(report)
    raw = report.read_bytes()
    result = validate(raw.decode('utf-8'), root, report.parent)
    result.update(report=str(report), report_sha256=hashlib.sha256(raw).hexdigest())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_file(args.report, args.root)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({'standard': 'VRS-COMPLETION-LOCAL-LINKS-1',
                          'status': 'HOLD_COMPLETION_LINKS', 'reason': str(exc),
                          'network_writes': 0, 'canonical_writes': 0}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
