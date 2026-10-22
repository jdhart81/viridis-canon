#!/usr/bin/env python3
"""Assemble the public registration package (flat folder) for plan v1.4. Run after freeze.py --stamp.

Every frozen source is checked against FREEZE.json first. Large predictor inputs (LANDFIRE and PCL arrays, roads,
NHD, ERC: about 400 MB) are not copied; their hashes are in FREEZE.json and fetch_data.py re-fetches them from the
live services (not byte-reproducibly, since the services can change). Tables and raw records are gzipped
deterministically (no name or timestamp in the header); logs and history are packed into deterministic tar.gz
files. SHA256SUMS.txt covers every file. Usage: python3 make_package.py <output dir>"""
import glob, gzip, hashlib, io, json, os, shutil, sys, tarfile

OUT = sys.argv[1]
F = json.load(open('FREEZE.json'))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
for p, h in F['sha256'].items():
    assert sha(p) == h, f'{p} changed after the freeze'
assert os.path.exists('FREEZE.json.ots'), 'stamp FREEZE.json first'
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)


def gz(src, name, check=True):
    dst = os.path.join(OUT, name)
    with open(src, 'rb') as fi, open(dst, 'wb') as fo:
        with gzip.GzipFile(filename='', mode='wb', fileobj=fo, compresslevel=9, mtime=0) as g:
            shutil.copyfileobj(fi, g)
    if check:
        assert hashlib.sha256(gzip.decompress(open(dst, 'rb').read())).hexdigest() == F['sha256'][src]


def targz(paths, name):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w', format=tarfile.PAX_FORMAT) as tf:
        for p in sorted(paths):
            data = open(p, 'rb').read(); ti = tarfile.TarInfo(p); ti.size = len(data); ti.mtime = 0; ti.mode = 0o644
            ti.uid = ti.gid = 0; ti.uname = ti.gname = ''
            tf.addfile(ti, io.BytesIO(data))
    with open(os.path.join(OUT, name), 'wb') as fo:
        with gzip.GzipFile(filename='', mode='wb', fileobj=fo, compresslevel=9, mtime=0) as g:
            g.write(buf.getvalue())


plain = [p for p in F['sha256'] if '/' not in p and p not in ('predictors_blind.csv', 'REGISTRATION_README.md')]
for p in plain:
    shutil.copy2(p, os.path.join(OUT, p))
shutil.copy2('REGISTRATION_README.md', os.path.join(OUT, 'README.md'))
for p in ('FREEZE.json', 'FREEZE.json.ots'):
    shutil.copy2(p, os.path.join(OUT, p))
gz('predictors_blind.csv', 'predictors_blind.csv.gz')
gz('raw/fpafod_ignitions_blind.json', 'raw_fpafod_ignitions_blind.json.gz')
gz('raw/mtbs_perims.json', 'raw_mtbs_perims.json.gz')
for p, name in [('raw/requests.log', 'raw_requests.log'), ('raw/pcl_legend.json', 'raw_pcl_legend.json'),
                ('raw/pcl_tile_log.json', 'raw_pcl_tile_log.json'), ('../p1/p1_config.json', 'pilot_p1_config.json'),
                ('../p1/results.json', 'pilot_results.json'), ('../p1/DEVIATION_2.json', 'pilot_DEVIATION_2.json'),
                ('../p1/DEVIATION_3.json', 'pilot_DEVIATION_3.json'),
                ('../p1/raw/requests.log', 'pilot_raw_requests.log')]:
    shutil.copy2(p, os.path.join(OUT, name))
gz('../p1/predictors_blind.csv', 'pilot_predictors_blind.csv.gz')
gz('../p1/outcomes.csv', 'pilot_outcomes.csv.gz')
gz('../p1/raw/mtbs_perims.json', 'pilot_raw_mtbs_perims.json.gz')
targz([k for k in F['sha256'] if k.startswith('logs/')], 'logs.tar.gz')
skip = lambda p: os.path.isdir(p) or p.endswith('.csv')          # CSVs are identical to the current ones (hashes in each FREEZE)
targz([p for p in glob.glob('history_v1.0/*') if not skip(p)], 'history_v1.0.tar.gz')
targz([p for p in glob.glob('history_v1.1/*') if not skip(p)], 'history_v1.1.tar.gz')
targz([p for p in glob.glob('history_v1.2/*') if not skip(p)], 'history_v1.2.tar.gz')
targz([p for p in glob.glob('history_v1.3/*') if not skip(p)], 'history_v1.3.tar.gz')
targz(glob.glob('history_v1.1_dev/*'), 'history_v1.1_dev.tar.gz')
targz(glob.glob('history_v1.3_dev/*'), 'history_v1.3_dev.tar.gz')
targz(glob.glob('history_v1.4_dev/*'), 'history_v1.4_dev.tar.gz')
for p in sorted(glob.glob('audits/*.md')):
    assert sha(p) == F['sha256'][p]
    shutil.copy2(p, os.path.join(OUT, os.path.basename(p)))
names = sorted(n for n in os.listdir(OUT) if n != 'SHA256SUMS.txt')
with open(os.path.join(OUT, 'SHA256SUMS.txt'), 'w') as fh:
    for n in names:
        fh.write(f'{sha(os.path.join(OUT, n))}  {n}\n')
size = sum(os.path.getsize(os.path.join(OUT, n)) for n in names)
print(OUT, len(names), 'files;', size // 1024, 'KiB')
