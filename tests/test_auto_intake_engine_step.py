"""Engine step (tools/auto_intake/engine_step.sh), run against a fake gh and local git remotes.

Invariants checked:
  R1 a canon release is published only when canon main's live-kernel files differ from the
     newest canon-v release (auto-intake merge, rollback or revert alike)
  R2 at most one release per day; an existing tag is never overwritten
  S1 the site moves only to a released bundle that already carries its DIGEST, read offline from
     what the fetch phase downloaded
  S2 the site moves only through the app's own scripts/sync-canon-bundle.sh, on a branch with a PR,
     never on main
  S3 an up-to-date site, or one without a sync script that reads CANON_ASSETS_DIR, is left alone
  AI-9 the build phase refuses to run with any credential in reach; the publish phase opens a PR
     only for a patch inside that change's allowed paths, and without PHASE nothing drafts
  AI-10 red, missing or stalled checks, and every refusal, are ALERT lines and lines in $AI_ALERTS
"""
import datetime
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "tools" / "auto_intake" / "engine_step.sh"
CRED = re.compile(r"TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|CREDENTIAL")

FAKE_GH = r"""#!/usr/bin/env bash
# Minimal gh stand-in: answers only what engine_step.sh asks.
echo "gh $*" >> "$FAKE_LOG"
args=" $* "
case "$1 $2" in
  "release list") [ -n "${FAKE_LATEST:-}" ] && echo "$FAKE_LATEST ${FAKE_LATEST_AT:-2026-11-14T00:00:00Z}";;
  "release view")
    tag="$3"
    if [[ "$args" == *" --json assets "* ]]; then
      for a in ${FAKE_ASSETS:-}; do echo "$a"; done
    else
      [[ " ${FAKE_EXISTING:-} ${FAKE_LATEST:-} " == *" $tag "* ]] || exit 1
    fi;;
  "release create") echo "created $3" >> "$FAKE_LOG";;
  "release download")
    dir=""; prev=""
    for a in "$@"; do [ "$prev" = "-D" ] && dir="$a"; prev="$a"; done
    mkdir -p "$dir"; for a in ${FAKE_ASSETS:-}; do echo "asset $a" > "$dir/$a"; done;;
  "pr list")
    if [[ "$args" == *"number,createdAt"* ]]; then printf '%s\n' "${FAKE_PRS:-}" | sed '/^$/d'; fi;;
  "pr checks") printf '%s' "${FAKE_CHECKS:-}";;
  "pr merge") echo "merged $3" >> "$FAKE_LOG";;
  "pr create")
    prev=""; for a in "$@"; do
      [ "$prev" = "--title" ] && echo "title: $a" >> "$FAKE_LOG"
      [ "$prev" = "--body-file" ] && { echo "body:" >> "$FAKE_LOG"; cat "$a" >> "$FAKE_LOG"; }
      prev="$a"; done
    echo "pr-created" >> "$FAKE_LOG";;
  *) echo "unexpected gh call: $*" >&2; exit 2;;
esac
"""

SYNC = """#!/usr/bin/env bash
# fake site sync script: pins the canon release tag in os-bundle/pin, from $CANON_ASSETS_DIR
set -e
if [ "$1" = "--check" ]; then [ "$(cat os-bundle/pin 2>/dev/null)" = "$2" ]; exit $?; fi
[ -f "$CANON_ASSETS_DIR/os-bundle-$1.DIGEST" ]
mkdir -p os-bundle && echo "$1" > os-bundle/pin
"""


