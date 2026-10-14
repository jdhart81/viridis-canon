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
import bz2
import gzip
import json
import lzma
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import urllib.parse
import urllib.request
import zipfile

STANDARD = "VRS-STANDALONE-MANUSCRIPT-PDF-1"
MAX_ARCHIVE_DEPTH = 3
MAX_MEMBER_BYTES = 200 * 1024 * 1024
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
ARCHIVE_SUFFIXES = (".zip", ".tar", ".gz", ".tgz", ".bz2", ".tbz2", ".tbz",
                    ".xz", ".txz", ".zst", ".zstd", ".tzst", ".7z", ".rar",
                    ".lz", ".lzma", ".cab", ".iso", ".ar")


class ManuscriptPDFHold(ValueError):
    pass


def _read(path: Path) -> bytes:
    # macOS system aliases /var and /tmp are not artifact-controlled links.
    if path.is_symlink() or not path.is_file() or any(p.is_symlink() and p not in {Path("/var"), Path("/tmp")} for p in path.parents):
        raise ManuscriptPDFHold("regular manuscript/reproduction file required")
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
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


def _archive_kind(raw: bytes) -> str | None:
    """Recognize containers by bytes, including archives with disguised names."""
    for magic, kind in ((b"PK\x03\x04", "zip"), (b"PK\x05\x06", "zip"),
                        (b"PK\x07\x08", "zip"), (b"\x1f\x8b", "gzip"),
                        (b"BZh", "bz2"), (b"\xfd7zXZ\x00", "xz"),
                        (b"\x28\xb5\x2f\xfd", "zstd")):
        if raw.startswith(magic):
            return kind
    # Valid ZIPs may carry an executable or other preamble. Their central
    # directory remains authoritative even when no ZIP signature is at byte 0.
    if zipfile.is_zipfile(BytesIO(raw)):
        return "zip"
    if len(raw) >= 512 and raw[257:262] == b"ustar":
        return "tar"
    if len(raw) >= 4 and 0x184D2A50 <= int.from_bytes(raw[:4], "little") <= 0x184D2A5F:
        return "zstd"
    # Old V7 TAR has a checksum field rather than a ustar marker.
    if len(raw) >= 512 and re.fullmatch(rb"[0-7\x00 ]{8}", raw[148:156]):
        try:
            with tarfile.open(fileobj=BytesIO(raw), mode="r:"):
                return "tar"
        except tarfile.TarError:
            pass
    if raw.startswith((b"7z\xbc\xaf\x27\x1c", b"Rar!\x1a\x07", b"!<arch>\n", b"MSCF")):
        return "unsupported"
    return None


class _ArchiveBudget:
    def __init__(self):
        self.expanded_bytes = 0

    def member(self, size: int) -> None:
        if not 0 <= size <= MAX_MEMBER_BYTES:
            raise ManuscriptPDFHold("reproduction archive member exceeds size limit")
        self.expanded_bytes += size
        if self.expanded_bytes > MAX_ARCHIVE_BYTES:
            raise ManuscriptPDFHold("reproduction archive exceeds total expanded size limit")


def _bounded_stream(stream, limit: int) -> bytes:
    data = stream.read(limit + 1)
    if len(data) > limit:
        raise ManuscriptPDFHold("reproduction archive expansion exceeds size limit")
    return data


def _decompress(raw: bytes, kind: str) -> bytes:
    """Bound codec expansion before allocating or inspecting its members."""
    if kind == "gzip":
        stream = gzip.GzipFile(fileobj=BytesIO(raw))
    elif kind == "bz2":
        stream = bz2.BZ2File(BytesIO(raw))
    elif kind == "xz":
        stream = lzma.LZMAFile(BytesIO(raw))
    else:
        try:
            from compression import zstd
            stream = zstd.ZstdFile(BytesIO(raw))
        except ImportError as exc:
            raise ManuscriptPDFHold("zstd reproduction archive inspection is unavailable") from exc
    with stream:
        return _bounded_stream(stream, MAX_ARCHIVE_BYTES)


