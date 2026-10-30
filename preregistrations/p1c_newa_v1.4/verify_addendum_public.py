#!/usr/bin/env python3
"""Addendum 1 to plan P1C v1.4: check that the public registration also holds the addendum and its proof.

fetch_outcomes.py, frozen with v1.4, checks only the plan and FREEZE.json in the public record (its G2). Addendum 1
commits that no outcome is requested until this check has passed too: run it after verify_registration.py and before
fetch_outcomes.py. It downloads ADDENDUM_v1.4.md and ADDENDUM_v1.4.md.ots ANONYMOUSLY from the same public record and
writes ADDENDUM_REGISTRATION.json only if both are byte-identical to the local copies. An anonymous download that
succeeds is itself the evidence that the record is public.

Usage, from p1c/ (the local copies are in addendum_v1.4/ unless another folder is given):
  python3 -B addendum_v1.4/verify_addendum_public.py zenodo <record id> [local folder]
  python3 -B addendum_v1.4/verify_addendum_public.py github <owner/repo> <40-hex commit> <folder path in repo> [local folder]
"""
import hashlib, json, os, re, sys, time, urllib.request

FILES = ['ADDENDUM_v1.4.md', 'ADDENDUM_v1.4.md.ots']


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'viridis-p1c-verify/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def digests(b):
    return dict(sha256=hashlib.sha256(b).hexdigest(), md5=hashlib.md5(b).hexdigest(), bytes=len(b))


def main(argv):
    kind = argv[1] if len(argv) > 1 else ''
    reg = dict(verified_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), registered_files={})
    if kind == 'github' and len(argv) in (5, 6):
        repo, commit, folder = argv[2], argv[3], argv[4].strip('/')
        local = argv[5] if len(argv) == 6 else 'addendum_v1.4'
        if not re.fullmatch(r'[0-9a-f]{40}', commit):
            sys.exit('full 40-hex commit SHA required')
        reg['github'] = dict(repo=repo, commit=commit, folder=folder,
                             evidence='files downloaded anonymously from raw.githubusercontent.com at this commit')
        urls = {f: f'https://raw.githubusercontent.com/{repo}/{commit}/{folder}/{f}' for f in FILES}
    elif kind == 'zenodo' and len(argv) in (3, 4):
        rid = argv[2]
        local = argv[3] if len(argv) == 4 else 'addendum_v1.4'
        if not re.fullmatch(r'\d+', rid):
            sys.exit('numeric Zenodo record id required')
        rec = json.loads(get(f'https://zenodo.org/api/records/{rid}'))
        byname = {f['key']: f for f in rec['files']}
        missing = [f for f in FILES if f not in byname]
        if missing:
            sys.exit(f'NOT IN THE PUBLIC RECORD: {missing}; ADDENDUM_REGISTRATION.json not written')
        reg['zenodo'] = dict(record=rid, doi=rec.get('doi'), created=rec.get('created'), evidence='anonymous Zenodo API read')
        urls = {f: byname[f]['links']['self'] for f in FILES}
    else:
        sys.exit(__doc__)
    for f, u in urls.items():
        remote = digests(get(u))
        mine = digests(open(os.path.join(local, f), 'rb').read())
        if remote != mine:
            sys.exit(f'MISMATCH for {f}: public {remote} vs local {mine}; ADDENDUM_REGISTRATION.json not written')
        reg['registered_files'][f] = dict(url=u, **remote)
    json.dump(reg, open('ADDENDUM_REGISTRATION.json', 'w'), indent=1)
    print(json.dumps(reg, indent=1))


if __name__ == '__main__':
    main(sys.argv)
