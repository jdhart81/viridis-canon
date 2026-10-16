"""Reproduce inactive patches from the three exact reviewed predecessor sources.

Only repository review artifacts are written. This tool has no CORE installation
path, publication client or production execution mode.
"""
from pathlib import Path
import argparse
import ast
import difflib
import hashlib
import json

HERE = Path(__file__).resolve().parent
RESOLVER = HERE.parent / "effective_allocation.py"
BEFORE = {
    "canon_product_router.py": "145409f74cee9ef48f3746050b731decaa5d9e9c33ec37d69b68b91d6f34a867",
    "assemble_saturday_candidate.py": "a94df6572ad68ada2f7d524aabde3d9f3ff1d6f69c7440a5f47653c71185c7c6",
    "reconcile_publication_receipt.py": "7d35e45713fe339ac543d9d3bb270897bd8e1bd611c8ebec568ce7d66f4386f8",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after, 1)


def loader(error_class):
    # An ambient module/sys.path/__pycache__ entry never supplies this code.
    return '''
EFFECTIVE_ALLOCATION_SOURCE_SHA256 = "RESOLVER_HASH"


def load_effective_allocation():
    path = HERE / "effective_allocation.py"
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ERROR_CLASS("HOLD_EFFECTIVE_ALLOCATION_MODULE_PATH")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EFFECTIVE_ALLOCATION_SOURCE_SHA256:
        raise ERROR_CLASS("HOLD_EFFECTIVE_ALLOCATION_MODULE_PIN")
    namespace = {"__file__": str(path), "__name__": "_bound_effective_allocation"}
    exec(compile(raw, str(path), "exec"), namespace)
    if path.read_bytes() != raw or any(p.is_symlink() for p in (path, *path.parents)):
        raise ERROR_CLASS("HOLD_EFFECTIVE_ALLOCATION_MODULE_RACE")
    return namespace


def effective_allocation_view(finalized_root, reconciliation_surface, *, allocation_correction=None,
                              ledger_path=None, expected_ledger_sha256=None):
    module = load_effective_allocation()
    try:
        root = module["safe_path"](finalized_root)
        if ledger_path is None:
            ledger_path = root.parent.parent / "ZENODO_SUBMISSION_LEDGER.md"
        if allocation_correction is None and (root / "Run-183/RELEASE_BINDING_PROPOSAL.json").exists():
            # Fixed installed role + reviewed byte pin, never an ambient search.
            allocation_correction = {"path": str(root / "Run-183" / module["OVERLAY_NAME"]),
                                     "sha256": module["OVERLAY_SHA256"]}
            if expected_ledger_sha256 is None:
                expected_ledger_sha256 = module["sha"](module["regular"](ledger_path)[0])
        view = module["resolve"](finalized_root, reconciliation_surface,
            correction=allocation_correction, ledger_path=ledger_path,
            expected_ledger_sha256=expected_ledger_sha256)
        view.read(HERE / "effective_allocation.py", EFFECTIVE_ALLOCATION_SOURCE_SHA256)
        view.revalidate()
        return ConsumerAllocationView(view, module["AllocationHold"])
    except module["AllocationHold"] as exc:
        raise ERROR_CLASS(str(exc)) from None



class ConsumerAllocationView:
    """Translate late read/revalidate failures at every consumer boundary."""
    def __init__(self, view, hold):
        self._view, self._hold = view, hold

    def __getattr__(self, name):
        try:
            value = getattr(self._view, name)
        except self._hold as exc:
            raise ERROR_CLASS(str(exc)) from None
        if not callable(value):
            return value
        def call(*args, **kwargs):
            try:
                return value(*args, **kwargs)
            except self._hold as exc:
                raise ERROR_CLASS(str(exc)) from None
        return call


def serialized_receipt(value, *, sort_keys=True):
    try:
        return json.dumps(value, indent=2, sort_keys=sort_keys, allow_nan=False) + "\\n"
    except (TypeError, ValueError) as exc:
        raise ERROR_CLASS("HOLD_RECEIPT_SERIALIZATION: " + str(exc)) from None

def explicit_allocation_options(path, digest, ledger_digest):
    if path is None and digest is None and ledger_digest is None:
        return {"allocation_correction": None, "expected_ledger_sha256": None}
    if path is None or digest is None or ledger_digest is None:
        raise ERROR_CLASS("HOLD_EFFECTIVE_ALLOCATION_EXPLICIT_PIN_AND_LEDGER_CAS_REQUIRED")
    return {"allocation_correction": {"path": path, "sha256": digest},
            "expected_ledger_sha256": ledger_digest}

'''.replace("RESOLVER_HASH", sha(RESOLVER.read_bytes())).replace("ERROR_CLASS", error_class)


