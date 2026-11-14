#!/usr/bin/env python3
"""Build the Canon overview: the front page of the Zenodo hub record, as HTML and PDF.

The overview is the first thing a reader of the hub record (concept DOI
10.5281/zenodo.19317982) opens. The October 2026 overview was written by hand and
went stale: it kept offering a cash bounty after BOUNTY.md closed it, and it kept a
delay bound whose scope an outside reader had corrected. This tool builds the
overview from the files that hold each fact, so a change to one of them shows up
here or fails the test.

Standard library only; deterministic (no clock reads).

Usage:
    python3 tools/build_overview.py                    # write docs/overview/index.html
    python3 tools/build_overview.py --check            # exit 1 if the page is stale
    python3 tools/build_overview.py --pdf OUT.pdf      # release time: render the PDF (needs Chrome/Chromium)
    python3 tools/build_overview.py --check-pdf F.pdf  # release time: check a PDF's text layer (needs pdftotext)
    python3 tools/build_overview.py --bundle OUT.zip   # release time: the certificates bundle for Zenodo
    python3 tools/build_overview.py --zenodo-description  # print the record description (HTML)

Invariants (enforced by tests/test_overview.py):
    O1  Certificate counts are read from certificates/index.json.
    O2  The decision-function count is the number of entries in formalization.yaml.
    O3  The bounty status is read from BOUNTY.md. While BOUNTY.md says the cash bounty
        is closed, neither the overview nor the Zenodo description offers cash.
    O4  Every row of the BOUNTY.md ledger appears in the overview (run, theorem,
        reporter, issue).
    O5  The three results are rendered from tools/build_results_pages.py RESULTS, so
        the overview and the result pages cannot disagree; every ledger finding on a
        featured run has a correction on that result naming the same issue.
    O6  The overview carries the approved UNCERTIFIED manuscript label verbatim.
    O7  docs/overview/index.html is current (--check).
    O8  (release time) The PDF's extracted text keeps the ORCID hyphens and the
        parentheses, names the release, and offers no cash while the bounty is closed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "overview" / "index.html"

# ---- release facts that no other file holds (edit these at each hub release) ----
VERSION = "2026.11.13"
RELEASE_NAME = "November 2026 release"
RELEASE_DATE_TEXT = "13 November 2026"
PREVIOUS_VERSION = "2026.10.17"
PREVIOUS_DOI = "10.5281/zenodo.23442570"
CONCEPT_DOI = "10.5281/zenodo.19317982"
PDF_NAME = "Viridis-Canon-November-2026-Overview.pdf"
BUNDLE_NAME = "viridis-canon-certificates-2026-11-13.zip"
ORCID_ID = "0009-0008-3082-2482"
# Files that travel with certificates/ in the bundle (the same seven as the October bundle).
BUNDLE_DOCS = ("formalization.yaml", "RESPONSIBLE_RELEASE.md", "AI_USE_AND_AUTHORSHIP.md",
               "BOUNTY.md", "CITATION.cff", "LICENSE", "README.md")
# Wording that offers money. Must not appear while the bounty is closed (O3, O8).
CASH_OFFER = re.compile(r"\bwe pay\b|\$\s?50 for each|up to \$\s?500", re.I)
CLOSED_MARK = "the cash bounty is closed to new reports"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


PAGES = _load("build_results_pages")
esc, REPO = PAGES.esc, PAGES.REPO


# ------------------------------------------------------------------ sources of fact
def certificate_counts() -> dict:
    return json.loads((ROOT / "certificates" / "index.json").read_text(encoding="utf-8"))["counts"]


def function_count() -> int:
    text = (ROOT / "formalization.yaml").read_text(encoding="utf-8")
    return len(re.findall(r"^  - id:", text, re.M))


def denominator() -> dict:
    """The engine denominator, from the table in RESPONSIBLE_RELEASE.md."""
    text = (ROOT / "RESPONSIBLE_RELEASE.md").read_text(encoding="utf-8")
    rows = dict(re.findall(r"^\| (Nightly research-engine runs to date|Runs submitted to the Comparator[^|]*|"
                           r"Runs issued a `LEAN_ZERO_SORRY_CERTIFIED` certificate) \| (\d+) \|$", text, re.M))
    out = {}
    for label, n in rows.items():
        key = "runs" if label.startswith("Nightly") else "submitted" if label.startswith("Runs submitted") else "certified"
        out[key] = int(n)
    if set(out) != {"runs", "submitted", "certified"}:
        raise SystemExit("RESPONSIBLE_RELEASE.md: the denominator table was not found")
    return out


def census() -> dict:
    ledgers = sorted((ROOT / "reports" / "compile_census").glob("ledger-*.json"))
    if not ledgers:
        raise SystemExit("reports/compile_census: no ledger found")
    d = json.loads(ledgers[-1].read_text(encoding="utf-8"))
    return {"date": ledgers[-1].stem.removeprefix("ledger-"), "files": d["files"], "clean": d["counts"]["CLEAN"],
            "declarations": d["declarations"], "theorems": d["theorems"]}


def bounty() -> dict:
    """Status and ledger, from BOUNTY.md."""
    text = (ROOT / "BOUNTY.md").read_text(encoding="utf-8")
    closed = CLOSED_MARK in text.lower()
    ledger = []
    section = text.split("## Ledger", 1)[1] if "## Ledger" in text else ""
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not re.match(r"\d{4}-\d{2}-\d{2}$", cells[0]):
            continue
        date, run, theorem, category, reporter, outcome = cells
        name = re.search(r"`([^`]+)`", theorem)
        label = re.search(r"\((C\d+)\)", theorem)
        who = re.search(r"@([A-Za-z0-9-]+)", reporter)
        issue = re.search(r"\[#(\d+)\]", reporter)
        if not (name and who and issue):
            raise SystemExit(f"BOUNTY.md: cannot read ledger row: {line[:80]}")
        cash = "$50 under the original terms" in outcome
        credit = "named credit in place of" in outcome
        ledger.append({"date": date, "run": run, "theorem": name.group(1).split(".")[-1],
                       "label": label.group(1) if label else "", "category": category,
                       "reporter": who.group(1), "issue": int(issue.group(1)),
                       "outcome": "Confirmed; $50" if cash else "Confirmed; named credit" if credit else "Confirmed"})
    return {"closed": closed, "ledger": ledger}


# ------------------------------------------------------------------ rendering
STATUS = (f"{PAGES.UNCERTIFIED_LABEL} Working paper, not peer reviewed. The main theorems of "
          "{runs} results carry comparator certificates (Lean 4; accepted by the Lean kernel and by the "
          "independent nanoda kernel). Results are conditional on their stated assumptions; the decision "
          "tools are not field-validated.")

CSS = """
:root{--fg:#1c2620;--muted:#55635a;--line:#d9ded6;--accent:#1f5c3d;--code:#f1f3ee;--warn:#7a5a12;--warnbg:#fbf3dc}
*{box-sizing:border-box}
body{margin:0;color:var(--fg);background:#fff;font:16px/1.55 'Liberation Serif','DejaVu Serif',Georgia,'Times New Roman',serif}
main{max-width:46rem;margin:0 auto;padding:1.5rem 16px 3rem}
h1{font-size:2.1rem;line-height:1.15;margin:0 0 .2rem;color:var(--accent)}
.sub{font-size:1.2rem;margin:0 0 .6rem;color:var(--accent)}
.by,.status,h2,table,.meta{font-family:'Liberation Sans','DejaVu Sans',Arial,Helvetica,sans-serif}
.by{font-size:.85rem;color:var(--muted);margin:0 0 1rem}
.status{font-size:.82rem;line-height:1.45;background:var(--warnbg);color:var(--warn);border-radius:6px;padding:.6rem .8rem}
h2{font-size:.95rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--accent);margin:1.6rem 0 .5rem;border-top:1px solid var(--line);padding-top:.9rem}
h3{font-size:1.25rem;line-height:1.25;margin:1.4rem 0 .3rem}
a{color:var(--accent)}
.question{font-style:italic}
ul{padding-left:1.2rem}li{margin:.3rem 0}
table{width:100%;border-collapse:collapse;font-size:.82rem;line-height:1.4}
td,th{border-bottom:1px solid var(--line);padding:.35rem .3rem;vertical-align:top;text-align:left}
td.n{text-align:right;white-space:nowrap;font-weight:700}
code,pre{font:.78rem/1.45 'Liberation Mono','DejaVu Sans Mono',Menlo,monospace;background:var(--code);border-radius:4px}
code{padding:.05rem .2rem;word-break:break-word}pre{padding:.6rem;white-space:pre-wrap;word-break:break-word}
.meta{font-size:.8rem;color:var(--muted)}
table.ledger td:nth-child(-n+2){white-space:nowrap}
.box{border:1px solid var(--line);border-radius:6px;padding:.1rem .8rem;margin:.8rem 0;background:#fafbf8}
@media print{main{max-width:none;padding:0}h2,h3{break-after:avoid}table,pre,.box,li{break-inside:avoid}a{text-decoration:none}}
@page{size:letter;margin:18mm 17mm}
"""


def _result_html(r: dict) -> str:
    fn = PAGES.load_function(r["series"])
    run = PAGES.load_run(r["run"])
    names = ", ".join(f"<code>{esc(t)}</code>" for t in run["theorems"])
    corr = "".join(f'<div class="box"><p>{c}</p></div>' for c in PAGES.correction_items(r))
    return f"""<h3>{esc(r['short_title'])}</h3>
<p class="question">{esc(r['question'])}</p>
{''.join(f'<p>{esc(p)}</p>' for p in r['answer'])}
<ul>
{''.join(f'<li>{m}</li>' for m in r['math'])}
</ul>
{corr}<p class="meta">Certified ({esc(r['run'])}, size label {esc(run['depth']['label'])}): {names}, plus
{len(run['nonvacuity_obligations'])} non-vacuity witnesses. Paper (UNCERTIFIED manuscript artifact):
<cite>{esc(r['paper_title'])}</cite>, DOI <a href="https://doi.org/{esc(fn['doi'])}">{esc(fn['doi'])}</a>.
Function: <code>{esc(fn['id'])}</code>. Plain-language page: <a href="{PAGES.page_url(r['slug'])}">{PAGES.page_url(r['slug'])}</a>.</p>
"""


def _review_html(b: dict) -> str:
    rows = "".join(
        f"<tr><td>{esc(e['date'])}</td><td>{esc(e['run'])}</td>"
        f"<td><code>{esc(e['theorem'])}</code>{' (' + esc(e['label']) + ')' if e['label'] else ''}</td>"
        f"<td>{esc(e['category'])}</td>"
        f"<td>@{esc(e['reporter'])} (<a href=\"{REPO}/issues/{e['issue']}\">#{e['issue']}</a>)</td>"
        f"<td>{esc(e['outcome'])}</td></tr>" for e in b["ledger"])
    n = len(b["ledger"])
    if b["closed"]:
        terms = ("The cash theorem bounty announced with the October release is closed to new reports. "
                 "Reports filed before it closed were reviewed under the terms they were filed under. "
                 "New confirmed findings earn named credit in the ledger, on the affected result page and "
                 "in the paper's next version; there is no cash award.")
    else:
        terms = "Terms for reporting a vacuous, trivial or misstated theorem are in BOUNTY.md in the repository."
    table = (f"<table class=\"ledger\"><thead><tr><th>Date</th><th>Run</th><th>Theorem</th><th>Finding</th><th>Reporter</th>"
             f"<th>Outcome</th></tr></thead><tbody>{rows}</tbody></table>") if n else ""
    return f"""<h2>Outside review</h2>
<p>A certificate cannot tell you whether a Lean statement says what the paper claims. Outside readers can.
So far they have confirmed {n} finding{'' if n == 1 else 's'} among the certified runs. Each one is credited
below and is fixed or relabelled.</p>
{table}
<p>{terms} How to report, how findings are judged and the full ledger:
<a href="{REPO}/blob/main/BOUNTY.md">BOUNTY.md</a>.</p>
"""


def _changes_html(b: dict) -> str:
    c = census()
    items = []
    if b["closed"]:
        items.append("The cash theorem bounty is closed to new reports; confirmed findings now earn named credit. "
                     f"{len(b['ledger'])} findings were confirmed and are listed under “Outside review”.")
    for r in PAGES.RESULTS:
        for corr in r.get("corrections", []):
            items.append(f"{esc(r['run'])}, <code>{esc(corr['theorem'])}</code>: the stated scope was corrected "
                         f"after an outside report (#{corr['issue']}). See the result below.")
    featured = {r["run"] for r in PAGES.RESULTS}
    for run in sorted({e["run"] for e in b["ledger"]} - featured):
        k = sum(1 for e in b["ledger"] if e["run"] == run)
        items.append(f"{esc(run)}, one of the certified runs, has {k} confirmed finding{'' if k == 1 else 's'}. "
                     "Its certified files stay as issued until it is re-certified with the repairs.")
    items.append(f"A compile census now compiles every Lean file in the repository on its own and audits its "
                 f"axioms, weekly and on every Lean change. The {esc(c['date'])} ledger covers {c['files']} files "
                 f"and {c['declarations']:,} declarations; {c['clean']} files are clean. The rest are listed with "
                 f"reasons in <code>reports/compile_census/</code>.")
    items.append(f"{function_count()} decision functions are now tied to Lean theorems in "
                 "<code>formalization.yaml</code>.")
    return (f"<h2>What changed since the October release</h2>\n<ul>\n"
            + "".join(f"<li>{i}</li>" for i in items) + "\n</ul>\n")


def render() -> str:
    k, d, b = certificate_counts(), denominator(), bounty()
    status = STATUS.replace("{runs}", str(k["runs"]))
    results = "".join(_result_html(r) for r in PAGES.RESULTS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Viridis Canon — {RELEASE_NAME}</title>
<meta name="description" content="Overview of the Viridis Canon {RELEASE_NAME}: machine-checked mathematics for ecological decisions, with certificate counts, three lead results, corrections and outside review.">
<meta name="author" content="Justin D. Hart">
<link rel="canonical" href="{PAGES.BASE}overview/">
<style>{CSS}</style>
</head>
<body>
<main>
<h1>Viridis Canon</h1>
<p class="sub">Machine-checked mathematics for ecological decisions — {RELEASE_NAME}</p>
<p class="by">Justin D. Hart · Viridis LLC · ORCID <a href="https://orcid.org/{ORCID_ID}">{ORCID_ID}</a> ·
{RELEASE_DATE_TEXT} · version {VERSION} · <a href="{REPO}">github.com/jdhart81/viridis-canon</a></p>
<p class="status">{esc(status)}</p>

<h2>What this is</h2>
<p>The Viridis Canon is an open research program that uses AI systems to propose and prove results about
decisions in ecology and conservation. Each result is released in three linked forms: Lean 4 proofs built
against a pinned Mathlib, a paper with a DOI, and a decision function you can run. The Git repository
<a href="{REPO}">github.com/jdhart81/viridis-canon</a> is where results are released and corrected; the
Zenodo record (concept DOI <a href="https://doi.org/{CONCEPT_DOI}">{CONCEPT_DOI}</a>) is the permanent,
citable snapshot. This overview replaces the October 2026 overview
(<a href="https://doi.org/{PREVIOUS_DOI}">{PREVIOUS_DOI}</a>).</p>

<h2>In numbers</h2>
<table><tbody>
<tr><td>Published with certificate bundles</td><td class="n">{k['runs']} runs, {k['theorems']} theorems</td><td>{k['substantial']} runs labelled substantial, {k['elementary']} elementary</td></tr>
<tr><td>Decision functions tied to Lean theorems</td><td class="n">{function_count()}</td><td>Listed in <code>formalization.yaml</code>; none is field-validated</td></tr>
<tr><td>Findings confirmed by outside readers</td><td class="n">{len(b['ledger'])}</td><td>Credited under “Outside review”</td></tr>
<tr><td>Engine runs</td><td class="n">{d['runs']}</td><td rowspan="3">Engine totals as published with the October 2026 release (<code>RESPONSIBLE_RELEASE.md</code>)</td></tr>
<tr><td>Submitted for certification</td><td class="n">{d['submitted']}</td></tr>
<tr><td>Certified</td><td class="n">{d['certified']}</td></tr>
</tbody></table>
<p class="meta">The size label is computed from the Lean source (at least 200 lines and a median proof of at
least six lines counts as substantial). It is a size indicator, not a judgement of novelty or importance.</p>

{_changes_html(b)}
<h2>Three results</h2>
{results}
<h2>What a certificate establishes, and what it does not</h2>
<p>The listed Lean theorems are proved in the solution file, their statements match the challenge file, they
use only the permitted axioms, and the Lean kernel and the nanoda kernel accept them. It does not establish
that the formal statement captures the paper's prose claim, that the model describes nature, that the result
is new, or that any decision built on it is correct.</p>

<h2>Check it yourself</h2>
<pre>git clone {REPO} &amp;&amp; cd viridis-canon
python3 certificates/verify_bundle.py         # every file still matches its certificate
certificates/rerun.sh Run-129 --axioms-only   # re-elaborate in Lean and audit the axioms
certificates/rerun.sh Run-129                 # full comparator check (needs comparator)</pre>
<p>The attached <code>{BUNDLE_NAME}</code> contains every certified run's challenge and solution files,
certificates, receipts and claim inventories, the verifier, the re-run script, <code>formalization.yaml</code>
and the release documents.</p>

{_review_html(b)}
<h2>Authorship and AI use</h2>
<p>Justin D. Hart is the accountable author of every result. The proofs are AI-generated and then
machine-checked. Tools and their roles: the Aristotle theorem prover (Harmonic) for automated Lean proofs;
OpenAI Codex for proof candidates, code and operations; Claude (Anthropic) for drafting, critique and review.
Tools are not authors. Details: <code>AI_USE_AND_AUTHORSHIP.md</code> and <code>RESPONSIBLE_RELEASE.md</code>.</p>

<h2>Earlier versions</h2>
<p>Version {PREVIOUS_VERSION} (<a href="https://doi.org/{PREVIOUS_DOI}">{PREVIOUS_DOI}</a>) is the October 2026
release; its overview offered the cash bounty that has since closed and stated the Run-129 delay bound without
the bounded-increment condition. Versions up to v10.2.0 bundled historical drafts and listed the Aristotle
prover among the creators. All earlier versions remain available as history.</p>
</main>
</body>
</html>
"""


def zenodo_description() -> str:
    """The record description for the hub release, from the same sources as the overview."""
    k, d, b = certificate_counts(), denominator(), bounty()
    lead = []
    for r in PAGES.RESULTS:
        fn = PAGES.load_function(r["series"])
        lead.append(f"<li><strong>{esc(r['short_title'])}</strong> {esc(r['abstract'])} "
                    f"<a href=\"https://doi.org/{esc(fn['doi'])}\">doi:{esc(fn['doi'])}</a>, certificate {esc(r['run'])}.</li>")
    n = len(b["ledger"])
    if b["closed"]:
        review = (f"<p><strong>Outside review.</strong> Outside readers have confirmed {n} findings among the "
                  "certified runs; each is credited in the overview and in BOUNTY.md and is fixed or relabelled. "
                  "The cash theorem bounty announced with the October release is closed to new reports; new "
                  "confirmed findings earn named credit.</p>")
    else:
        review = "<p><strong>Outside review.</strong> Reporting terms are in BOUNTY.md in the repository.</p>"
    return f"""<p><strong>Working paper, not peer reviewed.</strong> The main theorems of {k['runs']} results carry comparator certificates (Lean 4; accepted by the Lean kernel and by the independent nanoda kernel). Results are conditional on their stated assumptions; the decision tools are not field-validated. The linked papers are UNCERTIFIED manuscript artifacts: a certificate applies only to its sealed Lean files and stated theorem scope.</p>
<p>The Viridis Canon is machine-checked mathematics for ecological decisions. Each result is released as Lean 4 proofs against a pinned Mathlib, a paper with a DOI, and a decision function you can run. The Git repository <a href="{REPO}">github.com/jdhart81/viridis-canon</a> is where results are released and corrected; this record is the permanent, citable snapshot. Start with {PDF_NAME}.</p>
<p><strong>Three results</strong></p>
<ul>
{chr(10).join(lead)}
</ul>
<p><strong>In numbers.</strong> {k['runs']} runs published with certificate bundles ({k['theorems']} theorems; {k['substantial']} runs labelled substantial, {k['elementary']} elementary); {function_count()} decision functions tied to Lean theorems. Engine totals as published with the October 2026 release: {d['runs']} engine runs, {d['submitted']} submitted for certification, {d['certified']} certified.</p>
<p><strong>Changed since version {PREVIOUS_VERSION}.</strong> The overview is rebuilt from the repository's own records. It corrects the stated scope of the Run-129 detection-delay theorem (certified for uniformly bounded increments), credits the outside findings, and reports the weekly compile census of every Lean file.</p>
{review}
<p><strong>Check it yourself.</strong> <code>python3 certificates/verify_bundle.py</code> checks that every file still matches its certificate; <code>certificates/rerun.sh Run-129 --axioms-only</code> re-elaborates a run in Lean and audits its axioms. The attached certificates bundle holds every certified run's challenge and solution files, certificates and receipts, the verifier and the re-run script.</p>
<p><strong>Authorship.</strong> Justin D. Hart is the accountable author. The proofs are AI-generated and machine-checked. Tools used, which are not authors: the Aristotle prover (Harmonic), OpenAI Codex, and Claude (Anthropic); their roles are in AI_USE_AND_AUTHORSHIP.md. Earlier versions of this record remain available as history.</p>
"""


# ------------------------------------------------------------------ release-time helpers
def _chrome() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    raise SystemExit("no Chrome or Chromium found; install one to render the PDF")


def write_pdf(dest: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "overview.html"
        src.write_text(render(), encoding="utf-8")
        subprocess.run([_chrome(), "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={tmp}/profile", f"--print-to-pdf={dest}", src.as_uri()],
                       check=True, capture_output=True, timeout=180)
    problems = check_pdf(dest)
    if problems:
        dest.unlink(missing_ok=True)
        raise SystemExit("PDF failed its text-layer check:\n  " + "\n  ".join(problems))


def check_pdf(path: Path) -> list[str]:
    """O8. Return the problems found in the PDF's extracted text (empty list: none)."""
    text = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True,
                          text=True).stdout
    flat = re.sub(r"\s+", " ", text)
    k = certificate_counts()
    problems = []
    for needle in (ORCID_ID, "(Lean 4;", RELEASE_NAME, f"version {VERSION}",
                   f"{k['runs']} runs, {k['theorems']} theorems", "[μ − σ√((1−α)/α)]"):
        if needle not in flat:
            problems.append(f"missing from the text layer: {needle!r}")
    if bounty()["closed"]:
        m = CASH_OFFER.search(flat)
        if m:
            problems.append(f"offers cash while BOUNTY.md is closed: {m.group(0)!r}")
        if "closed to new reports" not in flat:
            problems.append("does not say the cash bounty is closed")
    return problems


def write_bundle(dest: Path) -> None:
    """certificates/ plus the release documents, in sorted order with fixed timestamps."""
    files = sorted(p for p in (ROOT / "certificates").rglob("*") if p.is_file())
    files += [ROOT / name for name in BUNDLE_DOCS]
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            info = zipfile.ZipInfo(p.relative_to(ROOT).as_posix(), date_time=(2026, 11, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if p.suffix == ".sh" else 0o644) << 16
            z.writestr(info, p.read_bytes())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--check-pdf", type=Path)
    ap.add_argument("--bundle", type=Path)
    ap.add_argument("--zenodo-description", action="store_true")
    args = ap.parse_args()
    if args.zenodo_description:
        sys.stdout.write(zenodo_description())
        return 0
    if args.check_pdf:
        problems = check_pdf(args.check_pdf)
        for p in problems:
            print("PDF:", p)
        print("overview PDF text layer:", "FAILED" if problems else "ok")
        return 1 if problems else 0
    if args.pdf:
        write_pdf(args.pdf)
        print("wrote", args.pdf)
        return 0
    if args.bundle:
        write_bundle(args.bundle)
        print("wrote", args.bundle)
        return 0
    text = render()
    stale = not OUT.exists() or OUT.read_text(encoding="utf-8") != text
    if args.check:
        print("overview:", "STALE" if stale else "up to date")
        return 1 if stale else 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
