#!/usr/bin/env python3
"""Verify the public registration of the confirmatory plan and write REGISTRATION.json (where to look).
fetch_outcomes.py repeats the anonymous download-and-compare itself before fetching; this file is a convenience.

Downloads the registered PREREGISTRATION_P1C_NEWA_v1.4.md and FREEZE.json ANONYMOUSLY from the public record,
hashes them, and writes REGISTRATION.json only if both match the local frozen files byte-for-byte.
An anonymous download succeeding is itself the evidence that the record is public.

Usage:
  python3 verify_registration.py github <owner/repo> <40-hex commit> <folder path in repo> [<PR url>]
  python3 verify_registration.py zenodo <record id>
"""
import hashlib, json, re, sys, time, urllib.request

FILES = ['PREREGISTRATION_P1C_NEWA_v1.4.md', 'FREEZE.json']


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'viridis-p1c-verify/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def digests(b):
    return dict(sha256=hashlib.sha256(b).hexdigest(), md5=hashlib.md5(b).hexdigest(), bytes=len(b))


def main():
    kind = sys.argv[1]
    reg = dict(verified_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), registered_files={})
    if kind == 'github':
        repo, commit, folder = sys.argv[2], sys.argv[3], sys.argv[4].strip('/')
        assert re.fullmatch(r'[0-9a-f]{40}', commit), 'full 40-hex commit SHA required'
        reg['github'] = dict(repo=repo, commit=commit, folder=folder, public=True,
                             pr=(sys.argv[5] if len(sys.argv) > 5 else None),
                             evidence='files downloaded anonymously from raw.githubusercontent.com at this commit')
        urls = {f: f'https://raw.githubusercontent.com/{repo}/{commit}/{folder}/{f}' for f in FILES}
    elif kind == 'zenodo':
        rid = sys.argv[2]
        rec = json.loads(get(f'https://zenodo.org/api/records/{rid}'))
        reg['zenodo'] = dict(record=rid, doi=rec['doi'], created=rec.get('created'), evidence='anonymous Zenodo API read')
        byname = {f['key']: f for f in rec['files']}
        urls = {f: byname[f]['links']['self'] for f in FILES}
        for f in FILES:
            reg['zenodo'][f + ' listed checksum'] = byname[f]['checksum']
    else:
        sys.exit('kind must be github or zenodo')
    for f, u in urls.items():
        remote = digests(get(u)); local = digests(open(f, 'rb').read())
        if remote != local:
            sys.exit(f'MISMATCH for {f}: public {remote} vs local {local}; REGISTRATION.json not written')
        reg['registered_files'][f] = dict(url=u, **remote)
    json.dump(reg, open('REGISTRATION.json', 'w'), indent=1)
    print(json.dumps(reg, indent=1))


if __name__ == '__main__':
    main()
