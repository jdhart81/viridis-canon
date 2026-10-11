"""Read-only, reproducible prior-art indices. Never builds Lean or admits evidence."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import tarfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n"


def mathlib_index(archive, revision):
    items = []
    total = 0
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            parts = member.name.split("/", 1)
            if parts[0] != "mathlib4-" + revision:
                raise ValueError("Official archive root does not match the exact upstream commit")
            if len(parts) != 2 or not parts[1].startswith("Mathlib/") or not parts[1].endswith(".lean"):
                continue
            if not member.isfile() or member.size > 4_000_000:
                raise ValueError("Non-regular or oversized Mathlib source")
            source = tar.extractfile(member).read()
            total += len(source)
            if total > 250_000_000:
                raise ValueError("Mathlib source cap exceeded")
            path = parts[1]
            items.append({"title": path, "path": path,
                          "url": f"https://github.com/leanprover-community/mathlib4/blob/{revision}/{path}",
                          "text": source.decode("utf-8"), "content_sha256": sha(source), "text_sha256": sha(source)})
    if not items:
        raise ValueError("Empty official Mathlib snapshot")
    return {"schema_version": 1, "source": "mathlib", "snapshot": {
        "complete": True, "revision": revision,
        "description": "All Mathlib/**/*.lean source files in the exact official upstream commit; advisory prior art only. Certification pin is unchanged.",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "archive_sha256": sha(Path(archive).read_bytes()), "files": len(items), "source_bytes": total,
        "certification_pin_unchanged": "8f9d9cff6bd728b17a24e163c9402775d9e6a365"}, "items": items}


def canon_index(root, catalog):
    root = Path(root)
    catalog = Path(catalog)
    data = catalog.read_bytes()
    obj = json.loads(data)
    items, bindings = [], [{"path": str(catalog.resolve()), "sha256": sha(data)}]
    for record in obj.get("records", []):
        text = json.dumps(record, ensure_ascii=False, sort_keys=True)
        link = (record.get("url") or record.get("zenodo_url") or record.get("external_url")
                or record.get("source_url") or record.get("paper_url"))
        doi = record.get("doi")
        if not link:
            identity = record.get("id") or record.get("title") or sha(text.encode())
            from urllib.parse import quote
            link = "https://doi.org/" + doi if doi else "https://jdhart81.github.io/viridis-canon/#" + quote(str(identity), safe="")
        items.append({"title": record.get("title", record.get("id", "Canon record")), "url": link,
                      "text": text, "content_sha256": sha(text.encode()), "text_sha256": sha(text.encode())})
    for group in obj.get("methods_digests", []):
        text = json.dumps(group, ensure_ascii=False, sort_keys=True)
        locators = [note.get("run_id", note.get("entity_id", "")) for note in group.get("notes", [])]
        items.append({"title": "Published Methods Digest " + group["doi"] + ": " + ", ".join(locators),
                      "url": "https://doi.org/" + group["doi"], "text": text,
                      "content_sha256": sha(text.encode()), "text_sha256": sha(text.encode())})
    mirror = root / "science-engine/07_nightly_engine/compound research papers"
    papers = sorted(mirror.glob("Run-*/paper.tex"))
    for paper in papers:
        if paper.is_symlink():
            raise ValueError("Symlink in own prior-art corpus")
        source = paper.read_bytes()
        bindings.append({"path": str(paper), "sha256": sha(source)})
        items.append({"title": paper.parent.name, "url": paper.as_uri(), "path": str(paper),
                      "text": source.decode("utf-8"), "content_sha256": sha(source), "text_sha256": sha(source)})
    if not papers or not obj.get("records") or not obj.get("methods_digests"):
        raise ValueError("Missing canonical prior-art source")
    ledger = root / "RESEARCH_PIPELINE_v2/corpus_ledger.json"
    if ledger.exists():
        bindings.append({"path": str(ledger), "sha256": sha(ledger.read_bytes())})
    revision = sha(raw(bindings))
    return {"schema_version": 1, "source": "canon", "snapshot": {
        "complete": True, "revision": revision,
        "description": "Entire current public catalog, every Methods Digest exact note scope, and all mirrored nightly paper.tex files. Includes uncertified historical claims as prior descriptions, never as verification evidence. Historical CANON_MAP is not admission authority.",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "catalog_sha256": sha(data), "catalog_digest": obj.get("catalog_digest"),
        "mirror_papers": len(papers), "bindings": bindings}, "items": items}


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = raw(value)
    with path.open("xb") as output:
        output.write(data)
    return {"path": str(path), "sha256": sha(data), "bytes": len(data), "items": len(value["items"])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kind", choices=("all", "canon", "mathlib"), default="all")
    p.add_argument("--root", type=Path)
    p.add_argument("--catalog", type=Path)
    p.add_argument("--mathlib-archive", type=Path)
    p.add_argument("--mathlib-revision")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = {}
    if a.kind in {"all", "mathlib"}:
        if not a.mathlib_archive or not a.mathlib_revision or len(a.mathlib_revision) != 40 or any(c not in "0123456789abcdef" for c in a.mathlib_revision):
            p.error("Exact upstream commit and archive required")
        result["mathlib"] = write_new(a.out / "mathlib.json", mathlib_index(a.mathlib_archive, a.mathlib_revision))
    if a.kind in {"all", "canon"}:
        if not a.root or not a.catalog:
            p.error("Canonical root and catalog required")
        result["canon"] = write_new(a.out / "canon.json", canon_index(a.root, a.catalog))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
