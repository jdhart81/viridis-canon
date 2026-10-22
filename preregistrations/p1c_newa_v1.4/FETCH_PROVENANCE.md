# P1C fetch provenance

This file records which code version fetched each input, and what was requested. Times are ET on 2026-10-20, taken from `raw/requests.log`. "Requests" counts its lines; the log records completed requests only, so failed attempts do not appear there but do appear in the fetch logs.

The fetch code changed during the session. Only the final `fetch_data.py` is frozen as a file. Every edit from 20:33 ET onward, with its exact text and timestamp, is in `logs/transcript_tool_calls_p1c.jsonl`. The changes are listed in time order below. Every change except two only altered how requests were split, retried or cached, which changes how many requests are made but not which records come back. The two exceptions are both marked **[content]**. Both narrowed what was requested, and neither widened it.

## Inputs and times

| Input | Window | Requests | Code state at the time |
|---|---|---|---|
| LANDFIRE LF2024 FBFM40 | 20:33:35–20:33:52 | 4 | pilot code; ERC box read from config |
| WA DNR PCL raster | 20:33:53–20:36:58 | 291 | pilot code |
| TIGER roads (3 layers) | 20:37:00–20:38:24 | 161 | pilot code |
| NHD Area, layer 9 | 20:39:29–20:41:41 | 3 | pilot code; fields `ftype,fcode`; all FTYPEs requested, filtered in the build |
| NHD Waterbody, layer 12 | 20:43:02–23:52:34 | 124 | see below |
| FPA FOD ignitions | 20:56:00–20:56:23 | 16 | outFields = the allow-list of 12 non-outcome fields, plus the runtime assertion that no outcome field is returned. Both are unchanged from the pilot. Requests split on failure (not needed) |
| gridMET ERC | 20:56:26–20:57:33 | 33 | pilot code; one netCDF per year |
| MTBS perimeters | 21:15:53–21:17:52 | 80 | **[content]** `fields='OBJECTID'`, geometry only. Attributes replaced by `{year}` before saving, as in the pilot |

## Code changes, in order

1. **About 20:51:** a failed batch of features is split in half and retried (`_query_ids`).
2. **About 20:55:** a timed-out id query is split into map quadrants (`_ids`).
3. **About 21:00, [content]:** NHD Waterbody requested with `ftype IN (390,436,378)`. These are the three FTYPEs the build uses, so the build's own filter, which still runs, gives the same features.
4. **21:15, [content]:** MTBS is requested with `fields='OBJECTID'` instead of `'*'`. This edit and the MTBS fetch ran in one command, one after the other. The command's log, `logs/tasks/bdqn7r65m.output`, shows the edit's "ok" line before "mtbs perimeters 262". The transcript extract records the command itself, at 01:15:50 UTC.
5. **About 21:22:** NHD Waterbody switched to a resumable, tile-by-tile fetch (`esri_query_cached`).
6. **About 21:34:** a failing tile is split into sub-tiles, a failing feature batch is halved, and the code asserts that the number of features equals the number of ids.

## NHD Waterbody attempts

- **20:43–20:46:** full layer, all FTYPEs. HTTP 504; nothing was saved.
- **20:51–21:15:** further full-box attempts, with change 3 from about 21:00. All failed with HTTP 504; nothing was saved.
- **21:24–23:52:** resumable attempts (`logs/fetch_vectors_try*.log`, `logs/chain*.log`). The fetch completed at 23:52 with 12,585 ids and 12,585 features.

## What touched outcome information

**FPA FOD fire size, size class or containment fields:**
- Never requested or received, for any record in this region. The confirmatory ignition fetch used the allow-list.
- `raw/fpafod_ignitions_blind.json` carries only those 12 fields (`CHECKS.txt` P1; `freeze.py` F2).

**MTBS attributes:**
- **In the pilot.** The pilot fetched MTBS at 19:53 and 20:06, before this region was chosen at about 20:33. It used `fields='*'`, which includes burned acreage, over the pilot's compute box. 63 of those 275 perimeters, 61 of them from 1992–2024, reach into this region. 1,697 of this region's ignitions lie inside the pilot's compute box.
- **What was kept.** The pilot code replaced every attribute record with `{year}` before saving. No attribute value was stored, printed or looked at.
- **In this region's fetch.** It requested geometry only.

**MTBS geometry:**
- The perimeter polygons on disk encode the burned area of every large fire (≥ 1,000 acres).
- They were used only as barriers in B+, and never linked to ignitions or measured for that purpose.
- The only computations on them were the count per year, the intersection counts above (63 and 61), and the S10b exclusion zone (`EXPOSURE_LISTS.json`).

## Evidence files

All are listed in `FREEZE.json`.

**Raw inputs:**
- `raw/fpafod_ignitions_blind.json`, `raw/mtbs_perims.json`, `raw/requests.log`;
- the predictor inputs: the LANDFIRE and PCL arrays, roads, NHD and the ERC files.

**Logs:**
- `logs/` holds every fetch, retry and chain log, plus `logs/run_chain_used_for_fetch.sh`, the script that ran the NHD retries.
- `logs/tasks/` holds the output of every background command in this session's working directory.
- `logs/transcript_tool_calls_p1c.jsonl` holds every command and code edit touching these files from 20:33 ET to the v1.2 freeze; `logs/transcript_tool_calls_p1c_part2.jsonl` continues it (the plan, §3, gives its coverage). `fetch_data.py` was not edited after 21:34.

**Pilot raw files:** `../p1/raw/mtbs_perims.json` and `../p1/raw/requests.log`. They give the 63/61/275 counts and the 19:53/20:06 fetch times.

`raw/requests.log` records each request's URL, up to 300 characters, but not the POST body. The fields requested are therefore documented by the code and the logs above.