def router(text):
    begin = text.index("def reserved_ledger_state(")
    end = text.index("\n\ndef seal_route_and_proposal", begin)
    text = text[:begin] + '''def reservation_state(view):
    return (view.authoritative_max, list(view.public_rows), list(view.proposal_rows),
            [display_path(Path(path)) for path in view.input_bindings])


def reserved_ledger_state(finalized_root, reconciliation_surface, *, allocation_correction=None,
                          ledger_path=None, expected_ledger_sha256=None):
    view = effective_allocation_view(finalized_root, reconciliation_surface,
        allocation_correction=allocation_correction, ledger_path=ledger_path,
        expected_ledger_sha256=expected_ledger_sha256)
    return reservation_state(view)
''' + text[end:]
    text = once(text, '    proposed_license: str = "cc-by-4.0",\n', '    proposed_license: str = "cc-by-4.0",\n    allocation_correction=None,\n    ledger_path: Path | None = None,\n    expected_ledger_sha256=None,\n')
    text = once(text, '''    authoritative_max, public_rows, proposal_rows, surfaces = reserved_ledger_state(
        finalized_root, reconciliation_surface
    )''', '''    if ledger_path is None:
        ledger_path = finalized_root.parent.parent / "ZENODO_SUBMISSION_LEDGER.md"
    allocation = effective_allocation_view(finalized_root, reconciliation_surface,
        allocation_correction=allocation_correction, ledger_path=ledger_path,
        expected_ledger_sha256=expected_ledger_sha256)
    authoritative_max, public_rows, proposal_rows, surfaces = reservation_state(allocation)''')
    text = once(text, '            "reservation_surfaces": surfaces,', '            "reservation_surfaces": surfaces,\n            "effective_allocation_projection": allocation.receipt(),')
    begin = text.index('    write_json_atomic(route_path, route)')
    end = text.index('\n\n\ndef main()', begin)
    result = text[text.index('    return {', begin):end].replace('    return {', '    result = {', 1)
    text = text[:begin] + result + '''
    route_bytes = serialized_receipt(route).encode("utf-8")
    serialized_receipt(proposal)
    serialized_receipt(result)
    allocation.revalidate()
    write_json_atomic(route_path, route)
    try:
        allocation.revalidate()
        write_json_atomic(proposal_path, proposal)
    except Exception:
        # Only remove our own exact route afterimage; never another writer's.
        if route_path.is_file() and not route_path.is_symlink() and route_path.read_bytes() == route_bytes:
            route_path.unlink()
        raise
    return result
''' + text[end:]
    text = once(text, '        result = seal_route_and_proposal(args.run, proposed_license=args.proposed_license)', '''        options = explicit_allocation_options(args.allocation_correction,
            args.allocation_correction_sha256, args.expected_ledger_sha256)
        result = seal_route_and_proposal(args.run, proposed_license=args.proposed_license, **options)''')
    return text


