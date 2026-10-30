#!/usr/bin/env python3
"""P1 pilot data acquisition (BLIND to fire outcomes).

Invariants:
  F1  No outcome field is ever requested from FPA FOD in this script:
      fire_size, fire_size_class, cont_date/doy/time, mtbs_id, mtbs_fire_name,
      complex_name, ics_209_* are excluded by an explicit allow-list.
  F2  Every layer lands on the same 30 m EPSG:5070 grid (compute box in p1_config.json).
  F3  Every download is cached under raw/ with its request URL logged, so the run is reproducible.
"""
import io, json, os, sys, time, urllib.parse, urllib.request
import numpy as np
from PIL import Image

CFG = json.load(open('p1_config.json'))
X0, Y0, X1, Y1 = CFG['compute_box_5070']
RES = CFG['res']; W, H = CFG['W'], CFG['H']
os.makedirs('raw', exist_ok=True)
LOG = open('raw/requests.log', 'a')

BLIND_FIELDS = ['objectid', 'fod_id', 'fire_year', 'discovery_date', 'discovery_doy',
                'nwcg_cause_classification', 'nwcg_general_cause', 'latitude', 'longitude',
                'owner_descr', 'state', 'nwcg_reporting_agency']
FORBIDDEN = {'fire_size', 'fire_size_class', 'cont_date', 'cont_doy', 'cont_time', 'mtbs_id',
             'mtbs_fire_name', 'complex_name', 'ics_209_plus_incident_join_id', 'ics_209_plus_complex_join_id'}
assert not (set(BLIND_FIELDS) & FORBIDDEN)  # F1


def fetch(url, data=None, tries=4, timeout=180):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'viridis-p1/1.0'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
            LOG.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {url[:300]}\n"); LOG.flush()
            return b
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(3 * (k + 1))


