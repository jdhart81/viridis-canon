"""Synthetic source-shaped W42 evidence; no installed Core code is executed.

Only the guard and frozen-weekend constants are replaced in tests because the
fixture's inert source bytes are intentionally not real publisher sources.
"""
import contextlib
import copy
import datetime as dt
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest import mock

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))
import root_scope
import w42_receipt as w42


class W42Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name).resolve()
        self.runtime = self.root / "_ZENODO_DEPOSITS/approved_release_sync"
        self.runtime.mkdir(parents=True)
        for name in root_scope.MODULES:
            shutil.copyfile(RUNTIME / name, self.runtime / name)
        self.guard = self.put("_ZENODO_DEPOSITS/guard_methods_digest_release.py", b"# inert outer guard fixture\n")
        self.authority = self.obj("authority.json", {"status": "APPROVED_RULE_AUTHORITY"})
        self.user = self.obj("user-authorization.json", {"standard": "VRS-PROVIDER-BOUND-EXACT-DIGEST-PUBLICATION-AUTHORITY-1", "scope_review": "existing provider-bound publication text"})
        modules = []
        names = ["digest_controller_v2.py", "methods_digest_registration_v3.py", "invoke_digest_v2.py"] + ["current_%02d.py" % i for i in range(17)]
        for name in names:
            path = self.put("_ZENODO_DEPOSITS/standalone_pdf_runtime/" + name, ("# inert " + name + "\n").encode())
            modules.append({"name": name, **self.bind(path)})
        shared = self.put("_ZENODO_DEPOSITS/standalone_pdf_runtime/common/shared.py", b"# inert shared\n")
        shared_rows = [{"name": "shared.py", **self.bind(shared)}]
        legacy = []
        for name in ["weekend_canon_lockstep.py"] + ["legacy_%03d.py" % i for i in range(129)]:
            path = self.put("_ZENODO_DEPOSITS/" + name, ("# frozen fixture " + name + "\n").encode())
            legacy.append({"name": name, **self.bind(path)})
        self.weekend = self.root / "_ZENODO_DEPOSITS/weekend_canon_lockstep.py"
        legacy_scope = self.obj("source-scope.json", {"purpose_source_pins": legacy})
        self.profile = self.obj("_ZENODO_DEPOSITS/standalone_pdf_runtime/CURRENT_PACKAGING_PROFILE.json", {
            "standard": "VRS-DIGEST-ARCHIVAL-PDF-PACKAGING-PROFILE-1", "status": "INSTALLED_EXACT_ADDITIVE_SOURCE_READBACK_PASS",
            "canonical_root": str(self.root), "default_routes": {"digest": "invoke_digest_v2.py"},
            "modules": modules, "shared_dependencies": shared_rows, "legacy_scope": self.bind(legacy_scope)})
        self.nomination = self.obj("_ZENODO_DEPOSITS/standalone_pdf_runtime/INSTALLATION_NOMINATION.json", {
            "standard": "VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-13",
            "status": "EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING", "profile": self.bind(self.profile)})
        self.output = self.root / "reports/verification-coverage/fixture-w42"
        self.config_value = {"canonical_root": str(self.root), "authority": self.bind(self.authority),
            "user_authorization": self.bind(self.user), "packaging_profile": self.bind(self.profile),
            "controller": {key: modules[0][key] for key in ("path", "sha256")}, "source_scope_plan": {"frozen": 130},
            "source_pins": sorted(legacy + modules + shared_rows, key=lambda row: row["name"])}
        # Original CLI config is distinct from the controller's canonical copy.
        self.config = self.put("inputs/ORIGINAL_CONFIG.json", json.dumps(self.config_value, separators=(",", ":")).encode())
        self.scope_value = {"standard": root_scope.STANDARD, "status": "ROOT_REVIEWED", "canonical_root": str(self.root),
            "permitted_actions": sorted(root_scope.ACTIONS), "existing_publication_authority": self.bind(self.user),
            "scientific_package_authority": self.bind(self.authority), "publisher_guard": self.bind(self.guard),
            "config": self.bind(self.config), "publisher_output": str(self.output),
            "sources": {name: self.bind(self.runtime / name) for name in root_scope.MODULES},
            "data_pr_review_policy": {"required": True}, "public_projection_format": "EXISTING_SOURCE_RECORD_WITH_RESTRICTIVE_COVERAGE"}
        self.scope = self.obj("root-scope-initial.json", self.scope_value)
        self.scope_binding = self.bind(self.scope)
        self.stack = contextlib.ExitStack()
        for name in root_scope.MODULES:
            module = sys.modules.get(name[:-3])
            if module is not None:
                self.stack.enter_context(mock.patch.object(module, "__file__", str(self.runtime / name)))
        self.stack.enter_context(mock.patch.object(w42, "GUARD_SHA256", self.bind(self.guard)["sha256"]))
        self.stack.enter_context(mock.patch.object(w42, "FROZEN_WEEKEND_SHA256", self.bind(self.weekend)["sha256"]))

    def close(self): self.stack.close(); self.temp.cleanup()
    def put(self, name, raw):
        path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw); return path
    def obj(self, name, value): return self.put(name, w42.encoded(value))
    def bind(self, path): return {"path": str(path.relative_to(self.root)), "sha256": w42.digest(path.read_bytes())}
    def read(self, path): return json.loads(path.read_bytes())

    def terminal(self, *, week="2026-W42"):
        notes, children, inputs = [], [], {str(self.authority): self.bind(self.authority)["sha256"]}
        for run in ("Run-198", "Run-199"):
            directory = self.root / "METHODS_NOTES" / run; directory.mkdir(parents=True, exist_ok=True)
            source = self.put(str(directory.relative_to(self.root) / "candidate.lean"), ("-- " + run + "\ntheorem example : True := by trivial\n").encode())
            cert = self.obj(str(directory.relative_to(self.root) / "certificate.json"), {"run_id": run, "valid_only_for_predecessor": True})
            statement = self.obj(str(directory.relative_to(self.root) / "statement.json"), {"statement": "conditional predecessor"})
            pdf = self.put(str(directory.relative_to(self.root) / "paper.pdf"), b"%PDF-derived-UNCERTIFIED-" + run.encode())
            note_pb = self.obj(str(directory.relative_to(self.root) / "PUBLICATION_BINDING.json"), {"run_id": run, "certifies": False})
            uploads = [{"filename": p.name, "sha256": self.bind(p)["sha256"]} for p in (source, cert, statement, pdf)]
            for path in (source, cert, statement, pdf, note_pb): inputs[str(path)] = self.bind(path)["sha256"]
            evidence = {"certificate": self.bind(cert), "candidate": self.bind(source), "formal_statement": self.bind(statement),
                "statement_scope": [{"lean_theorem": "example"}], "scientific_predecessor": {"source_sha256": "f" * 64},
                "scope": w42.STATEMENT_SCOPE, "certificate_valid": True, "certifies_current_artifact": False}
            note = {"run_id": run, "path": str(directory), "publication_binding": {**self.bind(note_pb), "bytes": note_pb.stat().st_size},
                "uploads": uploads, "artifact_label": w42.ARTIFACT_LABEL,
                **{key: evidence[key] for key in ("certificate", "candidate", "formal_statement", "statement_scope", "scientific_predecessor")}}
            notes.append(note)
            children.append({"id": "publication:methods-note:" + week + ":" + run, "run_id": run, "path": str(directory),
                "publication_binding": self.bind(note_pb), "certificate": None, "artifact_label": w42.ARTIFACT_LABEL,
                "statement_certificate_evidence": evidence})
        package_pdf = self.put("reports/verification-coverage/fixture-w42/package/paper.pdf", b"%PDF-W42-aggregate")
        uploads = [{"filename": "paper.pdf", "sha256": self.bind(package_pdf)["sha256"], "bytes": package_pdf.stat().st_size, "md5": "0" * 32}]
        self.manifest = self.obj("reports/verification-coverage/fixture-w42/package/DIGEST_MANIFEST.json", {
            "standard": w42.LABELLED_STANDARD, "release_week": week, "authority": self.bind(self.authority), "notes": notes,
            "input_bindings": inputs, "uploads": uploads, "certifies": False})
        self.publication = self.obj("reports/verification-coverage/fixture-w42/package/PUBLICATION_BINDING.json", {
            "manifest": {**self.bind(self.manifest), "bytes": self.manifest.stat().st_size}, "authority": self.bind(self.authority), "uploads": uploads, "certifies": False})
        public = self.obj("reports/verification-coverage/fixture-w42/public.json", {"method": "GET", "record_id": "123", "doi": "10.5281/zenodo.123"})
        self.registration = self.obj("reports/verification-coverage/fixture-w42/registration.json", {
            "standard": "VRS-METHODS-DIGEST-REGISTRATION-3", "status": "PUBLISHED_GROUP_BOUND", "tree_root": str(self.root),
            "record_id": "123", "doi": "10.5281/zenodo.123", "release_week": week, "certifies": False,
            "consumer_sha256": self.bind(self.root / "_ZENODO_DEPOSITS/standalone_pdf_runtime/methods_digest_registration_v3.py")["sha256"],
            "digest_manifest": self.bind(self.manifest), "digest_publication_binding": self.bind(self.publication),
            "public_evidence": self.bind(public), "authority": self.bind(self.authority), "children": children})
        strict = self.obj("reports/verification-coverage/fixture-w42/strict.json", {"status": "STRICT_OWN_PUBLIC_READBACK_PASS", "certifies": False,
            "record_id": "123", "doi": "10.5281/zenodo.123", "binding_sha256": self.bind(self.publication)["sha256"]})
        checkpoint = self.obj("reports/verification-coverage/fixture-w42/registered-checkpoint.json", {"published": True})
        config_copy = self.obj("reports/verification-coverage/fixture-w42/CONFIG.json", self.config_value)
        self.terminal_value = {"standard": "VRS-STANDALONE-PDF-DIGEST-EXECUTION-2", "status": "PUBLISHED_STRICT_READBACK_PASS",
            "published": True, "source_session_exit_succeeded": True, "certifies": False, "ssot_writes": 0, "certificates_issued": 0,
            "canonical_root": str(self.root), "controller": self.config_value["controller"], "doi": "10.5281/zenodo.123", "record_id": "123",
            "release_week": week, "run_ids": [n["run_id"] for n in notes], "config": self.bind(config_copy),
            "source_pins": self.config_value["source_pins"], "source_scope_plan": self.config_value["source_scope_plan"],
            "digest_manifest": self.bind(self.manifest), "publication_binding": self.bind(self.publication),
            "registration_receipt": self.bind(self.registration), "public_evidence": self.bind(public), "strict_readback": self.bind(strict),
            "public_native_receipt": self.bind(public), "public_legacy_receipt": self.bind(public), "checkpoint": self.bind(checkpoint),
            "downloads": [{"filename": p.name, "binding": self.bind(p), "url": "https://zenodo.org/records/123/files/" + p.name}
                          for p in (package_pdf, self.manifest, self.publication)]}
        self.terminal_path = self.obj("reports/verification-coverage/fixture-w42/TERMINAL_RESULT.json", self.terminal_value)
        return self.terminal_path

    def proof(self):
        snapshot = w42.source_snapshot(self.root, self.scope_binding)
        command = w42.fixed_command(self.root, self.scope_value)
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        self.proof_value = {"standard": w42.EXIT_STANDARD, "status": "GUARD_REAPED_EXIT0_SOURCE_UNCHANGED",
            "root_scope": self.scope_binding, "terminal": self.bind(self.terminal_path), "before": snapshot, "after": snapshot,
            "returncode": 0, "process_reaped": True, "child_pid": 123, "command": command,
            "command_sha256": w42.digest(w42.encoded(command)), "caller": self.scope_value["sources"]["w42_after_source_session.py"],
            "started_at_utc": now, "finished_at_utc": now}
        self.proof_path = self.obj("reports/approved-release-source-exit/owned.json", self.proof_value)
        return self.proof_path

    def consume(self): return w42.consume(self.root, self.bind(self.terminal_path), self.bind(self.proof_path), self.scope_binding)
    def refresh_proof(self):
        self.proof_value["terminal"] = self.bind(self.terminal_path)
        self.proof_path.write_bytes(w42.encoded(self.proof_value))

    def package(self):
        intake = self.consume(); mappings = []; files = []
        for row in intake["children"]:
            source = next(p for p in row["source_files"] if p["path"].endswith(".lean"))
            evidence = row["statement_certificate_evidence"]
            projection = {"scope": w42.STATEMENT_SCOPE, "certifies_current_artifact": False, "certificate_valid": True,
                "source_evidence_sha256": w42.digest(w42.encoded(evidence)), "statement_scope": evidence["statement_scope"],
                "scientific_predecessor_sha256": w42.digest(w42.encoded(evidence["scientific_predecessor"]))}
            for key in ("certificate", "candidate", "formal_statement"):
                public = "series/w42/" + row["run_id"] + "/" + Path(evidence[key]["path"]).name
                projection[key] = {"path": public, "sha256": evidence[key]["sha256"]}
                files.append({"target_path": public, "source": evidence[key]})
            mappings.append({"run_id": row["run_id"], "canon_record_id": "canon-" + row["run_id"], "backing_doi": intake["doi"],
                "source_path": source["path"], "source_sha256": source["sha256"], "statement_certificate_evidence": projection})
        self.payload_value = {"publication_mappings": [{"parent_doi": intake["doi"], "parent_canon_publication_id": "parent", "children": mappings}], "git_files": files}
        payload = self.obj("package.json", self.payload_value)
        self.latest_value = copy.deepcopy(self.scope_value)
        self.latest_value.update(publisher_exit_checkpoint=self.bind(self.proof_path), canon_payload_manifest=self.bind(payload), canon_package={
            "publication_receipt_sha256": self.bind(self.terminal_path)["sha256"], "payload_manifest_sha256": self.bind(payload)["sha256"], "adapter_source_sha256": self.bind(self.runtime / "trusted_canon_adapter.py")["sha256"]},
            protected_pr_merge={"standard": "VRS-ROOT-PROTECTED-PR-MERGE-SCOPE-1", "status": "ROOT_REVIEWED", "scope": "PROTECTED_PR_MERGE", "repository": "jdhart81/viridis-canon", "base_branch": "main", "head_sha": "b" * 40,
                "publication_receipt_sha256": self.bind(self.terminal_path)["sha256"], "payload_manifest_sha256": self.bind(payload)["sha256"],
                "adapter_source_sha256": self.bind(self.runtime / "trusted_canon_adapter.py")["sha256"], "merge_policy_source_sha256": self.bind(self.runtime / "protected_pr_merge.py")["sha256"], "required_check_names": ["verify"]})
        self.latest = self.obj("root-scope-canon.json", self.latest_value)
        self.route_value = {"owner_approval": self.bind(self.latest), "publication_receipt": self.bind(self.terminal_path), "canon_payload_manifest": self.bind(payload)}
        self.route = self.obj("route.json", self.route_value)
        self.canon = self.obj("canon.json", {"status": "verified", "repository": "jdhart81/viridis-canon", "branch": "main", "spine_changed": False,
            "bundles": [{"doi": intake["doi"], "record_id": "123"}]})
        return payload