def _archive_pdfs(path: Path, *, raw: bytes | None = None, budget=None):
    """Inspect bounded nested containers without extracting to the filesystem."""
    raw = _read(path) if raw is None else raw
    budget = budget or _ArchiveBudget()

    def scan(data, container, depth, prefix=""):
        if depth > MAX_ARCHIVE_DEPTH:
            raise ManuscriptPDFHold("reproduction archive exceeds nesting depth limit")
        kind = _archive_kind(data)
        if kind is None or kind == "unsupported":
            raise ManuscriptPDFHold("uninspectable reproduction archive: " + container)
        if kind in {"gzip", "bz2", "xz", "zstd"}:
            decoded = _decompress(data, kind)
            inner_kind = _archive_kind(decoded)
            if inner_kind is not None:
                # A compressed TAR/ZIP is one archive level; repeated codec
                # wrappers consume levels to prevent an unbounded codec stack.
                next_depth = depth + (inner_kind in {"gzip", "bz2", "xz", "zstd"})
                return scan(decoded, container, next_depth, prefix)
            name = re.sub(r"[.](?:gz|bz2|xz|zst|zstd)$", "", container, flags=re.I)
            if not name.lower().endswith(".pdf") and decoded.startswith(b"%PDF-"):
                name += ".pdf"
            if name == container or name.lower().endswith(ARCHIVE_SUFFIXES):
                raise ManuscriptPDFHold("uninspectable compressed reproduction member")
            budget.member(len(decoded))
            if _manuscript_source(name):
                raise ManuscriptPDFHold("compressed manuscript source requires a rendered PDF")
            return [(prefix + name, decoded)] if _archived_manuscript(name) else []

        seen = set(); sources = []; pdfs = []; nested = []

        def member(name):
            _safe_member(name)
            if name in seen:
                raise ManuscriptPDFHold("duplicate reproduction archive member")
            seen.add(name)

        def inspect(name, content):
            if _manuscript_source(name):
                sources.append(name)
            if _archived_manuscript(name):
                pdfs.append((name, content))
            nested_kind = _archive_kind(content)
            if nested_kind is not None or name.lower().endswith(ARCHIVE_SUFFIXES):
                nested.extend(scan(content, name, depth + 1, prefix + name + "!"))

        if kind == "zip":
            with zipfile.ZipFile(BytesIO(data)) as archive:
                for item in archive.infolist():
                    name = item.filename.rstrip("/") if item.is_dir() else item.filename
                    member(name)
                    if item.is_dir():
                        continue
                    mode = item.external_attr >> 16
                    if stat.S_IFMT(mode) not in {0, stat.S_IFREG}:
                        raise ManuscriptPDFHold("archived file must be a regular file")
                    budget.member(item.file_size)
                    with archive.open(item) as stream:
                        inspect(name, _bounded_stream(stream, min(item.file_size, MAX_MEMBER_BYTES)))
        else:
            with tarfile.open(fileobj=BytesIO(data), mode="r:") as archive:
                for item in archive:
                    name = item.name[2:] if item.name.startswith("./") else item.name
                    if name in {"", "."} and item.isdir():
                        continue
                    name = name.rstrip("/") if item.isdir() else name
                    member(name)
                    if item.isdir():
                        continue
                    if _manuscript_source(name) and not item.isfile():
                        raise ManuscriptPDFHold("archived manuscript source must be a regular file")
                    if _archived_manuscript(name) and not item.isfile():
                        raise ManuscriptPDFHold("archived manuscript must be a regular file")
                    if not item.isfile():
                        if name.lower().endswith(ARCHIVE_SUFFIXES):
                            raise ManuscriptPDFHold("nested archive must be a regular file")
                        continue
                    budget.member(item.size)
                    stream = archive.extractfile(item)
                    if stream is None:
                        raise ManuscriptPDFHold("archived file bytes missing")
                    with stream:
                        inspect(name, _bounded_stream(stream, min(item.size, MAX_MEMBER_BYTES)))
        pdf_names = {name.lower() for name, _ in pdfs}
        for name in sources:
            if str(PurePosixPath(name.lower()).with_suffix(".pdf")) not in pdf_names:
                raise ManuscriptPDFHold("archived manuscript source requires its corresponding rendered PDF in the approved release archive: " + container + ":" + name)
        return [(prefix + name, content) for name, content in pdfs] + nested

    try:
        yield from scan(raw, path.name, 1)
    except Exception as exc:
        if isinstance(exc, ManuscriptPDFHold):
            raise
        raise ManuscriptPDFHold("invalid or uninspectable reproduction archive") from exc


