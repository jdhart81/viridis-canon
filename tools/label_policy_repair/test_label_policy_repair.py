"""Prospective pure tests; authored only, not executed in the source-only scope."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
import tempfile
import time
import io
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).with_name("label_policy_repair.py")
spec = importlib.util.spec_from_file_location("label_policy_repair", SOURCE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def fixture(mod=tool):
    raw = b"immutable public paper bytes"
    sha = hashlib.sha256(raw).hexdigest()
    metadata = {"description": "<p>Working paper, not peer reviewed.</p><h2>New caveat</h2>",
                "subjects": [{"subject": "working paper", "scheme": "retained"}],
                "creators": [{"person_or_org": {"name": "Retained Author"}}],
                "rights": [{"id": "cc-by-4.0"}],
                "related_identifiers": [{"identifier": "exact-certificate-reference"}]}
    public = {"id": "20008839", "revision_id": 3, "metadata": metadata,
              "access": {"record": "public", "files": "public"},
              "pids": {"doi": {"identifier": "existing-doi"}},
              "parent": {"communities": {"ids": ["retained-community"]}},
              "files": {"entries": {"paper.pdf": {"key": "paper.pdf", "size": len(raw),
                                                  "checksum": "md5:retained"}}},
              "is_draft": False, "links": {"self": "server lifecycle link"}}
    item = {"id": "20008839", "before_revision": 3, "before_etag": '"3"',
            "before_metadata": copy.deepcopy(metadata),
            "before_projection_sha256": mod.digest(mod.projection(public)),
            "public_files": [{"key": "paper.pdf", "size": len(raw),
                              "checksum": "md5:retained", "sha256": sha}],
            "add_banner": True,
            "description_edits": [{"kind": "historical_caveat", "before": "New caveat",
                                   "after": "Historical verification claim; exact scope only"}],
            "subject_edits": [{"index": 0, "before": "working paper", "after": "uncertified"}],
            "mapping_source_ids": ["inventory", "mapping"],
            "status_mapping_evidence": {
                "verdict": "INDEPENDENT_EXACT_BYTES_SCOPE_REVIEW_PASS",
                "source_ids": ["inventory", "mapping"], "artifacts": [{
                    "key": "paper.pdf", "public_sha256": sha, "status": "UNMATCHED_EXACT_BYTES",
                    "certificate_inventory_source_ids": ["inventory"], "certificates": []}]}}
    expected = copy.deepcopy(metadata)
    expected["description"] = "<p>" + mod.BANNER + "</p>\n" + metadata["description"].replace(
        "New caveat", "Historical verification claim; exact scope only")
    expected["subjects"][0]["subject"] = "uncertified"
    item["expected_metadata_sha256"] = mod.digest(expected)
    draft = copy.deepcopy(public); draft["is_draft"] = True
    updated = copy.deepcopy(draft); updated["metadata"] = expected
    final = copy.deepcopy(updated); final["is_draft"] = False; final["revision_id"] = 4
    return public, item, draft, updated, final


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, copy.deepcopy(kwargs)))
        if not self.responses:
            raise AssertionError("unexpected dispatch")
        return self.responses.pop(0)


def response(value=None, status=200, etag=None):
    return status, copy.deepcopy(value), {} if etag is None else {"etag": etag}


def scripted(mode="apply", mutation=None, public_mutation=None):
    public, item, draft, updated, final = fixture()
    actual_public = copy.deepcopy(public)
    if public_mutation:
        public_mutation(actual_public)
        draft = copy.deepcopy(actual_public); draft["is_draft"] = True
    actual_updated = copy.deepcopy(updated)
    if mutation:
        mutation(actual_updated)
    file_bytes = {"size": item["public_files"][0]["size"],
                  "sha256": item["public_files"][0]["sha256"]}
    rows = [response(actual_public), response(file_bytes), response(status=404),
            response(actual_public, etag='"3"'), response(draft, status=201, etag='"3"'),
            response(updated), response(actual_updated, etag='"3"')]
    if mode == "apply":
        rows += [response(status=202), response(final), response(file_bytes)]
    else:
        rows += [response(status=204), response(status=404), response(public), response(file_bytes)]
    return item, FakeTransport(rows)


class PolicyTests(unittest.TestCase):
    def action(self, directory, item, transport, mod=tool, mode="apply", cas=None):
        journal = mod.Journal(directory, item["id"], "a" * 64, mode)
        action = mod.Action({}, item, journal, transport, cas or (lambda deadline: None),
                            time.monotonic())
        return action, journal

    def test_clean_baseline_full_body_and_exact_public_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted()
            action, journal = self.action(directory, item, transport)
            action.run("apply")
            self.assertEqual(journal.value["state"], "PUBLISHED_METADATA_AND_BYTES_VERIFIED")
            put = [kw["body"] for method, path, kw in transport.calls if method == "PUT"][0]
            self.assertEqual(put["parent"], fixture()[0]["parent"])
            self.assertEqual(put["metadata"]["creators"], fixture()[0]["metadata"]["creators"])
            self.assertEqual(put["metadata"]["subjects"][0]["scheme"], "retained")
            self.assertTrue(all(not kw.get("authenticated") for method, path, kw in transport.calls
                                if path.endswith("/content")))

    def test_replay_refused_before_dispatch_and_claim_kind_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted("rehearse")
            action, journal = self.action(directory, item, transport, mode="rehearse")
            action.run("rehearse")
            with self.assertRaises(tool.Hold):
                tool.Journal(directory, item["id"], "b" * 64, "rehearse")
            other = tool.Journal(directory, item["id"], "a" * 64, "apply")
            self.assertEqual(other.value["kind"], "apply")

    def test_rehearsal_zero_publish_and_owned_cleanup_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted("rehearse")
            action, journal = self.action(directory, item, transport, mode="rehearse")
            action.run("rehearse")
            self.assertTrue(journal.value["cleanup_confirmed"])
            self.assertFalse(any(path.endswith("/actions/publish") for _, path, _ in transport.calls))
            action.ready = True
            with self.assertRaises(tool.Hold):
                action.call("POST", action.base + "/draft/actions/publish", {202})

    def test_existing_or_foreign_draft_never_changed_or_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted()
            transport.responses[2] = response({"id": item["id"]})
            action, journal = self.action(directory, item, transport)
            with self.assertRaises(tool.Hold):
                action.run("apply")
            self.assertFalse(any(m != "GET" for m, _, _ in transport.calls))
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted()
            transport.responses[4][1]["id"] = "foreign"
            action, journal = self.action(directory, item, transport)
            with self.assertRaises(tool.Hold):
                action.run("apply")
            self.assertFalse(any(m == "DELETE" for m, _, _ in transport.calls))

    def test_revision_and_source_cas_prevent_mutation(self):
        for which in ("revision", "source"):
            with self.subTest(which=which), tempfile.TemporaryDirectory() as directory:
                item, transport = scripted()
                if which == "revision":
                    transport.responses[3][1]["revision_id"] = 4
                def cas(deadline):
                    if which == "source":
                        raise tool.Hold("INPUT_HASH_DRIFT")
                action, journal = self.action(directory, item, transport, cas=cas)
                with self.assertRaises(tool.Hold):
                    action.run("apply")
                self.assertFalse(any(m != "GET" for m, _, _ in transport.calls))

    def test_first_401_persists_after_cleanup_and_poison_blocks_later_get(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted()
            transport.responses = transport.responses[:5] + [response(status=401),
                                                             response(status=204), response(status=404)]
            action, journal = self.action(directory, item, transport)
            with self.assertRaisesRegex(tool.Hold, "HTTP_401"):
                action.run("apply")
            self.assertEqual(journal.value["first_failure"], "HTTP_401")
            self.assertTrue(journal.value["cleanup_confirmed"])
            count = len(transport.calls)
            with self.assertRaises(tool.Hold):
                action.call("GET", action.base, {200})
            self.assertEqual(count, len(transport.calls))
            rows = [json.loads(line) for line in journal.path.read_text().splitlines()]
            self.assertEqual([r["first_failure"] for r in rows if r["first_failure"]][-1], "HTTP_401")

    def test_failed_cleanup_preserves_first_failure_and_is_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted()
            transport.responses = transport.responses[:5] + [response(status=403), response(status=500)]
            action, journal = self.action(directory, item, transport)
            with self.assertRaisesRegex(tool.Hold, "HTTP_403"):
                action.run("apply")
            self.assertFalse(journal.value["cleanup_confirmed"])
            self.assertEqual(journal.value["first_failure"], "HTTP_403")

    def test_unexpected_metadata_diff_discards_without_publishing(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted(mutation=lambda r: r["metadata"].update(title="unexpected"))
            transport.responses = transport.responses[:7] + [response(status=204), response(status=410)]
            action, journal = self.action(directory, item, transport)
            with self.assertRaises(tool.Hold):
                action.run("apply")
            self.assertTrue(journal.value["cleanup_confirmed"])
            self.assertFalse(any(p.endswith("/actions/publish") for _, p, _ in transport.calls))

    def test_all_file_inventory_and_bytes_are_exact(self):
        for which in ("inventory", "bytes", "final_bytes"):
            with self.subTest(which=which), tempfile.TemporaryDirectory() as directory:
                item, transport = scripted()
                if which == "inventory":
                    transport.responses[0][1]["files"]["entries"]["extra"] = {"size": 1, "checksum": "x"}
                elif which == "bytes":
                    transport.responses[1][1]["sha256"] = "0" * 64
                else:
                    transport.responses[-1][1]["sha256"] = "0" * 64
                action, journal = self.action(directory, item, transport)
                with self.assertRaises(tool.Hold):
                    action.run("apply")
                self.assertNotEqual(journal.value["state"], "PUBLISHED_METADATA_AND_BYTES_VERIFIED")

    def test_positive_mapping_bound_certificate_and_nonpaper_rules(self):
        item = fixture()[1]
        tool.validate_mapping(item, {"inventory": {"sha256": "a" * 64}})
        for mutation in (lambda i: i["status_mapping_evidence"]["artifacts"][0].update(status="UNKNOWN"),
                         lambda i: i.update(id="23112434"),
                         lambda i: i["status_mapping_evidence"]["artifacts"][0].update(
                             status="BOUND_EXACT_BYTES", certificates=[{
                                 "source_id": "inventory", "sha256": "a" * 64,
                                 "bound_artifact_sha256": i["public_files"][0]["sha256"],
                                 "theorem_scope": "Exact predecessor scope"}])):
            candidate = copy.deepcopy(item); mutation(candidate)
            with self.assertRaises(tool.Hold):
                tool.validate_mapping(candidate, {"inventory": {"sha256": "a" * 64}})

    def test_foreign_record_rejected_by_finite_plan_guard(self):
        item = fixture()[1]; item["id"] = "99999999"
        with self.assertRaisesRegex(tool.Hold, "FOREIGN_RECORD_ID"):
            tool.validate_record(item, {})

    def test_stable_hash_and_symlink_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"; source.write_bytes(b"source")
            expected = hashlib.sha256(b"source").hexdigest()
            self.assertEqual(tool.stable_bytes(source, expected), b"source")
            source.write_bytes(b"drift")
            with self.assertRaises(tool.Hold):
                tool.stable_bytes(source, expected)
            link = Path(directory) / "link"; link.symlink_to(source)
            with self.assertRaises(tool.Hold):
                tool.stable_bytes(link, hashlib.sha256(b"drift").hexdigest())

    def test_override_and_disabled_admission_precede_any_inputs_or_api(self):
        with patch.dict(os.environ, {"VIRIDIS_ZENODO_API_BASE": "https://foreign.invalid"}):
            with self.assertRaisesRegex(tool.Hold, "ENDPOINT_OVERRIDE"):
                tool.admit({}, "a" * 64, SOURCE, {})
        with self.assertRaisesRegex(tool.Hold, "ACTION_DISABLED"):
            tool.admit({"schema": "VRS-067A-LABEL-METADATA-PLAN-1", "enabled": False},
                       "a" * 64, SOURCE, {})

    def test_native_accept_is_required_and_legacy_response_holds_before_write(self):
        public = fixture()[0]
        legacy = {"id": "20008839", "revision": 3, "files": [],
                  "metadata": {"description": "legacy", "keywords": ["legacy"]}}
        seen = []
        class Reply(io.BytesIO):
            status = 200
            headers = {}
        class HeaderServer:
            def open(self, request, timeout):
                seen.append((request.method, request.get_header("Accept")))
                value = public if request.get_header("Accept") == "application/vnd.inveniordm.v1+json" else legacy
                return Reply(json.dumps(value).encode())
        transport = tool.Transport("nonsecret-fixture-credential")
        transport._opener = HeaderServer()
        status, native, headers = transport.request("GET", "/api/records/20008839",
                                                    deadline=time.monotonic() + 30)
        tool.native_record(native)
        self.assertEqual(seen[-1][1], "application/vnd.inveniordm.v1+json")
        with tempfile.TemporaryDirectory() as directory, patch.object(tool, "NATIVE_ACCEPT", "application/json"):
            action, journal = self.action(directory, fixture()[1], transport)
            with self.assertRaisesRegex(tool.Hold, "NATIVE_SERIALIZER_REQUIRED"):
                action.run("apply")
            self.assertTrue(all(method == "GET" for method, accept in seen))

    def test_admission_clean_baseline_and_actual_source_binding(self):
        public, item, draft, updated, final = fixture()
        ids = ("actual_claude_pass", "full_ci_pass", "normal_main_merge", "S4_pass", "I14_pass", "independent_mapping_pass")
        sources = {name: {"path": name, "sha256": "b" * 64}
                   for name in ("policy", "direct_authority", "strike_history", "inventory", "mapping", "review")}
        sources["policy"]["sha256"] = tool.POLICY_SHA
        sources["direct_authority"]["sha256"] = tool.AUTHORITY_SHA
        plan = {"schema": "VRS-067A-LABEL-METADATA-PLAN-1", "enabled": True,
                "policy_sha256": tool.POLICY_SHA, "authority_sha256": tool.AUTHORITY_SHA,
                "max_strikes": 2, "max_seconds": 600, "preserve_all_prior_holds": True,
                "both_successors_quarantined": True, "sources": sources, "records": [item]}
        receipt = {"plan_sha256": "a" * 64,
                   "tool_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                   "main_commit": "c" * 40, "reviewed_commit": "c" * 40, "installed_commit": "c" * 40,
                   "attempts_used": 0, "quarantines_preserved": True,
                   "exact_metadata_action_authorized": True,
                   "exact_metadata_action_authority": {"path": "action_authority", "sha256": "b" * 64},
                   "allowed_modes": ["rehearse"]}
        for key in ids:
            receipt[key] = True; receipt[key + "_source_id"] = "review"
        history = {"case": "067A_CORRECTIVE_LABEL_POLICY", "max_strikes": 2,
                   "failed_attempt_source_ids": []}
        authority = {"schema": "VRS-067A-EXACT-NATIVE-ACTION-AUTHORITY-1",
                     "policy_sha256": tool.POLICY_SHA,
                     "direct_authority_sha256": tool.AUTHORITY_SHA,
                     "plan_sha256": "a" * 64, "tool_sha256": receipt["tool_sha256"],
                     "record_ids": [item["id"]], "allowed_modes": ["rehearse"]}
        def source_json(source, deadline=None):
            return authority if source["path"] == "action_authority" else history
        with patch.object(tool, "stable_bytes", return_value=b"fixture"), patch.object(tool, "source_json", side_effect=source_json):
            self.assertEqual(tool.admit(plan, "a" * 64, SOURCE, receipt), receipt)
            bad = copy.deepcopy(receipt); bad["installed_commit"] = "d" * 40
            with self.assertRaisesRegex(tool.Hold, "MERGED_SOURCE_REQUIRED"):
                tool.admit(plan, "a" * 64, SOURCE, bad)
            bad = copy.deepcopy(receipt); bad["tool_sha256"] = "0" * 64
            with self.assertRaisesRegex(tool.Hold, "INSTALL_PLAN_BINDING"):
                tool.admit(plan, "a" * 64, SOURCE, bad)
            bad = copy.deepcopy(receipt); bad["exact_metadata_action_authorized"] = False
            with self.assertRaisesRegex(tool.Hold, "EXACT_ACTION_AUTHORITY_REQUIRED"):
                tool.admit(plan, "a" * 64, SOURCE, bad)

    def test_absolute_deadline_stops_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted()
            action, journal = self.action(directory, item, transport)
            action.started = time.monotonic() - tool.ACTIVE_SECONDS - 1
            with self.assertRaises(tool.Hold):
                action.run("apply")
            self.assertEqual(transport.calls, [])

    def test_causal_public_cas_guard_omission_is_assertion_failure_not_error(self):
        def oracle(mod):
            with tempfile.TemporaryDirectory() as directory:
                item, transport = scripted(public_mutation=lambda r: r["metadata"].update(title="drift"))
                action, journal = self.action(directory, item, transport, mod=mod)
                try:
                    action.run("apply")
                except mod.Hold:
                    pass
                assert not any(m != "GET" for m, _, _ in transport.calls), "mutation before public CAS"
        oracle(tool)
        tree = ast.parse(SOURCE.read_text())
        removed = []
        class OmitPublicCAS(ast.NodeTransformer):
            def visit_Expr(self, node):
                if (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "need" and len(node.value.args) == 2
                    and isinstance(node.value.args[1], ast.Constant)
                    and node.value.args[1].value == "PUBLIC_CAS"):
                    removed.append(True)
                    return ast.copy_location(ast.Pass(), node)
                return self.generic_visit(node)
        tree = ast.fix_missing_locations(OmitPublicCAS().visit(tree))
        self.assertEqual(len(removed), 1)
        namespace = {"__name__": "causal_guard_mutant", "__file__": str(SOURCE)}
        exec(compile(tree, str(SOURCE), "exec"), namespace)
        mutant = type("Mutant", (), namespace)
        with self.assertRaises(AssertionError):
            oracle(mutant)


    def test_fixed_no_proxy_handler_ignores_hostile_ambient_settings(self):
        with patch.dict(os.environ, {"HTTPS_PROXY": "http://fixture-user:fixture-pass@proxy.invalid:3128",
                                     "HTTP_PROXY": "http://proxy.invalid:3128"}), \
             patch.object(tool.urllib.request, "build_opener") as build:
            tool.Transport("nonsecret-fixture-only")
        handlers = build.call_args.args
        self.assertEqual(len(handlers), 2)
        self.assertIsInstance(handlers[0], tool.urllib.request.ProxyHandler)
        self.assertEqual(handlers[0].proxies, {})
        self.assertIsInstance(handlers[1], tool.NoRedirect)
        self.assertFalse(any(isinstance(h, tool.urllib.request.HTTPCookieProcessor) for h in handlers))
        with self.assertRaisesRegex(tool.Hold, "REDIRECT_FORBIDDEN"):
            handlers[1].redirect_request(None, None, 302, "fixture", {}, "https://foreign.invalid")

    def test_kernel_hard_timer_precedes_soft_thread_and_survives_HOLD(self):
        # No actual timer, signal, process or thread is started by this control.
        import threading
        events, targets = [], []
        class FixtureThread:
            def __init__(self, *, target, name, daemon):
                self.target = target
                targets.append(target)
                events.append(("construct", name, daemon))
            def start(self):
                events.append(("start",))
        with patch.object(tool, "WHOLE_ACTION_STARTED", 100.0), \
             patch.object(tool, "_DEADLINE_ARMED", False), \
             patch.object(tool, "_SOFT_WATCHDOG_STARTED", False), \
             patch.object(tool, "_SOFT_REACHED", False), \
             patch.object(tool.time, "monotonic", return_value=110.0), \
             patch.object(tool.signal, "pthread_sigmask", return_value=set()), \
             patch.object(tool.signal, "getsignal", return_value=tool.signal.SIG_DFL), \
             patch.object(tool.signal, "getitimer", return_value=(0.0, 0.0)), \
             patch.object(tool.signal, "signal", side_effect=lambda *x: events.append(("handler",) + x)), \
             patch.object(tool.signal, "setitimer", side_effect=lambda *x: events.append(("timer",) + x)), \
             patch.object(threading, "Thread", FixtureThread), \
             patch.object(tool.os, "getpid", return_value=12345), \
             patch.object(tool.os, "kill") as kill, \
             patch.object(tool.time, "sleep") as sleep:
            tool._arm_cli_deadline()
            self.assertEqual(events[-1], ("timer", tool.signal.ITIMER_REAL, 580.0))
            self.assertIn(("handler", tool.signal.SIGALRM, tool.signal.SIG_DFL), events)
            tool._start_soft_watchdog()
            self.assertLess(next(i for i, e in enumerate(events) if e[0] == "timer"),
                            next(i for i, e in enumerate(events) if e[0] == "construct"))
            targets[0]()
            sleep.assert_called_once_with(530.0)
            kill.assert_called_once_with(12345, tool.signal.SIGUSR1)
            before = list(events)
            with self.assertRaisesRegex(tool.Hold, "ACTION_ACTIVE_DEADLINE"):
                tool._soft_deadline(tool.signal.SIGUSR1, None)
            self.assertTrue(tool._SOFT_REACHED)
            self.assertEqual(events, before)  # no cancellation, replacement or extension
            with self.assertRaisesRegex(tool.Hold, "SOFT_WATCHDOG_OWNERSHIP_REQUIRED"):
                tool._start_soft_watchdog()
            self.assertEqual(len(targets), 1)

    def test_signal_masks_ownership_and_nonmain_refuse_before_timer(self):
        for blocked, handler, timer, setter in (({tool.signal.SIGALRM}, tool.signal.SIG_DFL, (0.0, 0.0), None),
                ({tool.signal.SIGUSR1}, tool.signal.SIG_DFL, (0.0, 0.0), None),
                (set(), tool.signal.SIG_IGN, (0.0, 0.0), None),
                (set(), tool.signal.SIG_DFL, (1.0, 0.0), None),
                (set(), tool.signal.SIG_DFL, (0.0, 0.0), ValueError("main thread required"))):
            with self.subTest(blocked=blocked, handler=handler, timer=timer, nonmain=setter is not None), \
                 patch.object(tool, "_DEADLINE_ARMED", False), \
                 patch.object(tool.signal, "pthread_sigmask", return_value=blocked), \
                 patch.object(tool.signal, "getsignal", return_value=handler), \
                 patch.object(tool.signal, "getitimer", return_value=timer), \
                 patch.object(tool.signal, "signal", side_effect=setter), \
                 patch.object(tool.signal, "setitimer") as arm:
                with self.assertRaises(tool.Hold):
                    tool._arm_cli_deadline()
                arm.assert_not_called()
        with patch.object(tool.os, "name", "unsupported"):
            with self.assertRaisesRegex(tool.Hold, "SUPPORTED_MAIN_THREAD_POSIX_DEADLINE_REQUIRED"):
                tool._arm_cli_deadline()

    def test_input_read_is_nonblocking_bounded_and_checks_after_slow_chunk(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "bounded"; p.write_bytes(b"1234567890")
            original_open, original_read = os.open, os.read
            flags_seen = []
            def opened(path, flags):
                flags_seen.append(flags)
                return original_open(path, flags)
            with patch.object(tool.os, "open", side_effect=opened), \
                 patch.object(tool, "INPUT_CHUNK_BYTES", 3), \
                 patch.object(tool.os, "read", wraps=original_read) as read:
                self.assertEqual(tool.regular_bytes(p), b"1234567890")
                self.assertTrue(all(call.args[1] <= 3 for call in read.call_args_list))
            for flag in (os.O_NOFOLLOW, os.O_NONBLOCK, os.O_CLOEXEC):
                self.assertTrue(flags_seen[0] & flag)
            with patch.object(tool, "MAX_INPUT_BYTES", 9), patch.object(tool.os, "read") as read:
                with self.assertRaisesRegex(tool.Hold, "INPUT_NOT_BOUNDED_REGULAR"):
                    tool.regular_bytes(p)
                read.assert_not_called()
            clock = [1.0]
            def slow_read(fd, count):
                result = original_read(fd, count)
                clock[0] = 6.0
                return result
            with patch.object(tool, "WHOLE_ACTION_STARTED", 0.0), \
                 patch.object(tool.time, "monotonic", side_effect=lambda: clock[0]), \
                 patch.object(tool.os, "read", side_effect=slow_read) as read:
                with self.assertRaisesRegex(tool.Hold, "ACTION_CAP"):
                    tool.regular_bytes(p, 5.0)
                self.assertEqual(read.call_count, 1)

    def test_slow_response_cannot_complete_after_original_deadline(self):
        # Simulated elapsed I/O, not a real socket or native signal qualification.
        for is_file in (False, True):
            clock = [1.0]
            class SlowReply(io.BytesIO):
                status = 200
                headers = {}
                def read(self, size):
                    clock[0] = 6.0
                    return super().read(size)
            class FixedOpener:
                def open(self, request, timeout):
                    self.timeout = timeout
                    return SlowReply(b"{}")
            with self.subTest(is_file=is_file), patch.object(tool, "WHOLE_ACTION_STARTED", 0.0), \
                 patch.object(tool.time, "monotonic", side_effect=lambda: clock[0]):
                transport = tool.Transport("fixture-only")
                transport._opener = FixedOpener()
                with self.assertRaisesRegex(tool.Hold, "ACTION_CAP"):
                    transport.request("GET", "/api/records/20008839/files/paper.pdf/content" if is_file
                                      else "/api/records/20008839", deadline=5.0,
                                      file_size=2 if is_file else None)
                self.assertEqual(transport._opener.timeout, 4.0)


    def test_acyclic_admission_uses_real_fixture_files_and_rejects_foreign_authority(self):
        # TEST_ONLY data, no actual audit/PASS/installation/authority is fabricated.
        # Readers and hashes are REAL here; only the fixed policy roots are
        # replaced by clearly synthetic roots within this disposable fixture.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(strict=True)
            def store(name, value):
                raw = value if isinstance(value, bytes) else tool.canonical(value)
                path = root / name
                path.write_bytes(raw)
                return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
            policy = store("policy.json", {"TEST_ONLY": "policy fixture"})
            direct = store("direct.json", {"TEST_ONLY": "direct authority fixture"})
            history = store("history.json", {"case": "067A_CORRECTIVE_LABEL_POLICY",
                                             "max_strikes": 2, "failed_attempt_source_ids": []})
            sources = {"policy": policy, "direct_authority": direct, "strike_history": history,
                       "inventory": store("inventory.json", {"TEST_ONLY": "inventory"}),
                       "mapping": store("mapping.json", {"TEST_ONLY": "mapping"}),
                       "review": store("review.json", {"TEST_ONLY": "not actual gate approval"})}
            item = fixture()[1]
            plan = {"schema": "VRS-067A-LABEL-METADATA-PLAN-1", "enabled": True,
                    "policy_sha256": policy["sha256"], "authority_sha256": direct["sha256"],
                    "max_strikes": 2, "max_seconds": 600, "preserve_all_prior_holds": True,
                    "both_successors_quarantined": True, "sources": sources, "records": [item]}
            plan_source = store("plan.json", plan)
            receipt = {"plan_sha256": plan_source["sha256"],
                       "tool_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                       "main_commit": "c" * 40, "reviewed_commit": "c" * 40,
                       "installed_commit": "c" * 40, "attempts_used": 0,
                       "quarantines_preserved": True, "exact_metadata_action_authorized": True,
                       "allowed_modes": ["rehearse"]}
            for key in ("actual_claude_pass", "full_ci_pass", "normal_main_merge", "S4_pass",
                        "I14_pass", "independent_mapping_pass"):
                receipt[key] = True
                receipt[key + "_source_id"] = "review"
            authority = {"schema": "VRS-067A-EXACT-NATIVE-ACTION-AUTHORITY-1",
                         "policy_sha256": policy["sha256"],
                         "direct_authority_sha256": direct["sha256"],
                         "plan_sha256": plan_source["sha256"],
                         "tool_sha256": receipt["tool_sha256"], "record_ids": [item["id"]],
                         "allowed_modes": ["rehearse"]}
            receipt["exact_metadata_action_authority"] = store("exact-authority.json", authority)
            self.assertNotIn("exact_metadata_action_authority", sources)
            with patch.object(tool, "POLICY_SHA", policy["sha256"]), \
                 patch.object(tool, "AUTHORITY_SHA", direct["sha256"]):
                self.assertEqual(tool.admit(plan, plan_source["sha256"], SOURCE, receipt), receipt)
                for field, value in (("schema", "FOREIGN"), ("plan_sha256", "d" * 64),
                                     ("direct_authority_sha256", "e" * 64),
                                     ("allowed_modes", ["apply"])):
                    foreign = copy.deepcopy(authority)
                    foreign[field] = value
                    candidate = copy.deepcopy(receipt)
                    candidate["exact_metadata_action_authority"] = store("foreign-authority.json", foreign)
                    with self.subTest(field=field), self.assertRaisesRegex(tool.Hold, "EXACT_ACTION_AUTHORITY_BINDING"):
                        tool.admit(plan, plan_source["sha256"], SOURCE, candidate)
                bad = copy.deepcopy(receipt)
                bad["attempts_used"] = False
                with self.assertRaisesRegex(tool.Hold, "ATTEMPTS_EXHAUSTED"):
                    tool.admit(plan, plan_source["sha256"], SOURCE, bad)
                bad = copy.deepcopy(receipt)
                bad["actual_claude_pass"] = False
                with self.assertRaisesRegex(tool.Hold, "FRESH_REVIEW_ADMISSION_REQUIRED"):
                    tool.admit(plan, plan_source["sha256"], SOURCE, bad)
                Path(receipt["exact_metadata_action_authority"]["path"]).write_bytes(b"changed")
                with self.assertRaisesRegex(tool.Hold, "INPUT_HASH_DRIFT"):
                    tool.admit(plan, plan_source["sha256"], SOURCE, receipt)


    def test_native_metadata_and_anonymous_file_headers_are_distinct(self):
        public = fixture()[0]
        raw = b"immutable fixture binary"
        seen = []
        class Reply(io.BytesIO):
            status = 200
            headers = {}
        class HeaderSensitive:
            def open(self, request, timeout):
                headers = dict(request.header_items())
                seen.append((request.full_url, headers))
                if request.full_url.endswith("/content"):
                    assert headers.get("Accept") == "*/*"
                    assert headers.get("Accept-encoding") == "identity"
                    assert "Authorization" not in headers
                    return Reply(raw)
                assert headers.get("Accept") == tool.NATIVE_ACCEPT
                assert "Accept-encoding" not in headers
                return Reply(json.dumps(public).encode())
        transport = tool.Transport("nonsecret-fixture-only")
        transport._opener = HeaderSensitive()
        _, value, _ = transport.request("GET", "/api/records/20008839",
                                        deadline=time.monotonic() + 10)
        tool.native_record(value)
        _, value, _ = transport.request("GET", "/api/records/20008839/files/paper.pdf/content",
                                        file_size=len(raw), deadline=time.monotonic() + 10)
        self.assertEqual(value, {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        self.assertEqual(len(seen), 2)
        with self.assertRaisesRegex(tool.Hold, "ANONYMOUS_FILE_SIZE_REQUIRED"):
            transport.request("GET", "/api/records/20008839/files/paper.pdf/content",
                              authenticated=True, file_size=len(raw), deadline=time.monotonic() + 10)
        self.assertEqual(len(seen), 2)

    def test_file_406_poison_has_no_mutation_or_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            item, transport = scripted()
            transport.responses[1] = response(status=406)
            action, journal = self.action(directory, item, transport)
            with self.assertRaisesRegex(tool.Hold, "HTTP_406"):
                action.run("apply")
            self.assertEqual(journal.value["first_failure"], "HTTP_406")
            self.assertEqual(len(transport.calls), 2)
            self.assertTrue(all(method == "GET" for method, _, _ in transport.calls))
            with self.assertRaisesRegex(tool.Hold, "ACTION_POISONED"):
                action.call("GET", action.base, {200})
            self.assertEqual(len(transport.calls), 2)


if __name__ == "__main__":
    unittest.main()
