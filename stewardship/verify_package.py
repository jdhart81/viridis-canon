"""Authenticate the supplied archive and all its manifest entries before extraction.
No manifest regeneration, old-file modification, code execution, or extraction.
"""
import argparse,hashlib,json,re,zipfile
from pathlib import Path,PurePosixPath
EXPECTED='6af21f66207ed9e20dfc11ef2b991d3cac077de066e9dde7b13f329c20021a9e'
def verify(path):
    data=path.read_bytes(); digest=hashlib.sha256(data).hexdigest()
    if digest!=EXPECTED: raise ValueError(f'archive SHA-256 mismatch: observed {digest}; expected {EXPECTED}')
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)): raise ValueError('duplicate ZIP members')
        for n in names:
            p=PurePosixPath(n)
            if p.is_absolute() or '..' in p.parts or '\\' in n: raise ValueError('unsafe archive member')
        manifests=[n for n in names if PurePosixPath(n).name=='SHA256SUMS.txt']
        if len(manifests)!=1: raise ValueError('expected one internal manifest')
        manifest=manifests[0]; root=PurePosixPath(manifest).parent
        checked=[]
        for line in z.read(manifest).decode().splitlines():
            if not line.strip(): continue
            match=re.fullmatch(r'([0-9a-fA-F]{64})\s+[ *]?(.+)',line)
            if not match: raise ValueError('malformed SHA256SUMS entry')
            expected,relative=match.groups(); p=PurePosixPath(relative)
            if p.is_absolute() or '..' in p.parts: raise ValueError('unsafe manifest member')
            member=str(root/p)
            if member not in names: raise ValueError(f'manifest member missing: {member}')
            actual=hashlib.sha256(z.read(member)).hexdigest()
            if actual!=expected.lower(): raise ValueError(f'internal checksum mismatch: {member}')
            checked.append(member)
        if len(checked)!=len(set(checked)): raise ValueError('duplicate manifest entries')
        unlisted=sorted(set(n for n in names if not n.endswith('/'))-set(checked)-{manifest})
        if unlisted: raise ValueError(f'unmanifested files: {unlisted}')
        return {'archive':str(path),'sha256':digest,'internal_manifest':manifest,
                'verified_members':checked,'evidence_class':'byte provenance only; no execution'}
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('archive',type=Path); a=p.parse_args()
    print(json.dumps(verify(a.archive),indent=2))
