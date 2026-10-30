#!/usr/bin/env python3
"""Verify the public registration of the P1-M (P1C region) plan and write REGISTRATION_P1M.json.

Downloads ANONYMOUSLY, from the registered commit:
- every frozen file of this folder listed in MECH_FREEZE.json (the plan, scripts, disjoint input, pre-freeze checks
  and the frozen pilot code copies);
- MECH_FREEZE.json and MECH_FREEZE.json.ots.

Writes REGISTRATION_P1M.json only if every file matches the local copy byte for byte. A successful anonymous download
is itself the evidence that the record is public.

Usage: python3 -B verify_p1m_registration.py <owner/repo> <40-hex commit> <folder path in repo> [<PR url>]
"""
import hashlib, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'viridis-p1m-verify/1.0'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def digests(b):
    return dict(sha256=hashlib.sha256(b).hexdigest(), bytes=len(b))


def main():
    repo, commit, folder = sys.argv[1], sys.argv[2], sys.argv[3].strip('/')
    assert re.fullmatch(r'[0-9a-f]{40}', commit), 'full 40-hex commit SHA required'
    out = os.path.join(HERE, 'REGISTRATION_P1M.json')
    assert not os.path.exists(out), 'REGISTRATION_P1M.json already exists'
    frozen = json.load(open(os.path.join(HERE, 'MECH_FREEZE.json')))['sha256']
    files = [rel for rel in frozen if not rel.startswith('/')] + ['MECH_FREEZE.json', 'MECH_FREEZE.json.ots']
    reg = dict(verified_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               github=dict(repo=repo, commit=commit, folder=folder, pr=sys.argv[4] if len(sys.argv) > 4 else None,
                           evidence='files downloaded anonymously from raw.githubusercontent.com at this commit'),
               registered_files={})
    for rel in files:
        url = f'https://raw.githubusercontent.com/{repo}/{commit}/{folder}/' + urllib.parse.quote(rel)
        remote, local = digests(get(url)), digests(open(os.path.join(HERE, rel), 'rb').read())
        if remote != local:
            sys.exit(f'MISMATCH for {rel}: public {remote} vs local {local}; REGISTRATION_P1M.json not written')
        if rel in frozen:
            assert local['sha256'] == frozen[rel], f'{rel} differs from the freeze record'
        reg['registered_files'][rel] = dict(url=url, **remote)
    json.dump(reg, open(out, 'w'), indent=1)
    print(json.dumps(dict(verified_at_utc=reg['verified_at_utc'], files=len(reg['registered_files']), **reg['github']), indent=1))


if __name__ == '__main__':
    main()
