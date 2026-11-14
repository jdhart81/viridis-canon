"""The Canon overview and every other public surface agree with the files that hold the facts.

Invariants O1-O7 are stated in tools/build_overview.py; S1-S3 are stated on SurfaceTests.
Standard library only. The PDF check (O8) is a release-time check: it runs with CANON_RELEASE_CHECK=1
where pdftotext and Chrome are installed.
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "build_overview.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("build_overview", TOOL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _text(markup: str) -> str:
    """Visible text of an HTML page, whitespace collapsed."""
    body = re.sub(r"<(style|script)\b.*?</\1>", " ", markup, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))


class OverviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = _load_tool()
        cls.page = (ROOT / "docs" / "overview" / "index.html").read_text(encoding="utf-8")
        cls.text = _text(cls.page)
        cls.bounty_md = (ROOT / "BOUNTY.md").read_text(encoding="utf-8")

    def test_page_is_current(self):  # O7
        r = subprocess.run([sys.executable, str(TOOL), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_counts_come_from_the_certificate_index(self):  # O1
        k = json.loads((ROOT / "certificates" / "index.json").read_text(encoding="utf-8"))["counts"]
        self.assertIn(f"{k['runs']} runs, {k['theorems']} theorems", self.text)
        self.assertIn(f"{k['substantial']} runs labelled substantial, {k['elementary']} elementary", self.text)
        self.assertIn(f"main theorems of {k['runs']} results carry comparator certificates", self.text)

    def test_function_count_matches_formalization_yaml(self):  # O2
        n = len(re.findall(r"^  - id:", (ROOT / "formalization.yaml").read_text(encoding="utf-8"), re.M))
        self.assertGreater(n, 0)
        self.assertEqual(self.tool.function_count(), n)
        self.assertIn(f"{n} decision functions are now tied to Lean theorems", self.text)

    def test_bounty_status_follows_bounty_md(self):  # O3
        closed = "the cash bounty is closed to new reports" in self.bounty_md.lower()
        self.assertEqual(self.tool.bounty()["closed"], closed)
        for name, text in (("overview", self.text), ("Zenodo description", _text(self.tool.zenodo_description()))):
            if closed:
                self.assertIsNone(self.tool.CASH_OFFER.search(text), f"{name} offers cash; BOUNTY.md is closed")
                self.assertIn("closed to new reports", text, name)

    def test_cash_offer_pattern_catches_the_october_wording(self):  # O3: the check can fail
        october = ("We pay $50 for each confirmed vacuous, trivial or misstated theorem among the 18 certified "
                   "runs, up to $500 in total.")
        self.assertIsNotNone(self.tool.CASH_OFFER.search(october))
        self.assertIsNotNone(self.tool.CASH_OFFER.search("$50 for each confirmed theorem"))

    def test_every_ledger_row_is_on_the_overview(self):  # O4
        section = self.bounty_md.split("## Ledger", 1)[1]
        rows = [ln for ln in section.splitlines() if re.match(r"\| \d{4}-\d{2}-\d{2} \|", ln)]
        ledger = self.tool.bounty()["ledger"]
        self.assertEqual(len(ledger), len(rows), "a ledger row was not parsed")
        self.assertGreater(len(rows), 0)
        for row, entry in zip(rows, ledger):
            self.assertIn(f"issues/{entry['issue']}", row)
            for needle in (entry["date"], entry["run"], entry["theorem"], f"@{entry['reporter']}",
                           f"#{entry['issue']}"):
                self.assertIn(needle, self.text, f"ledger row missing from the overview: {needle}")
            self.assertIn(f'href="{self.tool.REPO}/issues/{entry["issue"]}"', self.page)
        self.assertIn(f"confirmed {len(rows)} finding", self.text)

    def test_results_share_one_source_with_the_result_pages(self):  # O5
        pages = self.tool.PAGES
        featured = {r["run"]: r for r in pages.RESULTS}
        for r in pages.RESULTS:
            page = _text((ROOT / "docs" / "results" / r["slug"] / "index.html").read_text(encoding="utf-8"))
            for fragment in r["math"]:
                want = _text(fragment)
                self.assertIn(want, self.text, r["slug"])
                self.assertIn(want, page, r["slug"])
        for entry in self.tool.bounty()["ledger"]:
            r = featured.get(entry["run"])
            if r is None:
                continue
            issues = {c["issue"] for c in r.get("corrections", [])}
            self.assertIn(entry["issue"], issues,
                          f"{entry['run']}: ledger finding #{entry['issue']} has no correction on the result")
            self.assertIn(f"Found by @{entry['reporter']}", self.text)

    def test_run_129_delay_bound_states_the_certified_hypotheses(self):  # O5, issue #121
        statement = (ROOT / "certificates" / "Run-129" / "VERIFICATION_STATEMENT.lean").read_text(encoding="utf-8")
        thm = statement.split("theorem bounded_overshoot_expected_delay", 1)[1].split(":= by", 1)[0]
        self.assertIn("|Z j ω| ≤ B", thm)       # the two-sided bound is in the certified statement
        self.assertIn("Integrable (fun ω => (N ω : ℝ)) μ", thm)
        for name, text in (("overview", self.text), ("result page", _text(
                (ROOT / "docs" / "results" / "anytime-change" / "index.html").read_text(encoding="utf-8")))):
            delay = text.split("Detection delay.", 1)[1][:400]
            self.assertIn("uniformly bounded (|Z j | ≤ B)", delay, name)
            self.assertIn("finite expectation", delay, name)
            self.assertNotIn("bounded above by z max with mean", delay, name)

    def test_uncertified_label_is_verbatim(self):  # O6
        label = ("UNCERTIFIED manuscript artifact. No issuer-produced Viridis Comparator certificate has been "
                 "shown to bind this public manuscript's exact bytes. Any linked certificate applies only to its "
                 "exact sealed artifacts and stated theorem scope. Results remain conditional on the declared "
                 "assumptions.")
        statuses = re.findall(r'<p class="status">(.*?)</p>', html.unescape(self.page), re.S)
        self.assertEqual(len(statuses), 1)
        self.assertTrue(statuses[0].startswith(f"{label} Working paper, not peer reviewed."))

    def test_bundle_holds_the_certificates_and_release_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.zip", Path(tmp) / "b.zip"
            self.tool.write_bundle(a)
            self.tool.write_bundle(b)
            self.assertEqual(a.read_bytes(), b.read_bytes(), "the bundle is not deterministic")
            names = set(zipfile.ZipFile(a).namelist())
        on_disk = {p.relative_to(ROOT).as_posix() for p in (ROOT / "certificates").rglob("*") if p.is_file()}
        self.assertEqual(names, on_disk | set(self.tool.BUNDLE_DOCS))

    @unittest.skipUnless(os.environ.get("CANON_RELEASE_CHECK") == "1" and shutil.which("pdftotext") and any(
        shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser", "chrome")),
        "release-time check: set CANON_RELEASE_CHECK=1; needs pdftotext and Chrome")
    def test_pdf_text_layer(self):  # O8
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "overview.pdf"
            self.tool.write_pdf(pdf)   # raises if the text layer fails its check
            self.assertEqual(self.tool.check_pdf(pdf), [])
            fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout
            self.assertNotIn("Type 3", fonts, "a Type 3 font loses characters when the text is copied")


class SurfaceTests(unittest.TestCase):
    """S1  While BOUNTY.md says the cash bounty is closed, no other public file offers cash.
    S2  The README's decision-function count equals formalization.yaml.
    S3  The README and CITATION.cff name the overview's version."""

    SURFACES = ("README.md", "AGENTS.md", "llms.txt", "RESPONSIBLE_RELEASE.md", "COMMUNITY_START_HERE.md",
                "CONTRIBUTING.md", "certificates/README.md", "os/README.md")

    @classmethod
    def setUpClass(cls):
        cls.tool = _load_tool()

    def _surfaces(self):
        files = [ROOT / s for s in self.SURFACES if (ROOT / s).exists()]
        files += sorted((ROOT / "docs").rglob("*.html"))
        files += sorted((ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.yml"))
        return files

    def test_no_surface_offers_cash_while_the_bounty_is_closed(self):  # S1
        if not self.tool.bounty()["closed"]:
            self.skipTest("the cash bounty is open")
        files = self._surfaces()
        self.assertGreater(len(files), 8)
        for p in files:
            text = _text(p.read_text(encoding="utf-8")) if p.suffix == ".html" else p.read_text(encoding="utf-8")
            m = self.tool.CASH_OFFER.search(text)
            self.assertIsNone(m, f"{p.relative_to(ROOT)} offers cash ({m.group(0) if m else ''}); BOUNTY.md is closed")

    def test_readme_function_count(self):  # S2
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        m = re.search(r"\| Decision functions tied to Lean theorems \| \*\*(\d+)\*\* \|", readme)
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(1)), self.tool.function_count())

    def test_version_is_the_same_everywhere(self):  # S3
        v = self.tool.VERSION
        self.assertIn(f'version: "{v}"', (ROOT / "CITATION.cff").read_text(encoding="utf-8"))
        self.assertIn(f"currently v{v}, git tag `canon-v{v}`", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn(f"version {v}", _text((ROOT / "docs" / "overview" / "index.html").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
