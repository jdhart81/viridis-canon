"""Forward-only premise gate proposal; never author proof or rewrite a seal.

The live Codex builders and Core preseal writer are outside this repository.
The companion review patches connect this guard to those boundaries; this file
alone is not an installed generation fix. The INV-9 sources remain unchanged.
"""
from __future__ import annotations

import builtins
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import types

BASES = frozenset({"THEOREM", "CONDITIONAL_PL_PD", "INDEPENDENT"})
PREMISE_SHA256 = "e00404ad578efa7dcd9299a5d947be594f36c15e53fd44479d22d578caab5137"
TITLE_SHA256 = "5c9981fe2536a6cde3c8a1d2e7cdc9684c1369aeb145be4fda635c8af8dfec81"
MAX_BYTES = 4 * 1024 * 1024


class GenerationPremiseHold(ValueError):
    pass


def _bytes(path: Path) -> bytes:
    path = path.absolute()
    if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise GenerationPremiseHold("PREMISE_INPUT_PATH")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        first = os.fstat(descriptor)
        if not stat.S_ISREG(first.st_mode) or first.st_size > MAX_BYTES:
            raise GenerationPremiseHold("PREMISE_INPUT_SIZE_OR_TYPE")
        def read():
            chunks, count = [], 0
            while count <= MAX_BYTES:
                raw = os.read(descriptor, MAX_BYTES + 1 - count)
                if not raw:
                    break
                chunks.append(raw); count += len(raw)
            return b"".join(chunks)
        raw = read(); os.lseek(descriptor, 0, os.SEEK_SET); repeated = read()
        after = os.fstat(descriptor); final = path.lstat()
        frame = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns)
        if (raw != repeated or len(raw) != first.st_size
                or frame(first) != frame(after) or frame(after) != frame(final)
                or any(p.is_symlink() for p in (path, *path.parents))):
            raise GenerationPremiseHold("PREMISE_INPUT_CHANGED")
        return raw
    finally:
        os.close(descriptor)


