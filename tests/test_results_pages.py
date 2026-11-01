"""The citable result pages stay current, truthful and readable by Google Scholar.

Invariants R1-R5 are stated in tools/build_results_pages.py. Standard library only.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "build_results_pages.py"
REQUIRED_TAGS = ("citation_title", "citation_author", "citation_publication_date",
                 "citation_doi", "citation_pdf_url", "citation_abstract_html_url")


def _load_tool():
    spec = importlib.util.spec_from_file_location("build_results_pages", TOOL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class _Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta: dict[str, list[str]] = {}
        self.jsonld: list[str] = []
        self._in_ld = False
        self.canonical = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and "name" in a:
            self.meta.setdefault(a["name"], []).append(a.get("content") or "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
            self.jsonld.append("")

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_ld = False

    def handle_data(self, data):
        if self._in_ld:
            self.jsonld[-1] += data


class ResultsPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = _load_tool()
        cls.index = json.loads((ROOT / "certificates" / "index.json").read_text(encoding="utf-8"))

    def _page(self, slug):
        p = _Meta()
        p.feed((ROOT / "docs" / "results" / slug / "index.html").read_text(encoding="utf-8"))
        return p

    def test_pages_are_current(self):
        r = subprocess.run([sys.executable, str(TOOL), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_scholar_tags_and_jsonld(self):  # R1, R4
        for res in self.tool.RESULTS:
            page = self._page(res["slug"])
            for tag in REQUIRED_TAGS:
                self.assertTrue(page.meta.get(tag) and page.meta[tag][0].strip(), f"{res['slug']}: {tag}")
            fn = json.loads((ROOT / "series" / res["series"] / "function.json").read_text(encoding="utf-8"))
            self.assertEqual(page.meta["citation_doi"][0], fn["doi"], res["slug"])
            self.assertRegex(page.meta["citation_publication_date"][0], r"^\d{4}/\d{2}/\d{2}$")
            self.assertIn(f"/records/{res['record']}/", page.meta["citation_pdf_url"][0])
            self.assertTrue(fn["doi"].endswith(res["record"]), res["slug"])
            self.assertEqual(page.canonical, page.meta["citation_abstract_html_url"][0])
            self.assertEqual(len(page.jsonld), 1, res["slug"])
            ld = json.loads(page.jsonld[0])
            self.assertEqual(ld["@type"], "ScholarlyArticle")
            self.assertEqual(ld["identifier"]["value"], fn["doi"])
            self.assertEqual(ld["author"]["sameAs"], "https://orcid.org/0009-0008-3082-2482")

    def test_listed_theorems_are_certified(self):  # R2
        for res in self.tool.RESULTS:
            run = next(r for r in self.index["runs"] if r["run"] == res["run"])
            certified = set(run["theorems"]) | set(run["nonvacuity_obligations"])
            listed = {name for name, _ in res["theorems"]}
            self.assertTrue(listed <= certified, f"{res['run']}: not certified: {sorted(listed - certified)}")
            self.assertTrue(set(run["theorems"]) <= listed, f"{res['run']}: main theorem missing from page")

    def test_examples_match_the_function(self):  # R3
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, "-m", "canon_core", "build-os", "--out", tmp],
                           cwd=ROOT, check=True, capture_output=True)
            for res in self.tool.RESULTS:
                fn = json.loads((ROOT / "series" / res["series"] / "function.json").read_text(encoding="utf-8"))
                ex = self.tool.example_of(fn)
                req = json.dumps({"id": fn["id"], "inputs": ex["inputs"]})
                out = subprocess.run([sys.executable, "-I", "-B", "run.py"], input=req, capture_output=True,
                                     text=True, cwd=tmp, check=True)
                got = json.loads(out.stdout)
                self.assertTrue(got.get("ok"), out.stdout)
                for k, v in ex["expected_outputs"].items():
                    g = got["output"].get(k)
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and isinstance(g, (int, float)):
                        self.assertAlmostEqual(g, v, places=9, msg=f"{fn['id']}.{k}")
                    else:
                        self.assertEqual(g, v, f"{fn['id']}.{k}")
                html_text = (ROOT / "docs" / "results" / res["slug"] / "index.html").read_text(encoding="utf-8")
                self.assertIn(fn["id"], html_text)

    def test_sitemap_lists_exactly_the_pages(self):  # R5
        locs = re.findall(r"<loc>([^<]+)</loc>", (ROOT / "docs" / "sitemap.xml").read_text(encoding="utf-8"))
        expected = [f"{self.tool.BASE}results/"] + [self.tool.page_url(r["slug"]) for r in self.tool.RESULTS]
        self.assertEqual(locs, expected)

    def test_papers_carry_the_uncertified_label(self):  # R6
        # The approved label, written out independently of the tool.
        label = ("UNCERTIFIED manuscript artifact. No issuer-produced Viridis Comparator certificate has been "
                 "shown to bind this public manuscript's exact bytes. Any linked certificate applies only to its "
                 "exact sealed artifacts and stated theorem scope. Results remain conditional on the declared "
                 "assumptions.")
        for res in self.tool.RESULTS:
            text = html.unescape((ROOT / "docs" / "results" / res["slug"] / "index.html").read_text(encoding="utf-8"))
            statuses = re.findall(r'<p class="status">(.*?)</p>', text, re.S)
            self.assertEqual(len(statuses), 1, res["slug"])
            self.assertTrue(statuses[0].startswith(f"{label} Working paper, not peer reviewed."), res["slug"])
            ld = json.loads(self._page(res["slug"]).jsonld[0])
            self.assertTrue(ld["creativeWorkStatus"].startswith("UNCERTIFIED manuscript artifact;"), res["slug"])
            self.assertIn(f"scoped to its sealed artifacts", ld["creativeWorkStatus"])
            self.assertIn("note      = {UNCERTIFIED manuscript artifact.", text, res["slug"])
        index = html.unescape((ROOT / "docs" / "results" / "index.html").read_text(encoding="utf-8"))
        self.assertIn('<p class="status">Each paper below is an UNCERTIFIED manuscript artifact', index)

    def test_no_overclaiming_words(self):
        bad = re.compile(r"\b(field[- ]validated and|peer[- ]reviewed and|proven in the field|guaranteed in practice)\b", re.I)
        for res in self.tool.RESULTS:
            text = (ROOT / "docs" / "results" / res["slug"] / "index.html").read_text(encoding="utf-8")
            self.assertIsNone(bad.search(text), res["slug"])
            self.assertIn("not field-validated", text.lower().replace("not field validated", "not field-validated"))


if __name__ == "__main__":
    unittest.main()
