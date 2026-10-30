#!/usr/bin/env python3
"""Build the citable result pages under docs/results/ (GitHub Pages).

Each page is plain, static HTML so that search engines and Google Scholar can read
it without running JavaScript. It carries Google Scholar (Highwire Press)
`citation_*` tags, ScholarlyArticle JSON-LD and a canonical URL, and explains the
result in plain language for practitioners.

Standard library only; deterministic (no clock reads).

Usage:
    python3 tools/build_results_pages.py          # write docs/results/** and docs/sitemap.xml
    python3 tools/build_results_pages.py --check  # exit 1 if any output is stale

Invariants (enforced by tests/test_results_pages.py):
    R1  Every page's citation_doi equals the DOI in its function manifest.
    R2  Every theorem a page lists is a certified theorem or witness of the run it names
        in certificates/index.json.
    R3  Every example on a page is the manifest's own example, whose expected output
        the test re-runs through the OS bundle.
    R4  Every page has the Scholar tags title, author, publication_date, doi,
        pdf_url and abstract_html_url, plus parseable ScholarlyArticle JSON-LD.
    R5  The sitemap lists every page and nothing else.
    R6  Science standard A1-A2 (labeling policy approved 2026-10-18): no certificate
        binds the exact bytes of a published paper PDF, so every page, its JSON-LD
        and its BibTeX label the paper an UNCERTIFIED manuscript artifact. The
        certificate is cited only for its sealed artifacts and theorem scope.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "results"
SITEMAP = ROOT / "docs" / "sitemap.xml"
BASE = "https://jdhart81.github.io/viridis-canon/"
REPO = "https://github.com/jdhart81/viridis-canon"
ORCID = "https://orcid.org/0009-0008-3082-2482"
LASTMOD = "2026-10-18"

# The approved label, verbatim. It is the same text the engine writes on Zenodo and the site shows.
UNCERTIFIED_LABEL = ("UNCERTIFIED manuscript artifact. No issuer-produced Viridis Comparator certificate has been "
                     "shown to bind this public manuscript's exact bytes. Any linked certificate applies only to its "
                     "exact sealed artifacts and stated theorem scope. Results remain conditional on the declared "
                     "assumptions.")
STATUS = (f"{UNCERTIFIED_LABEL} Working paper, not peer reviewed. The main theorems are machine-checked "
          "(comparator certificate, Lean and nanoda kernels); the decision tool is not field-validated.")
INDEX_STATUS = ("Each paper below is an UNCERTIFIED manuscript artifact: no issuer-produced Viridis Comparator "
                "certificate has been shown to bind its exact bytes. A certificate applies only to its exact sealed "
                "artifacts and stated theorem scope. Working papers, not peer reviewed. The main theorems are "
                "machine-checked; results are conditional on the declared assumptions, and the decision tools are "
                "not field-validated.")

RESULTS = [
    {
        "slug": "anytime-change",
        "series": "ACC",
        "short_title": "Anytime-valid change detection for ecological monitoring",
        "paper_title": ("The Anytime Change Certificate: False-alarm control, a late-change penalty, "
                        "and a bounded erasure budget for continuous monitoring"),
        "date": "2026-08-17",
        "record": "21971041",
        "run": "Run-129",
        "keywords": ["anytime-valid inference", "Ville's inequality", "change detection",
                     "test martingale", "ecological monitoring", "Lean 4", "machine-checked"],
        "abstract": ("A change detector for continuously monitored data whose false-alarm probability "
                     "stays at most α however long the data are watched, with a late-change evidence "
                     "penalty and a bound on expected detection delay. The main theorems, including "
                     "Ville's inequality for non-negative martingales, are machine-checked in Lean 4."),
        "question": ("Has this monitoring signal really changed? And if I re-check after every new "
                     "observation, for as long as the program runs, how do I keep false alarms under control?"),
        "answer": [
            "Monitoring programs look at data continuously. Re-running a classical test after every new "
            "count inflates the false-alarm rate. This result gives a monitor whose probability of ever "
            "raising a false alarm is at most α, however long you watch and however often you look.",
            "It also tells you what a late change costs (a log-sized evidence penalty) and bounds how "
            "long, on average, a real change takes to detect.",
        ],
        "math": [
            "<b>Ville's inequality.</b> For a non-negative martingale (M<sub>n</sub>) and c &gt; 0: "
            "P(∃n: M<sub>n</sub> ≥ c) ≤ E[M<sub>0</sub>]/c.",
            "<b>The monitor.</b> M<sub>n</sub> = A<sub>n</sub> + t<sub>n</sub>, with A<sub>0</sub> = 0, "
            "A<sub>n</sub> = Λ<sub>n</sub>(A<sub>n−1</sub> + π<sub>n</sub>), change-time prior "
            "π<sub>k</sub> = 1/(k(k+1)) and tail t<sub>n</sub> = 1/(n+1). Λ<sub>n</sub> is the likelihood "
            "ratio of observation n. Under the null it is a non-negative martingale with M<sub>0</sub> = 1.",
            "<b>Anytime false-alarm control.</b> P<sub>0</sub>(∃n: M<sub>n</sub> ≥ 1/α) ≤ α.",
            "<b>Late-change penalty.</b> The monitor dominates every embedded change-at-ν detector and "
            "alarms no later than it; the evidence boundary for a change at ν is "
            "log(1/α) + log(ν(ν+1)).",
            "<b>Detection delay.</b> If post-change log-likelihood increments are bounded above by "
            "z<sub>max</sub> with mean D &gt; 0, the first time the evidence sum reaches a satisfies "
            "a/D ≤ E[N<sub>a</sub>] &lt; (a + z<sub>max</sub>)/D.",
        ],
        "theorems": [
            ("anytime_change_mixture_martingale",
             "Under the declared null the monitor is a non-negative martingale with M₀ = 1 and mean 1 at every n."),
            ("anytime_change_ville_certificate",
             "P₀(the monitor ever reaches 1/α) ≤ α. Proved from Ville's inequality (`ville_inequality`)."),
            ("change_component_dominance_and_penalty",
             "The monitor dominates each change-at-ν component, alarms no later, and pays log(1/α) + log(ν(ν+1))."),
            ("bounded_overshoot_expected_delay",
             "a/D ≤ E[N_a] < (a + z_max)/D for the first crossing of level a."),
            ("c12_nonvacuous", "Witness: an iid Bernoulli(1/5) null on ℕ → Bool satisfies every hypothesis; the alarm event is neither empty nor null."),
            ("c2_sup_nonvacuous", "Witness for the supremum form of the certificate at the same instance."),
            ("c3_nonvacuous", "Witness: dominance is strict on an explicit path (alarm at 1 versus 2)."),
            ("c4_nonvacuous", "Witness: an explicit model where the delay corridor reads 5/2 ≤ 3 < 7/2."),
        ],
        "assumptions": [
            "The null is used only through E₀[Λₙ | past] = 1, with Λₙ non-negative, adapted and integrable.",
            "The runnable tool implements the single Bernoulli likelihood-ratio process of the paper; other data types need their own likelihood ratios.",
            "The paper's title also mentions an erasure budget. That physical reading is part of the paper's model, not of the certificate.",
            "Not field-validated: no monitoring program has used it yet.",
        ],
        "note_ville": ("We could not find Ville's inequality in Mathlib (checked master 74e558e on 2026-10-17) "
                       "and have offered to contribute it upstream."),
    },
    {
        "slug": "seed-supply-bottleneck",
        "series": "SSBC",
        "short_title": "Can a seed supply network meet restoration demand?",
        "paper_title": ("The Seed-Source Bottleneck Certificate: A cut condition for climate-aligned "
                        "afforestation supply networks"),
        "date": "2026-08-17",
        "record": "21971057",
        "run": "Run-130",
        "keywords": ["restoration", "native seed supply", "seed transfer zones", "max-flow min-cut",
                     "Hall's theorem", "decision support", "Lean 4", "machine-checked"],
        "abstract": ("Given seed sources with quantities, planting sites with demands and the allowed "
                     "source-to-site transfers, the largest share of every site's demand that can be met at "
                     "once equals a minimum cut ratio over site sets, and full supply is feasible exactly when "
                     "a capacitated Hall condition holds. The theorems are machine-checked in Lean 4."),
        "question": ("Can our seed sources meet every planting site's demand under our seed-transfer "
                     "rules? If not, which sites are the bottleneck, and will buying more seed help?"),
        "answer": [
            "Give the tool your seed lots (with quantities), your planting sites (with demand) and which "
            "lots may go to which sites, for example under climate-matched provenance rules. It returns "
            "the largest share of every site's demand you can meet at the same time, and the sites that "
            "limit it.",
            "Adding seed at a source that cannot reach the bottleneck sites cannot raise that share. "
            "Checking several climate scenarios together can only lower it, never raise it.",
            "Having as much seed in total as you need is not enough: the certified negative control shows "
            "total supply exactly equal to total demand while only a small fraction of every site's demand "
            "can be met.",
        ],
        "math": [
            "<b>Common fulfilment fraction.</b> θ* = min{1, min over non-empty site sets U of "
            "S(N(U)) / D(U)}, where N(U) is the set of sources allowed to serve some site in U, "
            "S is total supply and D is total demand. θ* is the largest feasible fraction.",
            "<b>Full supply.</b> Every site can be fully supplied if and only if D(U) ≤ S(N(U)) for every "
            "non-empty U (a capacitated Hall condition).",
            "<b>Bottleneck.</b> When θ* &lt; 1, increasing supply at a source outside N(U) for the active "
            "bottleneck U cannot increase θ*.",
            "<b>Scenarios.</b> The certificate for transfers allowed in every scenario is at most the "
            "certificate of each scenario.",
        ],
        "theorems": [
            ("seed_routing_common_fraction_eq_min_cut_ratio", "θ* is the greatest feasible common fulfilment fraction."),
            ("seed_routing_feasible_iff_cut_conditions", "Full supply is feasible exactly when every non-empty site set passes the cut condition."),
            ("capacity_outside_active_bottleneck_irrelevant", "More supply outside the active bottleneck cannot raise θ*."),
            ("scenario_intersection_certificate_le_each_scenario", "Requiring a transfer to be allowed in every scenario can only lower θ*."),
            ("C1_witness", "Witness: in the paper's two-site negative control the greatest feasible fraction is exactly 1/10."),
            ("C1_witness_nontrivial", "States 1/10 < 1, so that witness value is below full supply (a one-line arithmetic fact)."),
            ("C2_witness_infeasible", "Witness: in the negative control full supply is infeasible and the cut condition fails at the first site."),
            ("C2_witness_feasible", "Witness: with every transfer allowed, full supply is feasible and every cut condition holds."),
            ("C3_witness", "Witness: θ* < 1 at an explicit bottleneck; adding supply at a source outside it leaves θ* unchanged."),
            ("C4_witness", "Witness: two scenarios with θ* = 1 and 1/10; requiring both gives 1/10, while allowing either gives a falsely reassuring 1."),
            ("negative_control_arbitrarily_severe", "For any e in (0, 1], total supply can equal total demand while only a fraction e of every site's demand is achievable."),
        ],
        "assumptions": [
            "One period, continuous quantities, and a yes/no rule for which source may serve which site.",
            "Costs, timing, storage losses and germination are outside the model unless folded into the supply numbers.",
            "The underlying theorem is classical (Hall, Gale, max-flow/min-cut). What is new is a machine-checked statement for this decision, built from scratch because Mathlib has no capacitated Hall theorem.",
            "Not field-validated: no seed program has used it yet.",
        ],
    },
    {
        "slug": "precautionary-capacity",
        "series": "PCR",
        "short_title": "A precautionary capacity rule that is provably safe and provably tight",
        "paper_title": ("The Precautionary Capacity Reserve: A Sharp Moment-Robust Stewardship Discount "
                        "for an Intelligence-Rate Model"),
        "date": "2026-08-17",
        "record": "21971046",
        "run": "Run-127",
        "keywords": ["chance constraint", "Cantelli inequality", "distributional robustness",
                     "precautionary principle", "uncertainty reserve", "Lean 4", "machine-checked"],
        "abstract": ("Knowing only the mean and standard deviation of an uncertain capacity, planning against "
                     "the floor [μ − σ√((1−α)/α)]₊ keeps the probability that capacity falls short at most α "
                     "for every distribution; no mean-and-variance rule can do better, and a mean-only rule can "
                     "fail with probability arbitrarily close to 1. The theorems are machine-checked in Lean 4."),
        "question": ("If I only know the average and the spread of an uncertain capacity, how much can I "
                     "safely plan to use, with a guaranteed bound on the chance of falling short?"),
        "answer": [
            "Plan against the floor d = [μ − σ√((1−α)/α)]₊. Whatever the shape of the uncertainty (any "
            "non-negative distribution with mean μ and standard deviation σ), the chance that capacity "
            "falls below that floor is at most α.",
            "You cannot do better with the mean and variance alone: for any higher floor there is a "
            "two-point distribution that breaks the guarantee. Planning on the mean alone can fail with "
            "probability above any level below 1.",
        ],
        "math": [
            "<b>Two-moment floor.</b> d<sub>α</sub> = [μ − σ√((1−α)/α)]<sub>+</sub>, from Cantelli's "
            "one-sided inequality (proved here; Mathlib at our pinned revision has Chebyshev's but not "
            "Cantelli's).",
            "<b>Guarantee.</b> P(D &lt; d<sub>α</sub>) ≤ α for every non-negative capacity D with mean μ and "
            "standard deviation σ.",
            "<b>Sharpness.</b> For any d &gt; d<sub>α</sub> &gt; 0 there is a two-point law with the same mean "
            "and variance under which the violation probability exceeds α.",
            "<b>Mean-only rule.</b> For any β &lt; 1 there is a non-negative two-point law with mean μ under "
            "which planning on μ fails with probability above β.",
            "<b>In the paper's model</b> the certified rate is r<sub>α</sub> = P·d<sub>α</sub>/(k<sub>B</sub>T ln 2), "
            "and the reserve fraction is r<sub>α</sub>/r<sub>μ</sub> = [1 − CV·√((1−α)/α)]<sub>+</sub>.",
        ],
        "theorems": [
            ("cantelli_capacity_certificate", "The certified rate's violation probability is at most α."),
            ("precautionary_rate_le_violation_budget", "The certified rate needs exactly the floor d_α, and P(D < d_α) ≤ α."),
            ("capacity_reserve_fraction_eq", "Reserve fraction = [1 − CV·√((1−α)/α)]₊."),
            ("positive_floor_sharp_two_point_counterexample", "Any higher floor fails for some two-point law with the same moments."),
            ("mean_only_plugin_arbitrarily_unsafe", "A mean-only plan fails with probability above any β < 1 for some law."),
            ("cantelli_capacity_certificate_nonvacuous", "Witness: a law with mean 1 and standard deviation 1/2 at α = 1/2 has a positive floor and violation probability 4/13."),
            ("precautionary_rate_le_violation_budget_nonvacuous", "Witness for the violation-budget statement."),
            ("capacity_reserve_fraction_eq_nonvacuous", "Witness for the reserve-fraction identity."),
            ("positive_floor_sharp_two_point_counterexample_nonvacuous", "Witness for sharpness."),
            ("mean_only_plugin_arbitrarily_unsafe_nonvacuous", "Witness: a two-point law with mean 1 under which the mean-only plan fails with probability above 999/1000."),
        ],
        "assumptions": [
            "μ and σ are taken as known; estimation error in them is not covered.",
            "One period, one marginal distribution; no time dependence.",
            "The certified statements are written for the paper's information-rate model; the floor itself is Cantelli's bound and does not depend on that model.",
            "Not field-validated: no program has used it yet.",
        ],
    },
]

CSS = """
:root{--bg:#fbfaf6;--fg:#1c2620;--muted:#55635a;--line:#d9ded6;--accent:#1f5c3d;--code:#f1f3ee;--warn:#7a5a12;--warnbg:#fbf3dc}
@media (prefers-color-scheme:dark){:root{--bg:#121714;--fg:#e4ebe5;--muted:#a3b1a7;--line:#2c3630;--accent:#7fc79d;--code:#1b221e;--warn:#e6c46a;--warnbg:#2a2412}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 Georgia,'Iowan Old Style','Times New Roman',serif}
header,main,footer{max-width:46rem;margin:0 auto;padding:0 16px}
header{display:flex;gap:1rem;flex-wrap:wrap;align-items:baseline;padding-top:1.25rem;font:15px/1.4 system-ui,sans-serif}
header a{color:var(--accent);text-decoration:none}header .brand{font-weight:700;color:var(--fg)}
h1{font-size:1.9rem;line-height:1.2;margin:1.2rem 0 .4rem}
h2{font:600 1.05rem/1.3 system-ui,sans-serif;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:2rem 0 .6rem;border-top:1px solid var(--line);padding-top:1rem}
a{color:var(--accent)}
.status{font:14px/1.45 system-ui,sans-serif;background:var(--warnbg);color:var(--warn);border-radius:6px;padding:.6rem .8rem;margin-top:1rem}
.paper{font:15px/1.5 system-ui,sans-serif;color:var(--muted)}
.question{font-size:1.15rem;font-style:italic}
ul{padding-left:1.2rem}li{margin:.35rem 0}
table{width:100%;border-collapse:collapse;font:14px/1.45 system-ui,sans-serif}
td,th{border-bottom:1px solid var(--line);padding:.45rem .3rem;vertical-align:top;text-align:left}
code,pre{font:13px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);border-radius:4px}
code{padding:.05rem .25rem;word-break:break-word}pre{padding:.75rem;overflow-x:auto;white-space:pre-wrap;word-break:break-word}
.card{border:1px solid var(--line);border-radius:8px;padding:1rem;margin:1rem 0}
.card h3{margin:.1rem 0 .4rem;font-size:1.2rem}
footer{font:14px/1.5 system-ui,sans-serif;color:var(--muted);padding-bottom:3rem;margin-top:2.5rem;border-top:1px solid var(--line)}
"""


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def page_url(slug: str) -> str:
    return f"{BASE}results/{slug}/"


def load_function(series: str) -> dict:
    return json.loads((ROOT / "series" / series / "function.json").read_text(encoding="utf-8"))


def load_run(run: str) -> dict:
    ix = json.loads((ROOT / "certificates" / "index.json").read_text(encoding="utf-8"))
    return next(r for r in ix["runs"] if r["run"] == run)


def example_of(fn: dict) -> dict:
    ex = fn.get("examples") or fn.get("example")
    return ex[0] if isinstance(ex, list) else ex


def bibtex(r: dict, doi: str) -> str:
    key = "hart2026" + r["slug"].replace("-", "")
    return (f"@misc{{{key},\n  author    = {{Hart, Justin D.}},\n  title     = {{{r['paper_title']}}},\n"
            f"  year      = {{2026}},\n  publisher = {{Zenodo}},\n  doi       = {{{doi}}},\n"
            f"  note      = {{UNCERTIFIED manuscript artifact. Working paper. Main theorems machine-checked "
            f"(comparator certificate {r['run']}, scoped to its sealed artifacts)}}\n}}")


def render(r: dict) -> str:
    fn = load_function(r["series"])
    run = load_run(r["run"])
    doi = fn["doi"]
    url = page_url(r["slug"])
    pdf = f"https://zenodo.org/records/{r['record']}/files/paper.pdf"
    ex = example_of(fn)
    request = json.dumps({"id": fn["id"], "inputs": ex["inputs"]}, ensure_ascii=False)
    expected = json.dumps(ex["expected_outputs"], ensure_ascii=False, indent=1)
    jsonld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": r["paper_title"],
        "name": r["paper_title"],
        "author": {"@type": "Person", "name": "Justin D. Hart", "sameAs": ORCID,
                   "affiliation": {"@type": "Organization", "name": "Viridis LLC"}},
        "datePublished": r["date"],
        "identifier": {"@type": "PropertyValue", "propertyID": "DOI", "value": doi},
        "sameAs": f"https://doi.org/{doi}",
        "url": url,
        "abstract": r["abstract"],
        "keywords": r["keywords"],
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isBasedOn": f"{REPO}/tree/main/series/{r['series']}",
        "isPartOf": {"@type": "CreativeWork", "name": "Viridis Canon", "url": BASE},
        "creativeWorkStatus": (f"UNCERTIFIED manuscript artifact; working paper (not peer reviewed); main theorems "
                               f"machine-checked (comparator certificate {r['run']}, scoped to its sealed artifacts)"),
    }
    rows = "\n".join(f"<tr><td><code>{esc(n)}</code></td><td>{esc(g)}</td></tr>" for n, g in r["theorems"])
    depth = run["depth"]["label"]
    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(r['short_title'])} | Viridis Canon</title>
<meta name="description" content="{esc(r['abstract'])}">
<link rel="canonical" href="{url}">
<meta name="citation_title" content="{esc(r['paper_title'])}">
<meta name="citation_author" content="Hart, Justin D.">
<meta name="citation_author_institution" content="Viridis LLC">
<meta name="citation_author_orcid" content="{ORCID}">
<meta name="citation_publication_date" content="{r['date'].replace('-', '/')}">
<meta name="citation_online_date" content="{r['date'].replace('-', '/')}">
<meta name="citation_doi" content="{esc(doi)}">
<meta name="citation_pdf_url" content="{pdf}">
<meta name="citation_abstract_html_url" content="{url}">
<meta name="citation_technical_report_institution" content="Viridis LLC">
<meta name="citation_language" content="en">
<meta name="citation_keywords" content="{esc('; '.join(r['keywords']))}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(r['short_title'])}">
<meta property="og:description" content="{esc(r['abstract'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}assets/og.png">
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
<style>{CSS}</style>
</head>"""
    ville = f"<p>{esc(r['note_ville'])}</p>" if r.get("note_ville") else ""
    body = f"""
<body>
<header><a class="brand" href="../../">Viridis Canon</a><a href="../">Results</a><a href="{REPO}">Repository</a><a href="{REPO}/blob/main/BOUNTY.md">Theorem bounty</a></header>
<main>
<p class="status">{esc(STATUS)}</p>
<h1>{esc(r['short_title'])}</h1>
<p class="paper">Paper: <cite>{esc(r['paper_title'])}</cite>. Justin D. Hart, 2026.
DOI <a href="https://doi.org/{esc(doi)}">{esc(doi)}</a> · <a href="{pdf}">PDF</a> ·
<a href="{REPO}/tree/main/series/{r['series']}">Lean source</a> ·
<a href="{REPO}/tree/main/certificates/{r['run']}">certificate</a></p>

<h2>The question</h2>
<p class="question">{esc(r['question'])}</p>

<h2>The answer, in plain words</h2>
{''.join(f'<p>{esc(p)}</p>' for p in r['answer'])}

<h2>The mathematics</h2>
<ul>
{''.join(f'<li>{m}</li>' for m in r['math'])}
</ul>
{ville}

<h2>What is machine-checked</h2>
<p>Comparator certificate <a href="{REPO}/tree/main/certificates/{r['run']}"><code>{r['run']}</code></a>:
the statements below are proved with zero <code>sorry</code>, use only the axioms
<code>propext</code>, <code>Quot.sound</code> and <code>Classical.choice</code>, match a separate
challenge file, and are accepted by both the Lean kernel and the independent nanoda kernel
(Lean {esc(run['toolchain'].split(':')[-1])}, Mathlib <code>{esc(run['mathlib_rev'][:7])}</code>).
Size label: <b>{esc(depth)}</b>.</p>
<table><thead><tr><th>Lean theorem</th><th>What it says</th></tr></thead>
<tbody>
{rows}
</tbody></table>
<p>Check it yourself:</p>
<pre>git clone {REPO} &amp;&amp; cd viridis-canon
python3 certificates/verify_bundle.py                 # every file still matches its certificate (1 s)
certificates/rerun.sh {r['run']} --axioms-only            # re-elaborate in Lean and audit the axioms</pre>

<h2>Try it</h2>
<p>Run the decision function <code>{esc(fn['id'])}</code> with the Python standard library only:</p>
<pre>python3 -m canon_core build-os --out os-bundle
echo '{esc(request)}' | python3 os-bundle/run.py</pre>
<p>Expected output (from the function's manifest, re-checked in CI):</p>
<pre>{esc(expected)}</pre>
<p>AI agents can call the same function over MCP at <code>https://viridisconservation.com/api/viridisos/mcp</code>.</p>

<h2>Assumptions and limits</h2>
<ul>
{''.join(f'<li>{esc(a)}</li>' for a in r['assumptions'])}
</ul>

<h2>Cite</h2>
<pre>{esc(bibtex(r, doi))}</pre>
</main>
<footer>
<p>The proofs are AI-generated and machine-checked; Justin D. Hart (<a href="{ORCID}">ORCID</a>) is the accountable author.
Tools and their roles: <a href="{REPO}/blob/main/AI_USE_AND_AUTHORSHIP.md">AI_USE_AND_AUTHORSHIP.md</a>.
How we release: <a href="{REPO}/blob/main/RESPONSIBLE_RELEASE.md">RESPONSIBLE_RELEASE.md</a>.</p>
<p>Found a vacuous, trivial or misstated theorem among the certified runs? Confirmed findings are credited in the ledger and acknowledged in the papers. The cash bounty is closed to new reports (see the <a href="{REPO}/blob/main/BOUNTY.md">theorem bounty</a>).
Questions and challenges: <a href="{REPO}/discussions">Discussions</a>.</p>
</footer>
</body>
</html>
"""
    return head + body


def render_index() -> str:
    cards = []
    for r in RESULTS:
        fn = load_function(r["series"])
        cards.append(f"""<div class="card"><h3><a href="./{r['slug']}/">{esc(r['short_title'])}</a></h3>
<p>{esc(r['answer'][0])}</p>
<p class="paper">DOI <a href="https://doi.org/{esc(fn['doi'])}">{esc(fn['doi'])}</a> · certificate <code>{r['run']}</code> · function <code>{esc(fn['id'])}</code></p></div>""")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Results | Viridis Canon</title>
<meta name="description" content="Machine-checked results for ecological decisions: anytime-valid change detection, seed supply bottlenecks and precautionary capacity, each with a DOI, a Lean certificate and a runnable tool.">
<link rel="canonical" href="{BASE}results/">
<style>{CSS}</style>
</head>
<body>
<header><a class="brand" href="../">Viridis Canon</a><a href="{REPO}">Repository</a><a href="{REPO}/blob/main/BOUNTY.md">Theorem bounty</a></header>
<main>
<p class="status">{esc(INDEX_STATUS)}</p>
<h1>Results</h1>
<p>Each result answers a decision question in ecology or conservation, has a paper with a DOI,
a Lean 4 formalization with a comparator certificate you can re-run, and a decision function you can call.
These are the three we lead with; all 18 certified runs are listed in
<a href="{REPO}/tree/main/certificates">certificates/</a>.</p>
{''.join(cards)}
</main>
<footer><p>Justin D. Hart (<a href="{ORCID}">ORCID</a>), Viridis LLC. The proofs are AI-generated and machine-checked;
see <a href="{REPO}/blob/main/RESPONSIBLE_RELEASE.md">how we release</a>.</p></footer>
</body>
</html>
"""


def render_sitemap() -> str:
    urls = [f"{BASE}results/"] + [page_url(r["slug"]) for r in RESULTS]
    items = "".join(f"  <url><loc>{u}</loc><lastmod>{LASTMOD}</lastmod></url>\n" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + items + "</urlset>\n")


def outputs() -> dict[Path, str]:
    out = {OUT / "index.html": render_index(), SITEMAP: render_sitemap()}
    for r in RESULTS:
        out[OUT / r["slug"] / "index.html"] = render(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files = outputs()
    stale = [p for p, t in files.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
    if args.check:
        for p in stale:
            print("STALE:", p.relative_to(ROOT))
        print("results pages:", "STALE" if stale else "up to date")
        return 1 if stale else 0
    for p, t in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t, encoding="utf-8")
    print(f"wrote {len(files)} files ({len(RESULTS)} result pages, index, sitemap)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
