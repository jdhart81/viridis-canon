from __future__ import annotations

import json
import struct
import unittest
from html.parser import HTMLParser
from pathlib import Path

from canon_core.catalog import build_catalog


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.local_assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        for attribute in ("href", "src", "content"):
            value = values.get(attribute) or ""
            if value.startswith("./"):
                self.local_assets.append(value)


class ResearchPortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = (DOCS / "index.html").read_text(encoding="utf-8")
        cls.app = (DOCS / "assets" / "app.js").read_text(encoding="utf-8")
        cls.parser = _PageParser()
        cls.parser.feed(cls.index)

    def test_landmark_ids_are_unique(self) -> None:
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))
        for expected in (
            "research-map",
            "research-graph",
            "graph-search",
            "research",
            "method",
            "institutions",
            "catalog-grid",
        ):
            self.assertIn(expected, self.parser.ids)

    def test_local_assets_exist(self) -> None:
        for reference in self.parser.local_assets:
            path = DOCS / reference.removeprefix("./").split("#", 1)[0]
            self.assertTrue(path.exists(), reference)

    def test_social_card_is_valid_landscape_png(self) -> None:
        data = (DOCS / "assets" / "og.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", data[16:24])
        self.assertGreaterEqual(width, 1200)
        self.assertGreaterEqual(height, 630)
        self.assertGreater(width, height)

    def test_checked_in_catalog_matches_source(self) -> None:
        actual = json.loads((DOCS / "data" / "catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, build_catalog(ROOT))

    def test_public_catalog_contains_no_local_absolute_paths(self) -> None:
        rendered = (DOCS / "data" / "catalog.json").read_text(encoding="utf-8")
        self.assertNotIn("/Users/", rendered)
        self.assertNotIn("/private/tmp/", rendered)
        self.assertNotIn("\\\\Users\\\\", rendered)

    def test_page_states_the_honesty_boundary(self) -> None:
        self.assertIn("does not manufacture empirical truth", self.index)
        self.assertIn("No autonomous minting", self.index)

    def test_external_validation_path_is_public_and_inspectable(self) -> None:
        self.assertIn("external-validation.yml", self.index)
        for relative in (
            "AI_USE_AND_AUTHORSHIP.md",
            "EXTERNAL_VALIDATION.md",
            "REPRODUCE.md",
            ".github/ISSUE_TEMPLATE/external-validation.yml",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)
        validation = (ROOT / "EXTERNAL_VALIDATION.md").read_text(encoding="utf-8")
        self.assertIn("Traffic", validation)
        self.assertIn("External validation", validation)
        self.assertIn("Institutional adoption", validation)

    def test_portal_exposes_abstract_reader_and_full_artifacts(self) -> None:
        self.assertIn("Abstract", self.app)
        self.assertIn("Read full research artifact", self.app)
        self.assertIn("Open paper", self.app)

    def test_portal_exposes_interactive_research_map(self) -> None:
        self.assertIn("living mind map", self.index)
        self.assertIn("renderResearchGraph", self.app)
        self.assertIn("filterResearchGraph", self.app)


if __name__ == "__main__":
    unittest.main()