def _premise():
    """Compile only the exact unchanged sibling checker and title dependency."""
    folder = Path(__file__).absolute().parent
    paths = {"premise_declaration": (folder / "premise_declaration.py", PREMISE_SHA256),
             "inv9_title_basis": (folder / "inv9_title_basis.py", TITLE_SHA256)}
    raws = {name: _bytes(path) for name, (path, _) in paths.items()}
    if any(hashlib.sha256(raws[name]).hexdigest() != expected
           for name, (_, expected) in paths.items()):
        raise GenerationPremiseHold("UNCHANGED_PREMISE_SOURCE_REQUIRED")
    title = types.ModuleType("_forward_exact_title")
    title.__file__ = str(paths["inv9_title_basis"][0])
    exec(compile(raws["inv9_title_basis"], title.__file__, "exec"), title.__dict__)
    def imports(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "inv9_title_basis" and level == 0:
            return title
        return builtins.__import__(name, globals, locals, fromlist, level)
    premise = types.ModuleType("_forward_exact_premise")
    premise.__file__ = str(paths["premise_declaration"][0])
    premise.__dict__["__builtins__"] = {**vars(builtins), "__import__": imports}
    exec(compile(raws["premise_declaration"], premise.__file__, "exec"), premise.__dict__)
    if any(_bytes(path) != raws[name] for name, (path, _) in paths.items()):
        raise GenerationPremiseHold("PREMISE_SOURCE_LOAD_CHANGED")
    return premise


def basis_sentence(basis: str) -> str:
    """Draft wording only; actual frozen inputs must independently pass INV-9."""
    if basis == "INDEPENDENT":
        return (r"The foundation basis is \textbf{INDEPENDENT}; "
                "no framework-level bound or PL/PD premise is used.")
    if basis == "THEOREM":
        return (r"The foundation basis is \textbf{THEOREM}; "
                "the claim is confined to the explicitly cited certified theorem and its hypotheses.")
    if basis == "CONDITIONAL_PL_PD":
        return (r"The foundation basis is \textbf{CONDITIONAL\_PL\_PD}; "
                "the claim is conditional on premises PL and PD.")
    raise GenerationPremiseHold("PREMISE_DECLARATION_MISSING_OR_UNKNOWN")


def _abstract(paper_text: str):
    visible = re.sub(r"(?<!\\)%[^\n]*", "", paper_text)
    matches = list(re.finditer(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", visible, re.S))
    if len(matches) != 1 or r"\begin{document}" not in visible[:matches[0].start()]:
        raise GenerationPremiseHold("UNAMBIGUOUS_MAIN_ABSTRACT_REQUIRED")
    prefix = visible[:matches[0].start()]
    if re.search(r"\\begin\{(?:quote|quotation|verbatim|Verbatim|lstlisting)\}", prefix):
        raise GenerationPremiseHold("MAIN_ABSTRACT_REQUIRED")
    return matches[0]


def declare_abstract(paper_text: str, basis: str) -> str:
    """Prepend a basis sentence to an unsealed draft; never erase dependency text."""
    sentence = basis_sentence(basis)
    match = _abstract(paper_text)
    # Work on the original text so comments and exact non-abstract bytes survive.
    actual = list(re.finditer(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", paper_text, re.S))
    if len(actual) != 1:
        raise GenerationPremiseHold("UNAMBIGUOUS_MAIN_ABSTRACT_REQUIRED")
    if sentence not in match[1]:
        at = actual[0].start(1)
        paper_text = paper_text[:at] + "\n" + sentence + "\n" + paper_text[at:]
    require_abstract_basis(paper_text, basis)
    return paper_text


def require_abstract_basis(paper_text: str, basis: str) -> None:
    basis_sentence(basis)  # closed basis vocabulary
    abstract = _abstract(paper_text)[1]
    # A declaration hidden in a definition, conditional, quotation or literal
    # example is not the author's assertion. Refuse ambiguous abstract source.
    if (re.search(r"\\(?:newcommand|renewcommand|providecommand|DeclareRobustCommand|def|gdef|edef|xdef|let|futurelet|if[a-zA-Z]*|else|fi|phantom|hphantom|vphantom)\b", abstract)
            or re.search(r"\\begin\{(?:quote|quotation|verbatim|Verbatim|lstlisting)\}", abstract)):
        raise GenerationPremiseHold("VISIBLE_MAIN_ABSTRACT_DECLARATION_REQUIRED")
    plain = abstract
    for _ in range(8):
        unwrapped = re.sub(r"\\(?:textbf|texttt|emph)\{([^{}]*)\}", r"\1", plain)
        if unwrapped == plain:
            break
        plain = unwrapped
    plain = plain.replace(r"\_", "_")
    if not re.match(r"\s*(?:(?:\\sloppy|\\noindent|\\raggedright)\s*)*(?:The\s+)?(?:foundation|formal)\s+basis\s*(?:is|:)\s*(?:THEOREM|CONDITIONAL_PL_PD|INDEPENDENT)\b", plain, re.I):
        raise GenerationPremiseHold("ACTUAL_BASIS_REQUIRED_IN_FIRST_ABSTRACT")
    declarations = re.findall(r"(?:foundation|formal)\s+basis\s*(?:is|:)\s*(THEOREM|CONDITIONAL_PL_PD|INDEPENDENT)\b", plain, re.I)
    if not declarations or any(value.upper() != basis for value in declarations):
        raise GenerationPremiseHold("ACTUAL_BASIS_REQUIRED_IN_FIRST_ABSTRACT")
    if basis == "INDEPENDENT" and re.search(r"intelligence\s+bound", abstract, re.I):
        raise GenerationPremiseHold("INDEPENDENT_ABSTRACT_FORBIDDEN_PHRASE")
    if basis == "CONDITIONAL_PL_PD" and "conditional on premises PL and PD" not in " ".join(plain.split()):
        raise GenerationPremiseHold("CONDITIONAL_ABSTRACT_PREMISES_REQUIRED")


def require_premise(manifest, inventory, *, formal_statement, candidate, paper_text, theorem_names):
    if not isinstance(manifest, dict) or not isinstance(inventory, dict):
        raise GenerationPremiseHold("PREMISE_DOCUMENT_OBJECTS_REQUIRED")
    basis = manifest.get("foundation_basis")
    if basis not in BASES or inventory.get("foundation_basis") != basis:
        raise GenerationPremiseHold("PREMISE_DECLARATION_MISMATCH")
    require_abstract_basis(paper_text, basis)
    # The unchanged checker's exact aligner uses importlib; suppress its optional
    # bytecode cache so the static check remains read-only.
    bytecode_setting = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        result = _premise().evaluate(manifest, inventory, formal_statement=formal_statement,
            candidate=candidate, paper_text=paper_text, theorem_names=theorem_names, required=True)
    finally:
        sys.dont_write_bytecode = bytecode_setting
    if (result.get("status") != "PASS" or result.get("foundation_basis") != basis
            or result.get("historical_exemption") is not False
            or result.get("certifies") is not False or result.get("local_lean_execution") is not False):
        raise GenerationPremiseHold("HOLD_PREMISE_DECLARATION")
    return result


def require_staged_premise(stage: Path, manifest: dict):
    """Fresh exact draft inputs; call before seal writes and again before rename."""
    stage = Path(stage).absolute()
    names = ("CLAIM_INVENTORY.json", "paper.tex", "formalization/STATEMENT_CONTRACT.json",
             "formalization/VERIFICATION_STATEMENT.lean", "formalization/VERIFICATION_CANDIDATE.lean")
    raw = {name: _bytes(stage / name) for name in names}
    try:
        inventory = json.loads(raw["CLAIM_INVENTORY.json"])
        contract = json.loads(raw["formalization/STATEMENT_CONTRACT.json"])
        statement = raw["formalization/VERIFICATION_STATEMENT.lean"].decode("utf-8")
        candidate = raw["formalization/VERIFICATION_CANDIDATE.lean"].decode("utf-8")
        paper = raw["paper.tex"].decode("utf-8")
    except (UnicodeError, json.JSONDecodeError):
        raise GenerationPremiseHold("PREMISE_DRAFT_ENCODING_OR_JSON_INVALID") from None
    if not isinstance(inventory, dict) or not isinstance(contract, dict):
        raise GenerationPremiseHold("PREMISE_DRAFT_JSON_OBJECT_REQUIRED")
    if not isinstance(contract, dict) or contract.get("foundation_basis") != manifest.get("foundation_basis"):
        raise GenerationPremiseHold("FROZEN_CONTRACT_BASIS_MISMATCH")
    targets = contract.get("expected_theorem_names")
    witnesses = contract.get("nonvacuity_obligations", [])
    if (not isinstance(targets, list) or not targets or not isinstance(witnesses, list)
            or any(not isinstance(name, str) or not name for name in targets + witnesses)
            or len(set(targets)) != len(targets) or not set(witnesses) <= set(targets)):
        raise GenerationPremiseHold("EXACT_FROZEN_TARGET_CONTRACT_REQUIRED")
    result = require_premise(manifest, inventory,
        formal_statement=statement,
        candidate=candidate,
        paper_text=paper, theorem_names=[n for n in targets if n not in witnesses])
    if any(_bytes(stage / name) != data for name, data in raw.items()):
        raise GenerationPremiseHold("PREMISE_DRAFT_INPUT_CHANGED")
    return {**result, "input_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in raw.items()}}


def require_staged_manifest(stage: Path, manifest_path: Path):
    """Bind an existing draft manifest as well as the five premise inputs."""
    manifest_path = Path(manifest_path)
    raw = _bytes(manifest_path)
    try:
        manifest = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise GenerationPremiseHold("PREMISE_MANIFEST_ENCODING_OR_JSON_INVALID") from None
    if not isinstance(manifest, dict):
        raise GenerationPremiseHold("PREMISE_MANIFEST_OBJECT_REQUIRED")
    result = require_staged_premise(stage, manifest)
    if _bytes(manifest_path) != raw:
        raise GenerationPremiseHold("PREMISE_MANIFEST_CHANGED")
    return {**result, "manifest_sha256": hashlib.sha256(raw).hexdigest()}
