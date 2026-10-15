#!/usr/bin/env python3
"""Default outer guard for future Methods Digest controller execution.

Publication and credential consumption remain in the existing guarded
controller and credential loader. A legacy archive-only package cannot enter
that controller under the new standalone manuscript standard.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import types
import manuscript_pdf_gate
import rehearsal


def _object(raw: bytes, label: str) -> dict:
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise manuscript_pdf_gate.ManuscriptPDFHold("valid " + label + " required") from exc
    if not isinstance(value, dict):
        raise manuscript_pdf_gate.ManuscriptPDFHold(label + " object required")
    return value


class _PrivateControllerOutput(io.TextIOBase):
    """Discard Python diagnostics before a credential-bearing call can emit them.

    No controller text is copied into a log, receipt, exception or return value.
    The reviewed controller's own scientific/journal behavior is unchanged.
    """
    def write(self, text):
        return len(text)

    def flush(self):
        pass


def _credential_free(value, credential: str) -> None:
    # Reject a contaminated result before it reaches the main printer or a
    # guard receipt. This never reproduces the contaminated string in a HOLD.
    if credential in json.dumps(value, sort_keys=True):
        raise manuscript_pdf_gate.ManuscriptPDFHold("controller returned credential-bearing data")


def preflight(config_path: Path, expected_sha256: str) -> dict:
    raw = manuscript_pdf_gate._read(config_path)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise manuscript_pdf_gate.ManuscriptPDFHold("digest execution config hash differs")
    config = _object(raw, "digest execution config")
    if not isinstance(config.get("package"), str) or not config["package"]:
        raise manuscript_pdf_gate.ManuscriptPDFHold("digest package path required")
    package = Path(config["package"])
    manifest = _object(manuscript_pdf_gate._read(package / "DIGEST_MANIFEST.json"), "digest manifest")
    uploads = manifest.get("uploads")
    if not isinstance(uploads, list) or not uploads:
        raise manuscript_pdf_gate.ManuscriptPDFHold("approved digest upload inventory required")
    if any(not isinstance(row, dict) or not isinstance(row.get("filename"), str)
           or not row["filename"] or Path(row["filename"]).name != row["filename"]
           or row["filename"] in {".", ".."} for row in uploads):
        raise manuscript_pdf_gate.ManuscriptPDFHold("approved digest upload basenames required")
    return manuscript_pdf_gate.require_local(package, [package / row["filename"] for row in uploads])


def dispatch(config_path: Path, expected_sha256: str, output: Path, *, rehearse=False):
    """Invoke only the config's own hash-bound, reviewed controller."""
    rehearsal.require_production()
    checked = preflight(config_path, expected_sha256)
    config_raw = manuscript_pdf_gate._read(config_path)
    if hashlib.sha256(config_raw).hexdigest() != expected_sha256:
        raise manuscript_pdf_gate.ManuscriptPDFHold("digest execution config hash differs before dispatch")
    config = _object(config_raw, "digest execution config")
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
    if rehearse:
        engine = __import__("os").environ.get("VIRIDIS_ENGINE_ROOT")
        if not engine or not output.resolve().is_relative_to(Path(engine).resolve(strict=True) / "rehearsals"):
            raise manuscript_pdf_gate.ManuscriptPDFHold("rehearsal output must remain in ENGINE/rehearsals/<UTC>")
    elif not output.resolve().is_relative_to(root / "reports"):
        raise manuscript_pdf_gate.ManuscriptPDFHold("controller output must remain in canonical private reports")
    module = types.ModuleType("_standalone_pdf_reviewed_digest_controller")
    module.__file__ = str(controller.resolve(strict=True))
    # The existing controller freshly verifies merged source closure, science,
    # own-account authority, mutation journal and final exact public readback.
    try:
        with contextlib.redirect_stdout(_PrivateControllerOutput()), contextlib.redirect_stderr(_PrivateControllerOutput()):
            exec(compile(source, str(controller), "exec"), module.__dict__)
            if rehearse and not callable(getattr(module, "rehearse", None)):
                raise manuscript_pdf_gate.ManuscriptPDFHold("reviewed controller lacks the ENGINE-scoped draft-and-discard contract")
            import publish_dated_bundles
            credential = publish_dated_bundles.token()
            if not isinstance(credential, str) or not credential:
                raise manuscript_pdf_gate.ManuscriptPDFHold("controller credential unavailable")
            # Reconsume the exact approved package immediately before dispatch.
            checked = preflight(config_path, expected_sha256)
            operation = module.rehearse if rehearse else module.execute
            result = operation({"path": str(config_path.resolve(strict=True)), "sha256": expected_sha256},
                               str(output.resolve()), credential)
        _credential_free(result, credential)
    except Exception:
        # A token may be embedded in any downstream exception, including a
        # third-party exception class. Do not propagate its text or traceback.
        raise manuscript_pdf_gate.ManuscriptPDFHold("reviewed controller execution failed") from None
    terminal = result[0] if isinstance(result, tuple) else result
    if rehearse:
        if (not isinstance(terminal, dict) or terminal.get("published") is not False
                or terminal.get("status") != "REHEARSED_DRAFT_DELETED"
                or terminal.get("draft_deleted_http_status") not in (404, 410)):
            raise manuscript_pdf_gate.ManuscriptPDFHold("controller rehearsal lacks exact draft-deletion readback")
        return {"controller_rehearsal": result}
    if not isinstance(terminal, dict) or terminal.get("published") is not True:
        raise manuscript_pdf_gate.ManuscriptPDFHold("controller has not confirmed publication")
    record = manuscript_pdf_gate.public_record(str(terminal.get("record_id", "")))
    if record.get("doi") != terminal.get("doi"):
        raise manuscript_pdf_gate.ManuscriptPDFHold("controller/public manuscript DOI differs")
    receipt = manuscript_pdf_gate.require_public(record, checked)
    _credential_free(receipt, credential)
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
    parser.add_argument("--rehearse", action="store_true")
    args = parser.parse_args(argv)
    credential_boundary = False
    try:
        rehearsal.require_production()
        result = preflight(args.config, args.expected_config_sha256)
        print(json.dumps(result, sort_keys=True, indent=2))
        if not args.go:
            if args.rehearse:
                raise manuscript_pdf_gate.ManuscriptPDFHold("rehearsal requires --go")
            return 0
        if args.output is None:
            raise manuscript_pdf_gate.ManuscriptPDFHold("private controller output required for --go")
        # Reconsume immediately before dispatch. Downstream science, authority,
        # source closure, transport and strict public readback remain mandatory.
        preflight(args.config, args.expected_config_sha256)
        credential_boundary = True
        result = dispatch(args.config, args.expected_config_sha256, args.output, rehearse=True) if args.rehearse else dispatch(args.config, args.expected_config_sha256, args.output)
        print(json.dumps({"reviewed_controller_result": result}, sort_keys=True, indent=2))
        return 0
    except Exception as exc:
        if not credential_boundary and isinstance(exc, manuscript_pdf_gate.ManuscriptPDFHold):
            print("HOLD_STANDALONE_MANUSCRIPT_PDF: " + str(exc), file=sys.stderr)
            return 1
        # Preflight and public-readback exceptions can also contain unsafe
        # third-party diagnostics. A fixed outer HOLD never echoes input text.
        print("HOLD_STANDALONE_MANUSCRIPT_PDF: execution refused; private evidence required", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