def assembler(text):
    text = once(text, '    kernel_packages_root: Path | None = None,\n', '    kernel_packages_root: Path | None = None,\n    reconciliation_surface: Path | None = None,\n    allocation_correction=None,\n    expected_ledger_sha256=None,\n')
    begin = text.index('    proposal_path = root / "RELEASE_BINDING_PROPOSAL.json"', text.index('def stage_candidate'))
    end = text.index('    title = manifest.get("title")', begin)
    text = text[:begin] + '''    proposal_path = root / "RELEASE_BINDING_PROPOSAL.json"
    if reconciliation_surface is None:
        reconciliation_surface = finalized_root.parent / "PUBLIC_IDENTITY_RECONCILIATION_SURFACE_2026-08-30.json"
    allocation = effective_allocation_view(finalized_root, reconciliation_surface,
        allocation_correction=allocation_correction, ledger_path=ledger_path,
        expected_ledger_sha256=expected_ledger_sha256)
    candidate = allocation.proposals.get(run_id)
    proposal = candidate if candidate and candidate.get("status") == "READY_FOR_EXACT_AUTHORIZATION" else None
    if proposal is not None and (not isinstance(proposal.get("proposed_license"), str) or not proposal["proposed_license"].strip()):
        raise AssemblyError("ready release proposal requires a proposed license")
    allocation_identity = allocation.run_receipt(run_id)
    proposal_binding = ({
        "path": str(proposal_path),
        "sha256": allocation.input_bindings[str(proposal_path.absolute())],
        "original_proposed_ledger_row": allocation.original_proposal(run_id)["proposed_ledger_row"],
        "proposed_license": proposal["proposed_license"],
        "proposed_ledger_row": proposal["proposed_ledger_row"],
        "effective_allocation_receipt": allocation_identity,
    } if proposal is not None else None)
''' + text[end:]
    text = once(text, '        if prior.get("source_sha256") == bound_sources:', '''        old_binding = prior.get("release_binding_proposal")
        same_allocation = old_binding is None and proposal_binding is None
        if isinstance(old_binding, dict) and isinstance(proposal_binding, dict):
            same_allocation = all(old_binding.get(key) == proposal_binding[key]
                for key in ("path", "sha256", "proposed_license", "proposed_ledger_row"))
            # Legacy unaffected bundles can replay; a legacy183 row147 cannot.
            if "effective_allocation_receipt" in old_binding:
                same_allocation = same_allocation and old_binding["effective_allocation_receipt"] == allocation_identity
        allocation.revalidate()
        if prior.get("source_sha256") == bound_sources and same_allocation:''')
    begin = text.index('    temp.mkdir(parents=True)', text.index('def stage_candidate'))
    end = text.index('\n\n\ndef identical_tree', begin)
    original = text[begin:end]
    manifest = original[original.index('    bundle_manifest = {'):original.index('    write_json_atomic(temp / "BUNDLE_MANIFEST.json"')]
    start = manifest.index('        "release_binding_proposal": (')
    finish = manifest.index('        "artifact_sha256":', start)
    manifest = manifest[:start] + '''        "release_binding_proposal": proposal_binding,
        "effective_allocation_receipt": allocation_identity,
        "allocation_input_sha256": allocation.input_bindings,
''' + manifest[finish:]
    manifest = manifest.replace('"artifact_sha256": tree_hashes(temp)', '"artifact_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(prepared.items())}')
    text = text[:begin] + '''    # Freeze every output and receipt before mkdir or any other local write.
    prepared = {}
    for source in (paper, *lean, *summaries, review, kernel_package):
        prepared[source.name] = source.read_bytes()
    for relative, source in kernel_artifacts:
        prepared[(Path("viridisos_kernel") / relative).as_posix()] = source.read_bytes()
    prepared["zenodo_metadata.json"] = serialized_receipt(zenodo_payload(title.strip(), metadata)).encode("utf-8")
    coherence = load_coherence()
    prepared["RIGHTS_AND_LICENSE.md"] = coherence.unassigned_rights_notice(title.strip()).encode("utf-8")
''' + manifest + '''    manifest_bytes = serialized_receipt(bundle_manifest).encode("utf-8")
    result = {"status": "STAGED_CANDIDATE", "run_id": run_id, "bundle": str(destination), "ledger": ledger}
    serialized_receipt(result)
    allocation.revalidate()
    temp.mkdir(parents=True)
    try:
        for name, raw in prepared.items():
            target = temp / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        (temp / "BUNDLE_MANIFEST.json").write_bytes(manifest_bytes)
        allocation.revalidate()
        os.replace(temp, destination)
    except Exception:
        # This invocation exclusively created temp; never touch destination.
        shutil.rmtree(temp)
        raise
    return result
''' + text[end:]
    text = once(text, 'def scan(date: str, *, finalized_root: Path = FINALIZED_ROOT) -> dict[str, Any]:', 'def scan(date: str, *, finalized_root: Path = FINALIZED_ROOT, allocation_correction=None,\n         expected_ledger_sha256=None) -> dict[str, Any]:')
    text = once(text, 'stage_candidate(root.name, date, finalized_root=finalized_root)', 'stage_candidate(root.name, date, finalized_root=finalized_root,\n                    allocation_correction=allocation_correction, expected_ledger_sha256=expected_ledger_sha256)')
    text = once(text, '    try:\n        if args.run:\n            result = stage_candidate(args.run, args.date)', '''    try:
        options = explicit_allocation_options(args.allocation_correction,
            args.allocation_correction_sha256, args.expected_ledger_sha256)
        if (args.bind_ledger or args.promote_ledger_cleared) and options["allocation_correction"] is not None:
            raise AssemblyError("allocation projection does not authorize bind or promotion")
        if args.run:
            result = stage_candidate(args.run, args.date, **options)''')
    text = once(text, '            result = scan(args.date)', '            result = scan(args.date, **options)')
    return text


