"""Select existing certificates without changing their acceptance consumers."""
from pathlib import Path
import re


def certificate_selection_paths(root, cert_root, current_certificate):
    root, cert_root = Path(root).resolve(strict=True), Path(cert_root).resolve(strict=True)
    if not cert_root.is_relative_to(root) or not cert_root.is_dir():
        raise ValueError('configured certificate root must be a canonical-tree directory')
    standard_store = root / 'RESEARCH_PIPELINE_v2/lean_certificates'
    paths = []
    for directory in sorted(cert_root.glob('Run-*')):
        if re.fullmatch(r'Run-[0-9]+', directory.name) is None or not directory.is_dir():
            continue
        if directory.is_symlink():
            raise ValueError('symlink certificate run store refused')
        original = directory / 'LEAN_ZERO_SORRY_CERTIFICATE.json'
        # Nondefault --cert-root keeps its existing originals-only contract.
        # It must never silently import a certificate from the default store.
        selected = current_certificate(root, directory.name) if cert_root == standard_store else None
        if selected:
            path = Path(selected[0])
            if path.is_symlink() or path.parent.resolve() != directory.resolve() or not path.is_file():
                raise ValueError('current-certificate path differs from configured cert root/run')
            paths.append(path)
        elif original.is_file():
            # Retain invalid originals in the audit, so fail-closed reasons and
            # separate WIP file statuses are not erased by the selection fix.
            paths.append(original)
    return paths
