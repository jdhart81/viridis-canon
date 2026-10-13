"""Require independently openable manuscript PDFs, without changing science.

This packaging gate performs no authenticated request or external mutation.
Every manuscript PDF inside a public reproduction archive must have a byte-identical
top-level PDF. Figure PDFs do not establish a manuscript. Methods digests additionally bind every listed Run's paper to
its exact archive member and upload inventory; the digest summary is not a
substitute for those manuscripts.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import urllib.parse
import urllib.request
import zipfile

STANDARD = "VRS-STANDALONE-MANUSCRIPT-PDF-1"


class ManuscriptPDFHold(ValueError):
    pass


def _read(path: Path) -> bytes:
    # macOS system aliases /var and /tmp are not artifact-controlled links.
    if path.is_symlink() or not path.is_file() or any(p.is_symlink() and p not in {Path("/var"), Path("/tmp")} for p in path.parents):
        raise ManuscriptPDFHold("regular manuscript/reproduction file required")
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ManuscriptPDFHold("manuscript/reproduction file changed during read")
    return data


def _hashes(data: bytes) -> dict:
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "md5": hashlib.md5(data).hexdigest(), "bytes": len(data)}


def _pdf(data: bytes) -> None:
    if not data.startswith(b"%PDF-"):
        raise ManuscriptPDFHold("manuscript must contain actual PDF bytes")


def _safe_member(name: str) -> None:
    if (not name or "\\" in name or name.startswith("/")
            or any(p in {"", ".", ".."} for p in name.split("/"))
            or PurePosixPath(name).as_posix() != name):
        raise ManuscriptPDFHold("unsafe reproduction archive member")


def _manuscript_name(name: str) -> bool:
    basename = PurePosixPath(name).name.lower()
    return bool(re.search(r"(?:^|[-_ ])(?:paper|manuscript)(?:[-_ ].*)?[.]pdf$", basename))


def _archived_manuscript(name: str) -> bool:
    """Only an explicit figure role can exclude a PDF from the access gate.

    Descriptive names in papers/ and manuscripts/ are papers. Unknown PDF
    roles also require an accessible identical copy, so a summary cannot hide
    an unclassified manuscript. A paper role takes precedence over figures/.
    """
    path = PurePosixPath(name.lower())
    if path.suffix != ".pdf":
        return False
    if _manuscript_name(name) or any(p in {"papers", "manuscripts"} for p in path.parts[:-1]):
        return True
    figure = (any(p in {"figures", "plots"} for p in path.parts[:-1])
              or re.fullmatch(r"(?:fig(?:ure)?)[-_ ]?[0-9]*(?:[-_ ].*)?[.]pdf", path.name))
    return not figure


def _manuscript_source(name: str) -> bool:
    path = PurePosixPath(name.lower())
    # A descriptive Word-document name does not establish a non-paper role.
    # Its corresponding PDF is mandatory until separate reviewed routing
    # declares and admits a genuinely non-manuscript document exception.
    if path.suffix in {".docx", ".doc", ".odt"}:
        return True
    if path.suffix == ".tex":
        return _archived_manuscript(str(path.with_suffix(".pdf")))
    return (path.suffix in {".tex", ".md", ".docx", ".doc", ".odt"}
            and (_manuscript_name(str(path.with_suffix(".pdf")))
                 or any(p in {"papers", "manuscripts"} for p in path.parts[:-1])))


def _archive_pdfs(path: Path):
    """Inspect supported archive members without filesystem extraction."""
    raw = _read(path); seen = set(); sources = []; pdfs = []
    def member(name):
        _safe_member(name)
        if name in seen:
            raise ManuscriptPDFHold("duplicate reproduction archive member")
        seen.add(name)
    if path.name.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                for item in archive.infolist():
                    member(item.filename.rstrip("/") if item.is_dir() else item.filename)
                    if not item.is_dir() and _manuscript_source(item.filename):
                        sources.append(item.filename)
                    if not item.is_dir() and _archived_manuscript(item.filename):
                        pdfs.append((item.filename, archive.read(item)))
        except (zipfile.BadZipFile, RuntimeError) as exc:
            raise ManuscriptPDFHold("invalid reproduction archive") from exc
    else:
        try:
            with tarfile.open(fileobj=BytesIO(raw), mode="r:*") as archive:
                for item in archive:
                    name = item.name
                    # TAR writers commonly prefix own relative names with ./.
                    name = name[2:] if name.startswith("./") else name
                    if name in {"", "."} and item.isdir():
                        continue
                    member(name.rstrip("/") if item.isdir() else name)
                    if _manuscript_source(name):
                        if not item.isfile():
                            raise ManuscriptPDFHold("archived manuscript source must be a regular file")
                        sources.append(name)
                    if _archived_manuscript(name):
                        if not item.isfile():
                            raise ManuscriptPDFHold("archived manuscript must be a regular file")
                        stream = archive.extractfile(item)
                        if stream is None:
                            raise ManuscriptPDFHold("archived manuscript bytes missing")
                        pdfs.append((name, stream.read()))
        except tarfile.TarError as exc:
            raise ManuscriptPDFHold("invalid reproduction archive") from exc
    pdf_names = {name.lower() for name, _ in pdfs}
    for name in sources:
        if str(PurePosixPath(name.lower()).with_suffix(".pdf")) not in pdf_names:
            raise ManuscriptPDFHold("archived manuscript source requires its corresponding rendered PDF in the approved release archive: " + path.name + ":" + name)
    yield from pdfs


def require_local(bundle: Path, upload_paths=None, *, require_digest_inventory=True) -> dict:
    """Validate the actual future upload set, not merely files on disk."""
    bundle = Path(bundle)
    paths = list(upload_paths) if upload_paths is not None else [p for p in bundle.iterdir() if p.is_file() and not p.name.startswith(".")]
    names = [p.name for p in paths]
    if len(set(names)) != len(names) or any(p.parent.resolve() != bundle.resolve() for p in paths):
        raise ManuscriptPDFHold("unique top-level upload files required")
    top = {}
    for path in paths:
        if path.suffix.lower() == ".pdf":
            data = _read(path); _pdf(data); top[path.name] = _hashes(data)
    if not top:
        raise ManuscriptPDFHold("deposit requires at least one separate manuscript PDF")
    uploaded_pdf_names = {name.lower() for name in top}
    for path in paths:
        if (_manuscript_source(path.name)
                and str(PurePosixPath(path.name.lower()).with_suffix(".pdf")) not in uploaded_pdf_names):
            raise ManuscriptPDFHold("top-level manuscript source requires its corresponding same-stem PDF in actual uploads: " + path.name)
    declared_names = set()
    roles_path = bundle / "MANUSCRIPT_PDFS.json"
    if roles_path.is_file():
        try:
            roles = json.loads(_read(roles_path))
        except json.JSONDecodeError as exc:
            raise ManuscriptPDFHold("valid manuscript role declaration required") from exc
        if roles.get("standard") != STANDARD or not isinstance(roles.get("manuscripts"), list):
            raise ManuscriptPDFHold("exact manuscript role declaration required")
        for row in roles["manuscripts"]:
            if not isinstance(row, dict) or set(row) != {"filename", "sha256", "md5", "bytes"}:
                raise ManuscriptPDFHold("closed manuscript role binding required")
            if row["filename"] not in top or top[row["filename"]] != {k: row[k] for k in ("sha256", "md5", "bytes")}:
                raise ManuscriptPDFHold("declared manuscript is not in actual uploads or its bytes differ")
            declared_names.add(row["filename"])
    if not declared_names and not any(_manuscript_name(name) for name in top):
        raise ManuscriptPDFHold("a figure PDF does not establish an actual manuscript; declare its exact manuscript role")
    members = {}
    for path in paths:
        if not path.name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
            continue
        for name, data in _archive_pdfs(path):
            _pdf(data)
            matches = sorted(name for name, hashes in top.items() if hashes == _hashes(data))
            if not matches:
                raise ManuscriptPDFHold("archived manuscript lacks a byte-identical separate PDF: " + path.name + ":" + name)
            members[(path.name, name)] = {"archive": path.name, "member": name,
                "filename": matches[0], **_hashes(data)}
    digest_path = bundle / "DIGEST_MANIFEST.json"
    manuscripts = list(members.values())
    if digest_path.is_file():
        try:
            manifest = json.loads(_read(digest_path))
        except json.JSONDecodeError as exc:
            raise ManuscriptPDFHold("valid digest manifest required") from exc
        notes = manifest.get("notes")
        if not isinstance(notes, list) or not notes:
            raise ManuscriptPDFHold("digest requires an exact note inventory")
        rows = []; seen = set(); used_filenames = set()
        uploaded = {v.get("filename"): v for v in manifest.get("uploads", []) if isinstance(v, dict)}
        for note in notes:
            run = note.get("run_id") if isinstance(note, dict) else None
            if not isinstance(run, str) or not re.fullmatch(r"Run-[0-9]{3}", run) or run in seen:
                raise ManuscriptPDFHold("digest requires unique Run identities")
            seen.add(run)
            member = members.get(("METHODS_NOTES.zip", "notes/" + run + "/paper.pdf"))
            if member is None:
                raise ManuscriptPDFHold("listed note has no exact archived and separate manuscript PDF: " + run)
            choices = sorted(name for name, hashes in top.items()
                if hashes == {k: member[k] for k in ("sha256", "md5", "bytes")}
                and name.startswith(run + "-"))
            if not choices or choices[0] in used_filenames:
                raise ManuscriptPDFHold("each listed note requires its own Run-named standalone PDF: " + run)
            member = {**member, "filename": choices[0]}; used_filenames.add(choices[0])
            papers = [v for v in note.get("uploads", []) if isinstance(v, dict) and v.get("filename") == "paper.pdf"]
            if len(papers) != 1 or papers[0].get("sha256") != member["sha256"]:
                raise ManuscriptPDFHold("listed note manuscript hash differs from archive: " + run)
            if require_digest_inventory:
                row = uploaded.get(member["filename"])
                if row is None or any(row.get(k) != member[k] for k in ("sha256", "md5", "bytes")):
                    raise ManuscriptPDFHold("separate note PDF absent from approved digest upload inventory: " + run)
            rows.append({"run_id": run, **member})
        manuscripts = rows
    return {"standard": STANDARD, "status": "SEPARATE_MANUSCRIPT_PDF_PREFLIGHT_PASS",
            "manuscripts": sorted(manuscripts, key=lambda v: (v.get("run_id", ""), v["member"])),
            "top_level_pdfs": [{"filename": n, **v} for n, v in sorted(top.items())],
            "external_mutation": False, "certifies": False}


def _public_bytes(url: str) -> bytes:
    class OwnRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, response, code, message, headers, newurl):
            target = urllib.parse.urlsplit(newurl)
            if target.scheme != "https" or target.netloc != "zenodo.org" or target.query or target.fragment:
                raise ManuscriptPDFHold("public manuscript download left configured Zenodo host")
            return super().redirect_request(request, response, code, message, headers, newurl)
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.build_opener(OwnRedirect()).open(request, timeout=90) as response:
        return response.read()


def public_record(record_id: str) -> dict:
    if not re.fullmatch(r"[1-9][0-9]*", str(record_id)):
        raise ManuscriptPDFHold("own record required")
    result = json.loads(_public_bytes("https://zenodo.org/api/records/" + str(record_id)))
    if not isinstance(result, dict) or str(result.get("id")) != str(record_id):
        raise ManuscriptPDFHold("public manuscript record identity differs")
    return result


def public_pdf_bytes(record_id: str, filename: str) -> bytes:
    if not re.fullmatch(r"[1-9][0-9]*", str(record_id)) or Path(filename).name != filename:
        raise ManuscriptPDFHold("own record and PDF basename required")
    url = "https://zenodo.org/api/records/" + str(record_id) + "/files/" + urllib.parse.quote(filename, safe="") + "/content"
    return _public_bytes(url)


def require_public(record: dict, preflight: dict, *, download=public_pdf_bytes) -> dict:
    """Download every standalone PDF anonymously and compare exact bytes."""
    if preflight.get("standard") != STANDARD or preflight.get("status") != "SEPARATE_MANUSCRIPT_PDF_PREFLIGHT_PASS":
        raise ManuscriptPDFHold("actual standalone manuscript preflight required")
    record_id = str(record.get("id", ""))
    if not re.fullmatch(r"[1-9][0-9]*", record_id):
        raise ManuscriptPDFHold("public record identity required")
    files = record.get("files")
    if not isinstance(files, list) or any(not isinstance(f, dict) for f in files):
        raise ManuscriptPDFHold("public manuscript inventory required")
    names = [f.get("key") for f in files]
    if len(set(names)) != len(names):
        raise ManuscriptPDFHold("public manuscript names are duplicated")
    inventory = {f["key"]: f for f in files}
    verified = []
    for expected in preflight["top_level_pdfs"]:
        name = expected["filename"]; actual = inventory.get(name)
        if (actual is None or actual.get("size") != expected["bytes"]
                or actual.get("checksum") != "md5:" + expected["md5"]):
            raise ManuscriptPDFHold("separate public manuscript missing or changed: " + name)
        data = download(record_id, name); _pdf(data)
        if _hashes(data) != {k: expected[k] for k in ("sha256", "md5", "bytes")}:
            raise ManuscriptPDFHold("downloaded manuscript differs from approved PDF: " + name)
        verified.append({**expected, "url": "https://zenodo.org/records/" + record_id + "/files/" + urllib.parse.quote(name, safe="")})
    return {"standard": STANDARD, "status": "SEPARATE_MANUSCRIPT_PDF_PUBLIC_READBACK_PASS",
            "record_id": record_id, "pdfs": verified, "certifies": False}