def reconciler(text):
    text = once(text, 'import argparse\n', 'import argparse\nimport hashlib\n')
    begin = text.index('def proposal_map(');end = text.index('\n\ndef route_for(',begin)
    text = text[:begin] + '''def proposal_map_from_view(view):
    result = {}
    for run_id, proposal in sorted(view.proposals.items()):
        abbreviation = str(proposal.get("abbreviation", "")).strip().upper()
        if not abbreviation or abbreviation in result:
            raise ReconciliationError("missing or duplicate proposal abbreviation")
        result[abbreviation] = proposal
    return result


def proposal_map(finalized_root, *, reconciliation_surface=None, allocation_correction=None,
                 ledger_path=None, expected_ledger_sha256=None):
    if reconciliation_surface is None:
        reconciliation_surface = finalized_root.parent / "PUBLIC_IDENTITY_RECONCILIATION_SURFACE_2026-08-30.json"
    return proposal_map_from_view(effective_allocation_view(finalized_root, reconciliation_surface,
        allocation_correction=allocation_correction, ledger_path=ledger_path,
        expected_ledger_sha256=expected_ledger_sha256))
''' + text[end:]
    text = once(text, '    root: Path = ROOT,\n', '    root: Path = ROOT,\n    allocation_correction=None,\n    expected_ledger_sha256=None,\n')
    text = once(text, '    proposals = proposal_map(finalized_root)', '''    ledger_path = root / "ZENODO_SUBMISSION_LEDGER.md"
    allocation = effective_allocation_view(finalized_root,
        root / "RESEARCH_PIPELINE_v2/PUBLIC_IDENTITY_RECONCILIATION_SURFACE_2026-08-30.json",
        allocation_correction=allocation_correction, ledger_path=ledger_path,
        expected_ledger_sha256=expected_ledger_sha256)
    proposals = proposal_map_from_view(allocation)''')
    text = once(text, '    ledger_before = ledger_path.read_text(encoding="utf-8")', '    ledger_before = allocation.read(ledger_path).decode("utf-8")')
    text = once(text, '    intake = read_json(intake_path)', '''    intake = json.loads(allocation.read(intake_path))
    if not isinstance(intake, dict):
        raise ReconciliationError("intake must be a JSON object")''')
    begin = text.index('    if apply:\n        if ledger_changed:')
    end = text.index('\n\n\ndef main()', begin)
    result = text[text.index('    return {', begin):end].replace('    return {', '    result = {', 1)
    result = once(result, '        "status": "APPLIED" if apply else "DRY_RUN",', '        "status": "APPLIED" if apply else "DRY_RUN",\n        "effective_allocation_projection": allocation.receipt(),')
    text = text[:begin] + result + '''
    serialized_receipt(result)
    intake_bytes = serialized_receipt(intake, sort_keys=False)
    allocation.revalidate()
    if apply:
        if ledger_changed:
            write_text_atomic(ledger_path, ledger_after)
        if intake_changed:
            if ledger_changed:
                allocation.revalidate_after_ledger_write(ledger_after.encode("utf-8"))
            else:
                allocation.revalidate()
            write_text_atomic(intake_path, intake_bytes)
    return result
''' + text[end:]
    text = once(text, '        print(json.dumps(reconcile(args.receipt.resolve(), apply=args.apply), indent=2))', '''        options = explicit_allocation_options(args.allocation_correction,
            args.allocation_correction_sha256, args.expected_ledger_sha256)
        print(json.dumps(reconcile(args.receipt.resolve(), apply=args.apply, **options), indent=2))''')
    return text


TRANSFORMS = {"canon_product_router.py": (router,"RouteError"),
              "assemble_saturday_candidate.py": (assembler,"AssemblyError"),
              "reconcile_publication_receipt.py": (reconciler,"ReconciliationError")}


def artifacts():
    result = {}; rows = {}
    for name, expected in BEFORE.items():
        raw = (HERE/"before"/(name+".txt")).read_bytes(); assert sha(raw) == expected
        before = raw.decode(); transform,error = TRANSFORMS[name]
        after = transform(before)
        at = after.index("\ndef read_json(")
        after = after[:at] + loader(error) + after[at:]
        after = once(after, '    args = parser.parse_args()', '''    parser.add_argument("--allocation-correction", type=Path)
    parser.add_argument("--allocation-correction-sha256")
    parser.add_argument("--expected-ledger-sha256")
    args = parser.parse_args()''')
        ast.parse(after)
        relative = 'RESEARCH_PIPELINE_v2/' + name
        patch = ''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/'+relative,tofile='b/'+relative)).encode()
        # Git and patch accept empty context lines without a padding space.
        # Keep review artifacts free of whitespace-only added file lines.
        patch = b''.join(b'\n' if line == b' \n' else line for line in patch.splitlines(keepends=True))
        result['patches/'+name+'.patch'] = patch
        rows[name] = dict(before_sha256=expected,after_sha256=sha(after.encode()),patch_sha256=sha(patch),target=relative)
    manifest = dict(standard='VRS-INACTIVE-EFFECTIVE-ALLOCATION-PATCHES-1',active=False,
        merged_installed_or_publication_authority=False,resolver_source_sha256=sha(RESOLVER.read_bytes()),
        sources=rows,requires='independent exact-head review, Justin merge, separate S4 installation and fresh CAS')
    result['PATCH_MANIFEST.json'] = (json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    for name,raw in artifacts().items():
        path=HERE/name
        if a.check:
            assert path.read_bytes()==raw, 'nonreproducible review artifact: '+name
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)


if __name__=='__main__':main()