def sh(*args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        gitcfg = self.tmp / "gitconfig"
        gitcfg.write_text("[user]\n\tname = Test\n\temail = test@example.invalid\n[init]\n\tdefaultBranch = main\n")
        bindir = self.tmp / "bin"
        bindir.mkdir()
        (bindir / "gh").write_text(FAKE_GH)
        (bindir / "gh").chmod(0o755)
        home = self.tmp / "home"
        home.mkdir()
        self.log = self.tmp / "gh.log"
        self.log.write_text("")
        self.alerts = self.tmp / "alerts"
        base = {k: v for k, v in os.environ.items()
                if not CRED.search(k) and not k.startswith(("GIT_CONFIG_", "GIT_ASKPASS", "SSH_"))}
        self.env = dict(base, GIT_CONFIG_GLOBAL=str(gitcfg), GIT_CONFIG_NOSYSTEM="1", HOME=str(home),
                        PATH=f"{bindir}:{os.environ['PATH']}", FAKE_LOG=str(self.log),
                        GIT_REMOTE_BASE="file://" + str(self.tmp / "gh"), AI_ALERTS=str(self.alerts))
        for k in ("PHASE", "STEPS", "SITE", "VIRIDISOS", "RESEARCH", "AI_IN", "AI_OUT"):
            self.env.pop(k, None)

    def origin(self, repo, files):
        """bare origin at <tmp>/gh/<repo>.git with one commit of files; returns (origin, clone)"""
        origin = self.tmp / "gh" / f"{repo}.git"
        origin.parent.mkdir(parents=True, exist_ok=True)
        seed = self.tmp / "seed" / repo
        sh("git", "init", "-q", "--bare", str(origin), env=self.env)
        sh("git", "init", "-q", str(seed), env=self.env)
        for rel, text in files.items():
            (seed / rel).parent.mkdir(parents=True, exist_ok=True)
            (seed / rel).write_text(text)
        sh("git", "add", "-A", cwd=seed, env=self.env)
        sh("git", "commit", "-qm", "seed", cwd=seed, env=self.env)
        sh("git", "remote", "add", "origin", str(origin), cwd=seed, env=self.env)
        sh("git", "push", "-q", "-u", "origin", "main", "--tags", cwd=seed, env=self.env)
        clone = self.tmp / "work" / repo
        sh("git", "clone", "-q", str(origin), str(clone), env=self.env)
        return origin, clone

    def run_step(self, phase, steps, **extra):
        env = dict(self.env, STEPS=steps, **extra)
        if phase:
            env["PHASE"] = phase
        return subprocess.run(["bash", str(STEP)], env=env, capture_output=True, text=True)

    def alert_text(self):
        return self.alerts.read_text() if self.alerts.exists() else ""


class Release(Base):
    def canon(self, change_after_tag):
        origin, _ = self.origin("jdhart81/viridis-canon", {"os/core.json": '{"function_order": ["a"]}\n', "README.md": "x\n"})
        seed = self.tmp / "seed" / "jdhart81/viridis-canon"
        sh("git", "tag", "canon-v2026.11.14", cwd=seed, env=self.env)
        if change_after_tag == "kernel":
            (seed / "os" / "core.json").write_text('{"function_order": ["a", "b"]}\n')
        else:
            (seed / "README.md").write_text("y\n")
        sh("git", "commit", "-qam", "two", cwd=seed, env=self.env)
        sh("git", "push", "-q", "origin", "main", "--tags", cwd=seed, env=self.env)
        clone = self.tmp / "canon"
        sh("git", "clone", "-q", str(origin), str(clone), env=self.env)
        return clone

    def test_release_published_when_live_kernels_changed(self):
        out = self.run_step("fetch", "R", CANON=str(self.canon("kernel")), FAKE_LATEST="canon-v2026.11.14",
                            FAKE_ASSETS="os-bundle-canon-v2026.11.14.DIGEST")
        self.assertEqual(out.returncode, 0, out.stderr)
        today = datetime.datetime.now(datetime.timezone.utc).strftime("canon-v%Y.%m.%d")
        self.assertIn(f"created {today}", self.log.read_text())

    def test_no_release_when_only_other_files_changed(self):
        out = self.run_step("fetch", "R", CANON=str(self.canon("readme")), FAKE_LATEST="canon-v2026.11.14",
                            FAKE_ASSETS="os-bundle-canon-v2026.11.14.DIGEST")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("release create", self.log.read_text())
        self.assertEqual(self.alert_text(), "")

    def test_existing_release_tag_is_never_overwritten(self):
        today = datetime.datetime.now(datetime.timezone.utc).strftime("canon-v%Y.%m.%d")
        out = self.run_step("fetch", "R", CANON=str(self.canon("kernel")), FAKE_LATEST="canon-v2026.11.14",
                            FAKE_EXISTING=today, FAKE_ASSETS="os-bundle-canon-v2026.11.14.DIGEST")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("release create", self.log.read_text())
        self.assertIn("already exists", out.stdout)

    def test_release_without_digest_raises_an_alert(self):
        out = self.run_step("fetch", "R", CANON=str(self.canon("readme")), FAKE_LATEST="canon-v2026.11.14",
                            FAKE_ASSETS="os-bundle-canon-v2026.11.14.tar.gz")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("has no bundle DIGEST", self.alert_text())


class Sweep(Base):
    def run_sweep(self, checks, hours_old):
        created = "2026-11-17T00:00:00Z"
        now = int(datetime.datetime(2026, 11, 17, tzinfo=datetime.timezone.utc).timestamp()) + hours_old * 3600
        if not hasattr(self, "canon_dir"):
            _, self.canon_dir = self.origin("jdhart81/viridis-canon", {"README.md": "x\n"})
        return self.run_step("fetch", "A", CANON=str(self.canon_dir), FAKE_PRS=f"7 {created}", FAKE_CHECKS=checks,
                             NOW_EPOCH=str(now))

    def test_green_pr_is_merged(self):
        out = self.run_sweep("SUCCESS", 1)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("merged 7", self.log.read_text())
        self.assertEqual(self.alert_text(), "")

    def test_red_pr_raises_an_alert_and_is_not_merged(self):
        out = self.run_sweep("FAILURE,SUCCESS", 1)
        self.assertNotIn("merged 7", self.log.read_text())
        self.assertIn("failing checks", self.alert_text())

    def test_pr_with_no_checks_alerts_once_stalled(self):
        self.run_sweep("", 2)
        self.assertEqual(self.alert_text(), "", "young PR without checks should only wait")
        self.run_sweep("", 13)
        self.assertIn("no checks have run", self.alert_text())

    def test_pending_checks_alert_once_stalled(self):
        self.run_sweep("PENDING", 30)
        self.assertIn("waited 30h", self.alert_text())


class Phases(Base):
    def test_without_phase_only_sweep_and_release_run(self):
        _, canon = self.origin("jdhart81/viridis-canon", {"README.md": "x\n"})
        out = self.run_step(None, "A R B S C D", CANON=str(canon))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("without PHASE", self.alert_text())
        self.assertNotIn("VIRIDISOS", out.stderr)  # B never started

    def test_build_refuses_with_a_token_in_its_environment(self):
        _, canon = self.origin("jdhart81/viridis-canon", {"README.md": "x\n"})
        for var in ("GH_TOKEN", "AUTO_INTAKE_TOKEN", "RECORD_SECRET"):
            out = self.run_step("build", "D", CANON=str(canon), AI_IN=str(self.tmp / "in"), AI_OUT=str(self.tmp / "out"),
                                **{var: "x"})
            self.assertEqual(out.returncode, 3, var)
            self.assertIn("credentials in its environment", out.stdout)

    def test_build_refuses_when_a_checkout_stores_credentials(self):
        _, canon = self.origin("jdhart81/viridis-canon", {"README.md": "x\n"})
        sh("git", "config", "http.https://github.com/.extraheader", "AUTHORIZATION: basic x", cwd=canon, env=self.env)
        out = self.run_step("build", "D", CANON=str(canon), AI_IN=str(self.tmp / "in"), AI_OUT=str(self.tmp / "out"))
        self.assertEqual(out.returncode, 3)
        self.assertIn("stores git credentials", out.stdout)

    def test_build_refuses_a_linked_worktree_whose_shared_config_holds_credentials(self):
        _, canon = self.origin("jdhart81/viridis-canon", {"README.md": "x\n"})
        sh("git", "config", "http.https://github.com/.extraheader", "AUTHORIZATION: basic x", cwd=canon, env=self.env)
        wt = self.tmp / "worktree"
        sh("git", "worktree", "add", "-q", "--detach", str(wt), cwd=canon, env=self.env)
        self.assertTrue((wt / ".git").is_file())
        out = self.run_step("build", "D", CANON=str(wt), AI_IN=str(self.tmp / "in"), AI_OUT=str(self.tmp / "out"))
        self.assertEqual(out.returncode, 3)
        self.assertIn("stores git credentials", out.stdout)

    def test_build_refuses_a_token_in_a_remote_url(self):
        _, canon = self.origin("jdhart81/viridis-canon", {"README.md": "x\n"})
        sh("git", "remote", "set-url", "origin", "https://x-access-token:abc@github.com/a/b.git", cwd=canon, env=self.env)
        out = self.run_step("build", "D", CANON=str(canon), AI_IN=str(self.tmp / "in"), AI_OUT=str(self.tmp / "out"))
        self.assertEqual(out.returncode, 3)

    def test_build_refuses_when_gh_is_logged_in(self):
        _, canon = self.origin("jdhart81/viridis-canon", {"README.md": "x\n"})
        hosts = Path(self.env["HOME"]) / ".config" / "gh" / "hosts.yml"
        hosts.parent.mkdir(parents=True)
        hosts.write_text("github.com: {}\n")
        out = self.run_step("build", "D", CANON=str(canon), AI_IN=str(self.tmp / "in"), AI_OUT=str(self.tmp / "out"))
        self.assertEqual(out.returncode, 3)


class Site(Base):
    TAG = "canon-v2026.11.14"

    def setup_site(self, pinned, script=SYNC):
        _, canon = self.origin("jdhart81/viridis-canon", {"README.md": "x\n"})
        files = {"os-bundle/pin": pinned + "\n", "app.txt": "app\n"}
        if script is not None:
            files["scripts/sync-canon-bundle.sh"] = script
        origin, site = self.origin("jdhart81/viridis-conservation-app", files)
        if script is not None:
            (site / "scripts" / "sync-canon-bundle.sh").chmod(0o755)
        return canon, origin, site

    def three_phases(self, canon, site, assets):
        common = dict(CANON=str(canon), SITE=str(site), AI_IN=str(self.tmp / "in"), AI_OUT=str(self.tmp / "out"),
                      FAKE_LATEST=self.TAG, FAKE_ASSETS=assets)
        outs = [self.run_step(p, "S", **common) for p in ("fetch", "build", "publish")]
        for o in outs:
            self.assertEqual(o.returncode, 0, o.stdout + o.stderr)
        return outs

    def test_site_moves_to_released_bundle_with_digest_on_a_branch(self):
        canon, origin, site = self.setup_site("canon-v2026.11.13")
        self.three_phases(canon, site, f"os-bundle-{self.TAG}.tar.gz os-bundle-{self.TAG}.DIGEST")
        log = self.log.read_text()
        self.assertIn("pr-created", log)
        self.assertIn(f"title: Auto-intake: take canon bundle {self.TAG}", log)
        branches = sh("git", "branch", "--list", "--format=%(refname:short)", cwd=origin, env=self.env).split()
        self.assertIn(f"auto-intake/site-{self.TAG}", branches)
        self.assertEqual(sh("git", "show", "main:os-bundle/pin", cwd=origin, env=self.env).strip(), "canon-v2026.11.13")
        self.assertEqual(sh("git", "show", f"auto-intake/site-{self.TAG}:os-bundle/pin", cwd=origin, env=self.env).strip(), self.TAG)

    def test_site_waits_while_release_has_no_digest(self):
        canon, _, site = self.setup_site("canon-v2026.11.13")
        outs = self.three_phases(canon, site, f"os-bundle-{self.TAG}.tar.gz")
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("site stays pinned", outs[1].stdout)

    def test_up_to_date_site_is_left_alone(self):
        canon, _, site = self.setup_site(self.TAG)
        self.three_phases(canon, site, f"os-bundle-{self.TAG}.DIGEST")
        self.assertNotIn("pr-created", self.log.read_text())

    def test_site_without_sync_script_is_left_alone(self):
        canon, _, site = self.setup_site("canon-v2026.11.13", script=None)
        outs = self.three_phases(canon, site, f"os-bundle-{self.TAG}.DIGEST")
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("no scripts/sync-canon-bundle.sh", outs[1].stdout)

    def test_site_with_an_online_only_sync_script_alerts(self):
        canon, _, site = self.setup_site("canon-v2026.11.13", script="#!/usr/bin/env bash\nexit 0\n")
        self.three_phases(canon, site, f"os-bundle-{self.TAG}.DIGEST")
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("CANON_ASSETS_DIR", self.alert_text())


    def test_sync_script_never_sees_the_claude_credential(self):
        spy = SYNC.replace("set -e\n", "set -e\nenv > \"$SPY\"\n")
        canon, _, site = self.setup_site("canon-v2026.11.13", script=spy)
        self.env.update(SPY=str(self.tmp / "spy-env"), CLAUDE_CODE_OAUTH_TOKEN="claude-secret")
        self.three_phases(canon, site, f"os-bundle-{self.TAG}.DIGEST")
        self.assertIn("pr-created", self.log.read_text())
        self.assertNotIn("claude-secret", (self.tmp / "spy-env").read_text())


class Publish(Base):
    """The publish phase applies only patches inside the change's allowed paths (AI-9)."""
    CANON_FILES = {"os/research_statements.json": "{}\n", "os/core.json": "{}\n", "README.md": "x\n",
                   "canon_core/__init__.py": "\n", "research/old-kernel/runner.py": "print(1)\n"}

    def change(self, kind, repo, files, mutate, branch):
        origin, clone = self.origin(repo, files)
        mutate(clone)
        sh("git", "add", "-A", cwd=clone, env=self.env)
        out = self.tmp / "out" / kind
        out.mkdir(parents=True)
        (out / "branch").write_text(branch + "\n")
        (out / "patch").write_bytes(subprocess.run(["git", "diff", "--cached", "--binary", "HEAD"], cwd=clone,
                                                   env=self.env, check=True, capture_output=True).stdout)
        (out / "body").write_text("note from the build\n")
        return origin

    def publish(self, **extra):
        _, canon = self.origin("jdhart81/canon-runner-copy", {"README.md": "x\n"})
        out = self.run_step("publish", "", CANON=str(canon), AI_OUT=str(self.tmp / "out"), **extra)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        return out

    def canon_change(self, mutate, branch="auto-intake/P3.CascadedRecovery"):
        return self.change("canon", "jdhart81/viridis-canon", self.CANON_FILES, mutate, branch)

    @staticmethod
    def write(root, rel, text="x\n"):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def entry(self, clone, extra=()):
        self.write(clone, "research/cascaded-recovery/runner.py", "print('k')\n")
        self.write(clone, "research/cascaded-recovery/proof/Main.lean", "theorem t : True := trivial\n")
        self.write(clone, "tests/test_os_auto_cascaded_recovery.py", "\n")
        self.write(clone, "os/research_statements.json", '{"P3": 1}\n')
        self.write(clone, "os/core.json", '{"a": 1}\n')
        self.write(clone, "README.md", "y\n")
        for rel in extra:
            self.write(clone, rel)

    def assert_refused(self, why):
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("refused the canon change", self.alert_text())
        self.assertIn(why, self.alert_text())

    def test_valid_entry_is_published_with_a_fixed_title(self):
        origin = self.canon_change(self.entry)
        self.publish()
        log = self.log.read_text()
        self.assertIn("title: Auto-intake: P3.CascadedRecovery → cascaded-recovery", log)
        self.assertIn("note from the build", log)
        self.assertIn("auto-intake/P3.CascadedRecovery",
                      sh("git", "branch", "--list", "--format=%(refname:short)", cwd=origin, env=self.env))
        msg = sh("git", "log", "-1", "--format=%s", "auto-intake/P3.CascadedRecovery", cwd=origin, env=self.env).strip()
        self.assertEqual(msg, "auto-intake: P3.CascadedRecovery enters as cascaded-recovery")
        self.assertEqual(self.alert_text(), "")

    def test_decline_touching_only_the_ledger_is_published(self):
        self.canon_change(lambda c: self.write(c, "os/research_statements.json", '{"P3": "declined"}\n'))
        self.publish()
        self.assertIn("title: Auto-intake: P3.CascadedRecovery not entered", self.log.read_text())

    def test_workflow_file_is_refused(self):
        self.canon_change(lambda c: self.entry(c, [".github/workflows/x.yml"]))
        self.publish()
        self.assert_refused("touches .github/workflows/x.yml")

    def test_core_code_is_refused(self):
        self.canon_change(lambda c: self.entry(c, ["canon_core/evil.py"]))
        self.publish()
        self.assert_refused("touches canon_core/evil.py")

    def test_two_packages_are_refused(self):
        self.canon_change(lambda c: self.entry(c, ["research/second-one/runner.py"]))
        self.publish()
        self.assert_refused("more than one package")

    def test_mismatched_test_name_is_refused(self):
        self.canon_change(lambda c: self.entry(c, ["tests/test_os_auto_other.py"]))
        self.publish()
        self.assert_refused("touches tests/test_os_auto_other.py")

    def test_symlink_is_refused(self):
        def mutate(c):
            self.entry(c)
            os.symlink("/etc/passwd", c / "research" / "cascaded-recovery" / "link")
        self.canon_change(mutate)
        self.publish()
        self.assert_refused("symlink")

    def test_deletion_is_refused(self):
        self.canon_change(lambda c: (c / "research" / "old-kernel" / "runner.py").unlink())
        self.publish()
        self.assert_refused("deletions")

    def test_decline_touching_more_than_the_ledger_is_refused(self):
        def mutate(c):
            self.write(c, "os/research_statements.json", '{"P3": "declined"}\n')
            self.write(c, "README.md", "changed\n")
        self.canon_change(mutate)
        self.publish()
        self.assert_refused("only the ledger")

    def test_bad_branch_name_is_refused(self):
        self.canon_change(self.entry, branch="main")
        self.publish()
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("unusable branch name", self.alert_text())

    def test_viridisos_may_touch_only_the_kernel_file(self):
        self.change("viridisos", "jdhart81/viridisos", {"runtime/canon_auto_kernels.json": "{}\n", "run.py": "\n"},
                    lambda c: self.write(c, "run.py", "import os\n"), "auto-intake/os-refresh-abc1234")
        self.publish()
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("refused the viridisos change", self.alert_text())

    def test_site_may_touch_only_the_bundle(self):
        self.change("site", "jdhart81/viridis-conservation-app", {"os-bundle/pin": "a\n", "package.json": "{}\n"},
                    lambda c: self.write(c, "package.json", '{"scripts": {}}\n'), "auto-intake/site-canon-v2026.11.14")
        self.publish(FAKE_ASSETS="os-bundle-canon-v2026.11.14.DIGEST")
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("outside os-bundle/", self.alert_text())

    def test_build_output_with_a_symlink_publishes_nothing(self):
        self.canon_change(self.entry)
        os.symlink("/etc/passwd", self.tmp / "out" / "canon" / "extra")
        self.publish()
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("holds a symlink", self.alert_text())


class Script(unittest.TestCase):
    def test_script_parses(self):
        subprocess.run(["bash", "-n", str(STEP)], check=True)


if __name__ == "__main__":
    unittest.main()