def require_local(bundle: Path, upload_paths=None, *, require_digest_inventory=True) -> dict:
    """Validate the actual future upload set, not merely files on disk."""
    bundle = Path(bundle)
    paths = [Path(p) for p in upload_paths] if upload_paths is not None else [p for p in bundle.iterdir() if p.is_file() and not p.name.startswith(".")]
    names = [p.name for p in paths]
    if len(set(names)) != len(names) or any(p.parent.resolve() != bundle.resolve() for p in paths):
        raise ManuscriptPDFHold("unique top-level upload files required")
    top = {}; upload_files = {}; upload_bytes = {}
    for path in paths:
        data = _read(path)
        upload_bytes[path.name] = data
        upload_files[path.name] = _hashes(data)
        if path.suffix.lower() == ".pdf":
            _pdf(data); top[path.name] = _hashes(data)
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
            roles = json.loads(upload_bytes[roles_path.name] if roles_path.name in upload_bytes else _read(roles_path))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ManuscriptPDFHold("valid manuscript role declaration required") from exc
        if not isinstance(roles, dict) or roles.get("standard") != STANDARD or not isinstance(roles.get("manuscripts"), list):
            raise ManuscriptPDFHold("exact manuscript role declaration required")
        for row in roles["manuscripts"]:
            if not isinstance(row, dict) or set(row) != {"filename", "sha256", "md5", "bytes"}:
                raise ManuscriptPDFHold("closed manuscript role binding required")
            if not isinstance(row["filename"], str) or row["filename"] in declared_names:
                raise ManuscriptPDFHold("unique manuscript role filename required")
            if row["filename"] not in top or top[row["filename"]] != {k: row[k] for k in ("sha256", "md5", "bytes")}:
                raise ManuscriptPDFHold("declared manuscript is not in actual uploads or its bytes differ")
            declared_names.add(row["filename"])
    if not declared_names and not any(_manuscript_name(name) for name in top):
        raise ManuscriptPDFHold("a figure PDF does not establish an actual manuscript; declare its exact manuscript role")
    members = {}; budget = _ArchiveBudget()
    for path in paths:
        if _archive_kind(upload_bytes[path.name]) is None and not path.name.lower().endswith(ARCHIVE_SUFFIXES):
            continue
        for name, data in _archive_pdfs(path, raw=upload_bytes[path.name], budget=budget):
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
            manifest = json.loads(upload_bytes[digest_path.name] if digest_path.name in upload_bytes else _read(digest_path))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ManuscriptPDFHold("valid digest manifest required") from exc
        if not isinstance(manifest, dict):
            raise ManuscriptPDFHold("valid digest manifest object required")
        notes = manifest.get("notes")
        if not isinstance(notes, list) or not notes:
            raise ManuscriptPDFHold("digest requires an exact note inventory")
        rows = []; seen = set(); used_filenames = set()
        uploads = manifest.get("uploads", [])
        if not isinstance(uploads, list) or any(not isinstance(v, dict) or not isinstance(v.get("filename"), str) for v in uploads):
            raise ManuscriptPDFHold("valid digest upload inventory required")
        uploaded = {v["filename"]: v for v in uploads}
        if len(uploaded) != len(uploads):
            raise ManuscriptPDFHold("unique digest upload filenames required")
        for note in notes:
            run = note.get("run_id") if isinstance(note, dict) else None
            if not isinstance(run, str) or not re.fullmatch(r"Run-[0-9]{3,}", run) or run in seen:
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
            note_uploads = note.get("uploads", [])
            if not isinstance(note_uploads, list):
                raise ManuscriptPDFHold("valid note upload inventory required")
            papers = [v for v in note_uploads if isinstance(v, dict) and v.get("filename") == "paper.pdf"]
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
            "upload_files": [{"filename": n, **v} for n, v in sorted(upload_files.items())],
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
    """Require the approved public set and anonymously hash every uploaded file."""
    if not isinstance(preflight, dict) or preflight.get("standard") != STANDARD or preflight.get("status") != "SEPARATE_MANUSCRIPT_PDF_PREFLIGHT_PASS":
        raise ManuscriptPDFHold("actual standalone manuscript preflight required")
    if not isinstance(record, dict):
        raise ManuscriptPDFHold("public record object required")
    record_id = str(record.get("id", ""))
    if not re.fullmatch(r"[1-9][0-9]*", record_id):
        raise ManuscriptPDFHold("public record identity required")
    files = record.get("files")
    if not isinstance(files, list) or any(not isinstance(f, dict) for f in files):
        raise ManuscriptPDFHold("public manuscript inventory required")
    names = [f.get("key") for f in files]
    if any(not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."} for name in names) or len(set(names)) != len(names):
        raise ManuscriptPDFHold("public manuscript names are duplicated")
    inventory = {f["key"]: f for f in files}
    approved = preflight.get("upload_files")
    if not isinstance(approved, list) or not approved:
        raise ManuscriptPDFHold("complete approved upload inventory required")
    for expected in approved:
        if (not isinstance(expected, dict) or set(expected) != {"filename", "sha256", "md5", "bytes"}
                or not isinstance(expected.get("filename"), str)
                or Path(expected["filename"]).name != expected["filename"]
                or not re.fullmatch(r"[a-f0-9]{64}", str(expected.get("sha256")))
                or not re.fullmatch(r"[a-f0-9]{32}", str(expected.get("md5")))
                or type(expected.get("bytes")) is not int or expected["bytes"] < 0):
            raise ManuscriptPDFHold("complete approved upload byte binding required")
    approved_names = [row["filename"] for row in approved]
    if len(set(approved_names)) != len(approved_names) or set(names) != set(approved_names):
        raise ManuscriptPDFHold("public file set differs from exact approved uploads")
    pdf_rows = preflight.get("top_level_pdfs")
    if (not isinstance(pdf_rows, list) or not pdf_rows
            or pdf_rows != [row for row in approved if Path(row["filename"]).suffix.lower() == ".pdf"]):
        raise ManuscriptPDFHold("standalone PDF bindings differ from approved uploads")
    verified = []; verified_pdfs = []
    for expected in approved:
        name = expected["filename"]; actual = inventory.get(name)
        if (actual is None or actual.get("size") != expected["bytes"]
                or actual.get("checksum") != "md5:" + expected["md5"]):
            raise ManuscriptPDFHold("public upload missing or changed: " + name)
        data = download(record_id, name)
        if not isinstance(data, bytes):
            raise ManuscriptPDFHold("public download did not return file bytes: " + name)
        if Path(name).suffix.lower() == ".pdf":
            _pdf(data)
        if _hashes(data) != {k: expected[k] for k in ("sha256", "md5", "bytes")}:
            raise ManuscriptPDFHold("downloaded upload differs from approved bytes: " + name)
        row = {**expected, "url": "https://zenodo.org/records/" + record_id + "/files/" + urllib.parse.quote(name, safe="")}
        verified.append(row)
        if Path(name).suffix.lower() == ".pdf":
            verified_pdfs.append(row)
    return {"standard": STANDARD, "status": "SEPARATE_MANUSCRIPT_PDF_PUBLIC_READBACK_PASS",
            "record_id": record_id, "pdfs": verified_pdfs, "upload_files": verified, "certifies": False}
