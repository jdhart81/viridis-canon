#!/usr/bin/env python3
"""Default outer guard for future Methods Digest controller execution.

Publication and credential consumption remain in the existing guarded
controller and credential loader. A legacy archive-only package cannot enter
that controller under the new standalone manuscript standard.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import types
import manuscript_pdf_gate


def preflight(config_path: Path, expected_sha256: str) -> dict:
    raw = config_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise manuscript_pdf_gate.ManuscriptPDFHold("digest execution config hash differs")
    config = json.loads(raw)
    package = Path(config["package"])
    manifest = json.loads((package / "DIGEST_MANIFEST.json").read_bytes())
    uploads = manifest.get("uploads")
    if not isinstance(uploads, list) or not uploads:
        raise manuscript_pdf_gate.ManuscriptPDFHold("approved digest upload inventory required")
    return manuscript_pdf_gate.require_local(package, [package / row["filename"] for row in uploads])


def dispatch(config_path: Path, expected_sha256: str, output: Path):
    """Invoke only the config's own hash-bound, reviewed controller."""
    config_raw = config_path.read_bytes()
    if hashlib.sha256(config_raw).hexdigest() != expected_sha256:
        raise manuscript_pdf_gate.ManuscriptPDFHold("digest execution config hash differs before dispatch")
    config = json.loads(config_raw)
    root = Path(config["canonical_root"]).resolve(strict=True)
    bound = config.get("controller")
    if not isinstance(bound, dict) or set(bound) != {"path", "sha256"}:
        raise manuscript_pdf_gate.ManuscriptPDFHold("exact reviewed controller source binding required")
    controller = Path(bound["path"])
    controller = controller if controller.is_absolute() else root / controller
    if not controller.resolve(strict=True).is_relative_to(root):
        raise manuscript_pdf_gate.ManuscriptPDFHold("reviewed controller outside canonical root")
    source = manuscript_pdf_gate._read(controller)
    if hashlib.sha256(source).hexdigest() != bound["sha256"]:
        raise manuscript_pdf_gate.ManuscriptPDFHold("reviewed controller source hash differs")
    if not output.resolve().is_relative_to(root / "reports"):
        raise manuscript_pdf_gate.ManuscriptPDFHold("controller output must remain in canonical private reports")
    module = types.ModuleType("_standalone_pdf_reviewed_digest_controller")
    module.__file__ = str(controller.resolve(strict=True))
    exec(compile(source, str(controller), "exec"), module.__dict__)
    # The existing controller freshly verifies merged source closure, science,
    # own-account authority, mutation journal and final exact public readback.
    import publish_dated_bundles
    checked = preflight(config_path, expected_sha256)
    result = module.execute({"path": str(config_path.resolve(strict=True)), "sha256": expected_sha256},
                            str(output.resolve()), publish_dated_bundles.token())
    terminal = result[0] if isinstance(result, tuple) else result
    if not isinstance(terminal, dict) or terminal.get("published") is not True:
        raise manuscript_pdf_gate.ManuscriptPDFHold("controller has not confirmed publication")
    record = manuscript_pdf_gate.public_record(str(terminal.get("record_id", "")))
    if record.get("doi") != terminal.get("doi"):
        raise manuscript_pdf_gate.ManuscriptPDFHold("controller/public manuscript DOI differs")
    receipt = manuscript_pdf_gate.require_public(record, checked)
    data = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    receipt_path = output / "STANDALONE_MANUSCRIPT_PDF_READBACK.json"
    if receipt_path.exists():
        if manuscript_pdf_gate._read(receipt_path) != data:
            raise manuscript_pdf_gate.ManuscriptPDFHold("standalone manuscript receipt conflicts")
    else:
        with receipt_path.open("xb") as stream:
            stream.write(data)
    return {"controller": result, "standalone_manuscript_pdf_readback": receipt}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--go", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = preflight(args.config, args.expected_config_sha256)
        print(json.dumps(result, sort_keys=True, indent=2))
        if not args.go:
            return 0
        if args.output is None:
            raise manuscript_pdf_gate.ManuscriptPDFHold("private controller output required for --go")
        # Reconsume immediately before dispatch. Downstream science, authority,
        # source closure, transport and strict public readback remain mandatory.
        preflight(args.config, args.expected_config_sha256)
        result = dispatch(args.config, args.expected_config_sha256, args.output)
        print(json.dumps({"reviewed_controller_result": result}, sort_keys=True, indent=2))
        return 0
    except (manuscript_pdf_gate.ManuscriptPDFHold, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("HOLD_STANDALONE_MANUSCRIPT_PDF: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