def tiles(nx=2, ny=2):
    """Split the compute grid into nx*ny tiles; yields (col0,row0,w,h,bbox)."""
    cw = -(-W // nx); ch = -(-H // ny)
    for j in range(ny):
        for i in range(nx):
            c0, r0 = i * cw, j * ch
            w, h = min(cw, W - c0), min(ch, H - r0)
            bx0 = X0 + c0 * RES; bx1 = bx0 + w * RES
            by1 = Y1 - r0 * RES; by0 = by1 - h * RES
            yield c0, r0, w, h, (bx0, by0, bx1, by1)


# ---------------- rasters ----------------
def landfire():
    out = 'raw/fbfm40_lf2024.npy'
    if os.path.exists(out):
        return
    base = 'https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2024/LF2024_FBFM40_CONUS/ImageServer/exportImage'
    arr = np.zeros((H, W), dtype=np.int16)
    for c0, r0, w, h, bb in tiles():
        q = dict(bbox=','.join(map(str, bb)), bboxSR=5070, imageSR=5070, size=f'{w},{h}', format='tiff',
                 pixelType='S16', interpolation='RSP_NearestNeighbor', f='image')
        b = fetch(base + '?' + urllib.parse.urlencode(q))
        import tifffile
        t = tifffile.imread(io.BytesIO(b))
        assert t.shape == (h, w), (t.shape, h, w)
        arr[r0:r0 + h, c0:c0 + w] = t
    np.save(out, arr)
    print('landfire', np.unique(arr)[:40])


def pcl():
    out = 'raw/pcl_class.npy'
    if os.path.exists(out):
        return
    base = 'https://gis.dnr.wa.gov/site3/rest/services/Public_Wildfire/POD_Project_Data/MapServer'
    leg = json.loads(fetch(base + '/legend?f=pjson'))
    import base64
    swatches = []
    for e in [L for L in leg['layers'] if L['layerId'] == 0][0]['legend']:
        im = Image.open(io.BytesIO(base64.b64decode(e['imageData']))).convert('RGBA')
        a = np.array(im).reshape(-1, 4)
        a = a[a[:, 3] > 200]
        vals, counts = np.unique(a[:, :3], axis=0, return_counts=True)
        swatches.append((e['label'], tuple(int(v) for v in vals[counts.argmax()])))
    json.dump(swatches, open('raw/pcl_legend.json', 'w'))
    cls = np.full((H, W), -1, dtype=np.int8)        # -1 = nodata
    dist_max = np.zeros((H, W), dtype=np.float32)
    S = np.array([s[1] for s in swatches], dtype=np.float32)
    # The server renders large extents unreliably (blank or partial images), so use 512 px tiles
    # and retry tiles whose opaque fraction is below the best seen for that tile.
    nx, ny = -(-W // 512), -(-H // 512)
    tile_log = []
    for c0, r0, w, h, bb in tiles(nx, ny):
        q = dict(bbox=','.join(map(str, bb)), bboxSR=5070, imageSR=5070, size=f'{w},{h}', format='png32',
                 transparent='true', layers='show:0', dpi=96, f='image')
        best = None
        for attempt in range(4):
            b = fetch(base + '/export?' + urllib.parse.urlencode(q))
            im = np.array(Image.open(io.BytesIO(b)).convert('RGBA'))
            assert im.shape[:2] == (h, w), (im.shape, h, w)
            op = float((im[:, :, 3] >= 128).mean())
            if best is None or op > best[0]:
                best = (op, im)
            if op >= 0.999 or (attempt >= 1 and op == best[0]):
                break   # full tile, or two identical answers in a row (genuine edge / no-data)
        op, im = best
        tile_log.append((c0, r0, op, attempt + 1))
        rgb = im[:, :, :3].astype(np.float32); alpha = im[:, :, 3]
        d = np.sqrt(((rgb[:, :, None, :] - S[None, None, :, :]) ** 2).sum(-1))
        k = d.argmin(-1).astype(np.int8); dm = d.min(-1)
        k[alpha < 128] = -1
        cls[r0:r0 + h, c0:c0 + w] = k
        dist_max[r0:r0 + h, c0:c0 + w] = np.where(alpha < 128, 0, dm)
    json.dump(tile_log, open('raw/pcl_tile_log.json', 'w'))
    np.save(out, cls)
    print('pcl classes', {int(v): int(c) for v, c in zip(*np.unique(cls, return_counts=True))},
          'max color distance', float(dist_max.max()), 'p99', float(np.percentile(dist_max[cls >= 0], 99)))


# ---------------- vectors ----------------
def esri_query_all(layer_url, where='1=1', fields='*', geom=None, in_sr=5070, out_sr=5070, chunk=500):
    """Return list of Esri-JSON features; paginates by objectIds (F3 caching handled by caller)."""
    base = dict(where=where, f='json')
    if geom is not None:
        base.update(geometryType='esriGeometryEnvelope', inSR=in_sr, spatialRel='esriSpatialRelIntersects')
    ids = sorted(_ids(layer_url, base, geom))
    feats = []
    for i in range(0, len(ids), chunk):
        feats += _query_ids(layer_url, ids[i:i + chunk], fields, out_sr)
    return feats


def esri_query_cached(layer_url, name, where, fields, geom, nx=4, ny=4, chunk=200, in_sr=5070, out_sr=5070):
    """Resumable query for a flaky server: object ids are requested per tile (nx x ny) and features per chunk, each
    cached under raw/cache_<name>/; any failed request stops the run, and a rerun resumes where it stopped. Returns
    the same features as esri_query_all (a feature intersects the box iff it intersects at least one tile)."""
    d = f'raw/cache_{name}'
    os.makedirs(d, exist_ok=True)
    base = dict(where=where, f='json', geometryType='esriGeometryEnvelope', inSR=in_sr,
                spatialRel='esriSpatialRelIntersects', returnIdsOnly='true')
    x0, y0, x1, y1 = geom
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny

    def tile_ids(g, key, depth):
        p = f'{d}/ids_{key}.json'
        if os.path.exists(p):
            return set(json.load(open(p)))
        try:
            if os.path.exists(f'{d}/split_{key}'):
                raise RuntimeError('tile failed before; go straight to its quadrants')
            r = json.loads(fetch(layer_url + '/query', data=urllib.parse.urlencode(dict(base, geometry=','.join(map(str, g)))).encode(), tries=1))
            if 'error' in r:
                raise RuntimeError(r['error'])
            out = set(r.get('objectIds') or [])
        except Exception:
            if depth >= 2:
                raise
            open(f'{d}/split_{key}', 'w').close()
            a0, b0, a1, b1 = g; am, bm = (a0 + a1) / 2, (b0 + b1) / 2
            out = set()
            for k, sg in enumerate([(a0, b0, am, bm), (am, b0, a1, bm), (a0, bm, am, b1), (am, bm, a1, b1)]):
                out |= tile_ids(sg, f'{key}q{k}', depth + 1)
        json.dump(sorted(out), open(p, 'w'))
        print(f'  {name}: ids tile {key} cached', flush=True)
        return out

    ids = set()
    for i in range(nx):
        for j in range(ny):
            ids |= tile_ids((x0 + i * dx, y0 + j * dy, x0 + (i + 1) * dx, y0 + (j + 1) * dy), f'{i}_{j}', 0)
    ids = sorted(ids)
    def feat_chunk(sub):
        p = f'{d}/feat_{sub[0]}_{sub[-1]}_{len(sub)}.json'
        if os.path.exists(p):
            return json.load(open(p))
        try:
            qq = dict(f='json', objectIds=','.join(map(str, sub)), outFields=fields, outSR=out_sr, returnGeometry='true')
            r = json.loads(fetch(layer_url + '/query', data=urllib.parse.urlencode(qq).encode(), tries=1))
            if 'error' in r:
                raise RuntimeError(r['error'])
            fs = r.get('features', [])
        except Exception:
            if len(sub) == 1:
                raise
            h = len(sub) // 2
            fs = feat_chunk(sub[:h]) + feat_chunk(sub[h:])
        json.dump(fs, open(p, 'w'))
        return fs

    feats = []
    for k in range(0, len(ids), chunk):
        feats += feat_chunk(ids[k:k + chunk])
    print(f'  {name}: {len(ids)} ids, {len(feats)} features', flush=True)
    assert len(feats) == len(ids), 'feature count differs from id count'
    return feats


def _ids(layer_url, base_q, geom, depth=0):
    """objectIds of the features intersecting the envelope. If the server times out (HTTP 504 on large extents),
    query the four quadrants and take the union: the same set, since a feature intersects the envelope iff it
    intersects at least one quadrant."""
    q = dict(base_q, returnIdsOnly='true')
    if geom is not None:
        q['geometry'] = ','.join(map(str, geom))
    try:
        r = json.loads(fetch(layer_url + '/query', data=urllib.parse.urlencode(q).encode(), tries=(2 if depth < 3 else 4)))
        if 'error' in r:
            raise RuntimeError(r['error'])
        return set(r.get('objectIds') or [])
    except Exception:
        if geom is None or depth >= 3:
            raise
        x0, y0, x1, y1 = geom
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        print(f'  split id query into quadrants (depth {depth + 1})', flush=True)
        out = set()
        for g in [(x0, y0, xm, ym), (xm, y0, x1, ym), (x0, ym, xm, y1), (xm, ym, x1, y1)]:
            out |= _ids(layer_url, base_q, g, depth + 1)
        return out


def _query_ids(layer_url, ids, fields, out_sr):
    """Fetch features by objectId. A chunk that fails (e.g. HTTP 504 on heavy geometry) is split in half and
    retried, so the result is the same set of features, only in more requests."""
    qq = dict(f='json', objectIds=','.join(map(str, ids)), outFields=fields, outSR=out_sr, returnGeometry='true')
    try:
        r = json.loads(fetch(layer_url + '/query', data=urllib.parse.urlencode(qq).encode(), tries=(6 if len(ids) == 1 else 2)))
        if 'error' in r:
            raise RuntimeError(r['error'])
        return r.get('features', [])
    except Exception:
        if len(ids) == 1:
            raise
        h = len(ids) // 2
        print(f'  split chunk of {len(ids)} after a failed request', flush=True)
        return _query_ids(layer_url, ids[:h], fields, out_sr) + _query_ids(layer_url, ids[h:], fields, out_sr)


def vectors():
    bb = (X0, Y0, X1, Y1)
    jobs = {
        'roads_primary': ('https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Transportation/MapServer/2', 'MTFCC'),
        'roads_secondary': ('https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Transportation/MapServer/6', 'MTFCC'),
        'roads_local': ('https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Transportation/MapServer/8', 'MTFCC'),
        'nhd_area': ('https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/9', 'ftype,fcode'),
        'nhd_waterbody': ('https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/12', 'ftype,fcode,areasqkm'),
    }
    # Confirmatory change: the NHD server times out on the full waterbody layer over this box, so request only the
    # FTYPEs that build_predictors.py uses (LakePond 390, Reservoir 436, IceMass 378). The features used are the
    # same as fetching everything and filtering in build_predictors.py, which still applies the same filter.
    where = {'nhd_waterbody': 'ftype IN (390,436,378)'}
    for name, (url, fields) in jobs.items():
        out = f'raw/{name}.json'
        if os.path.exists(out):
            continue
        if name == 'nhd_waterbody':      # resumable, tile by tile (see esri_query_cached)
            feats = esri_query_cached(url, name, where[name], fields, bb)
        else:
            feats = esri_query_all(url, where=where.get(name, '1=1'), fields=fields, geom=bb)
        json.dump(feats, open(out, 'w'))
        print(name, len(feats))
    mtbs()


def mtbs():
    """MTBS burned-area boundaries, all years (used ONLY as barrier features for later years)."""
    bb = (X0, Y0, X1, Y1)
    out = 'raw/mtbs_perims.json'
    if not os.path.exists(out):
        meta = json.loads(fetch('https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer?f=pjson'))
        allf = []
        for L in meta['layers']:
            if 'Burned Area Boundaries' in L['name'] and L['name'][:4].isdigit():
                yr = int(L['name'][:4])
                fs = esri_query_all(f"https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/{L['id']}",
                                    fields='OBJECTID', geom=bb)   # geometry only: no size attribute is ever received
                for f in fs:
                    f['attributes'] = {'year': yr}      # keep geometry + year only (no size attributes kept)
                allf += fs
        json.dump(allf, open(out, 'w'))
        print('mtbs perimeters', len(allf))


def ignitions():
    out = 'raw/fpafod_ignitions_blind.json'
    if os.path.exists(out):
        return
    lon0, lat0, lon1, lat1 = CFG['analysis_box_lonlat']
    url = 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0'
    feats = esri_query_all(url, fields=','.join(BLIND_FIELDS), geom=(lon0, lat0, lon1, lat1), in_sr=4326,
                           out_sr=5070, chunk=1000)
    for f in feats:  # F1 runtime guard
        bad = set(k.lower() for k in f['attributes']) & FORBIDDEN
        assert not bad, bad
    json.dump(feats, open(out, 'w'))
    print('ignitions (blind)', len(feats))


def erc():
    """gridMET daily ERC-G for the box, one netCDF3 file per year (parsed later with scipy.io.netcdf_file)."""
    os.makedirs('raw/erc', exist_ok=True)
    eb = CFG['erc_box']
    base = ('https://thredds.northwestknowledge.net/thredds/ncss/agg_met_erc_1979_CurrentYear_CONUS.nc'
            f"?var=daily_mean_energy_release_component-g&north={eb['north']}&south={eb['south']}&west={eb['west']}&east={eb['east']}"
            '&horizStride=1&accept=netcdf')
    for yr in range(1992, 2025):
        out = f'raw/erc/erc_{yr}.nc'
        if os.path.exists(out) and os.path.getsize(out) > 10000:
            continue
        b = fetch(base + f'&time_start={yr}-01-01T00:00:00Z&time_end={yr}-12-31T00:00:00Z', timeout=300)
        open(out, 'wb').write(b)
        print('erc', yr, len(b))


if __name__ == '__main__':
    steps = sys.argv[1:] or ['landfire', 'pcl', 'vectors', 'ignitions']
    for s in steps:
        t = time.time(); globals()[s](); print(f'{s} done in {time.time() - t:.0f}s', flush=True)
