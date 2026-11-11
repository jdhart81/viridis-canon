"""P1C-W: fetch ERA5 hourly 10 m u/v for a box covering NE Washington (P1C) and the west-side Oregon Cascades,
from the public NSF NCAR ERA5 mirror on AWS (s3://nsf-ncar-era5, ds633.0), by HDF5 byte-range reads.
Weather only: no fire record of any kind is read or requested here.
Box: latitude rows for 49.5..43.25 N, longitude 237.0..243.5 E (-123.0..-116.5)."""
import fsspec, h5py, numpy as np, os, sys, time, json, calendar
from multiprocessing import Pool
BASE = 'https://nsf-ncar-era5.s3.amazonaws.com/e5.oper.an.sfc/{ym}/e5.oper.an.sfc.{code}.ll025sc.{ym}0100_{ym}{last:02d}23.nc'
CODES = {'u10': ('128_165_10u', 'VAR_10U'), 'v10': ('128_166_10v', 'VAR_10V')}
LAT0, LAT1, LON0, LON1 = 162, 188, 948, 975   # 49.5..43.25 N ; 237.0..243.5 E
LOG = 'raw/era5/requests.log'

def one(ym):
    y, m = int(ym[:4]), int(ym[4:])
    out = f'raw/era5/era5_wind_{ym}.npz'
    if os.path.exists(out):
        return ym, 'cached'
    last = calendar.monthrange(y, m)[1]
    arrs = {}
    for name, (code, var) in CODES.items():
        url = BASE.format(ym=ym, code=code, last=last)
        for attempt in range(5):
            try:
                h = h5py.File(fsspec.open(url, block_size=2**20).open(), 'r')
                arrs[name] = h[var][:, LAT0:LAT1, LON0:LON1].astype(np.float32)
                arrs['time'] = h['time'][:]; arrs['lat'] = h['latitude'][LAT0:LAT1]; arrs['lon'] = h['longitude'][LON0:LON1]
                with open(LOG, 'a') as f:
                    f.write(json.dumps({'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'url': url, 'shape': list(arrs[name].shape)}) + '\n')
                break
            except Exception as e:
                time.sleep(2 ** attempt)
        else:
            return ym, 'FAILED'
    np.savez_compressed(out + '.tmp.npz', **arrs); os.replace(out + '.tmp.npz', out)
    return ym, 'ok'

if __name__ == '__main__':
    months = ['199112'] + [f'{y}{m:02d}' for y in range(1992, 2025) for m in range(1, 13)] + ['202501']
    os.makedirs('raw/era5', exist_ok=True)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as p:
        for ym, st in p.imap_unordered(one, months):
            print(ym, st, flush=True)
