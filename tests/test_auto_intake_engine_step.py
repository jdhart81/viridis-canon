"""Engine-step release (R) and site (S) hops, run against a fake gh and local git remotes.

Invariants checked:
  R1 a canon release is published only when canon main's live-kernel files differ from the
     newest canon-v release (auto-intake merge, rollback or revert alike)
  R2 at most one release per day; an existing tag is never overwritten
  S1 the site moves only to a released bundle that already carries its DIGEST
  S2 the site moves only through the app's own scripts/sync-canon-bundle.sh, on a branch with a PR,
     never on main
  S3 an up-to-date site, or one without the sync script, is left alone
"""
import datetime
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "tools" / "auto_intake" / "engine_step.sh"

FAKE_GH = r"""#!/usr/bin/env bash
# Minimal gh stand-in: answers only what engine_step.sh steps R and S ask.
echo "gh $*" >> "$FAKE_LOG"
case "$1 $2" in
  "release list") echo "${FAKE_LATEST:-}";;
  "release view")
    tag="$3"
    if [[ " $* " == *" --json assets "* ]]; then
      for a in ${FAKE_ASSETS:-}; do echo "$a"; done
    else
      [[ " ${FAKE_EXISTING:-} ${FAKE_LATEST:-} " == *" $tag "* ]] || exit 1
    fi;;
  "release create") echo "created $3" >> "$FAKE_LOG";;
  "pr list") ;;
  "pr create") echo "pr-created" >> "$FAKE_LOG";;
  *) echo "unexpected gh call: $*" >&2; exit 2;;
esac
"""

SYNC = """#!/usr/bin/env bash
# fake site sync script: pins the canon release tag in canon-bundle.pin
set -e
if [ "$1" = "--check" ]; then [ "$(cat canon-bundle.pin 2>/dev/null)" = "$2" ]; exit $?; fi
echo "$1" > canon-bundle.pin
"""


def sh(*args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout


class EngineStepHops(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        gitcfg = self.tmp / "gitconfig"
        gitcfg.write_text("[user]\n\tname = Test\n\temail = test@example.invalid\n[init]\n\tdefaultBranch = main\n")
        bindir = self.tmp / "bin"
        bindir.mkdir()
        (bindir / "gh").write_text(FAKE_GH)
        (bindir / "gh").chmod(0o755)
        self.log = self.tmp / "gh.log"
        self.log.write_text("")
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=str(gitcfg), GIT_CONFIG_NOSYSTEM="1",
                        PATH=f"{bindir}:{os.environ['PATH']}", FAKE_LOG=str(self.log))
        self.env.pop("GH_TOKEN", None)

    # canon origin with tag canon-v2026.11.14 on the first commit
    def canon(self, change_after_tag):
        origin = self.tmp / "canon-origin.git"
        work = self.tmp / "canon-seed"
        sh("git", "init", "-q", "--bare", str(origin), env=self.env)
        sh("git", "init", "-q", str(work), env=self.env)
        (work / "os").mkdir()
        (work / "os" / "core.json").write_text('{"function_order": ["a"]}\n')
        (work / "README.md").write_text("x\n")
        sh("git", "add", "-A", cwd=work, env=self.env)
        sh("git", "commit", "-qm", "one", cwd=work, env=self.env)
        sh("git", "tag", "canon-v2026.11.14", cwd=work, env=self.env)
        if change_after_tag == "kernel":
            (work / "os" / "core.json").write_text('{"function_order": ["a", "b"]}\n')
        else:
            (work / "README.md").write_text("y\n")
        sh("git", "commit", "-qam", "two", cwd=work, env=self.env)
        sh("git", "remote", "add", "origin", str(origin), cwd=work, env=self.env)
        sh("git", "push", "-q", "origin", "main", "--tags", cwd=work, env=self.env)
        clone = self.tmp / "canon"
        sh("git", "clone", "-q", str(origin), str(clone), env=self.env)
        return clone

    def site(self, pinned, with_script=True):
        origin = self.tmp / "site-origin.git"
        work = self.tmp / "site"
        sh("git", "init", "-q", "--bare", str(origin), env=self.env)
        sh("git", "init", "-q", str(work), env=self.env)
        (work / "canon-bundle.pin").write_text(pinned + "\n")
        if with_script:
            (work / "scripts").mkdir()
            (work / "scripts" / "sync-canon-bundle.sh").write_text(SYNC)
            (work / "scripts" / "sync-canon-bundle.sh").chmod(0o755)
        sh("git", "add", "-A", cwd=work, env=self.env)
        sh("git", "commit", "-qm", "site", cwd=work, env=self.env)
        sh("git", "remote", "add", "origin", str(origin), cwd=work, env=self.env)
        sh("git", "push", "-q", "-u", "origin", "main", cwd=work, env=self.env)
        return work, origin

    def run_step(self, steps, **extra):
        env = dict(self.env, STEPS=steps, **extra)
        return subprocess.run(["bash", str(STEP)], env=env, capture_output=True, text=True)

    # R ------------------------------------------------------------------------------------
    def test_release_published_when_live_kernels_changed(self):
        canon = self.canon("kernel")
        out = self.run_step("R", CANON=str(canon), FAKE_LATEST="canon-v2026.11.14")
        self.assertEqual(out.returncode, 0, out.stderr)
        today = datetime.datetime.now(datetime.timezone.utc).strftime("canon-v%Y.%m.%d")
        self.assertIn(f"created {today}", self.log.read_text())

    def test_no_release_when_only_other_files_changed(self):
        canon = self.canon("readme")
        out = self.run_step("R", CANON=str(canon), FAKE_LATEST="canon-v2026.11.14")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("release create", self.log.read_text())

    def test_existing_release_tag_is_never_overwritten(self):
        canon = self.canon("kernel")
        today = datetime.datetime.now(datetime.timezone.utc).strftime("canon-v%Y.%m.%d")
        out = self.run_step("R", CANON=str(canon), FAKE_LATEST="canon-v2026.11.14", FAKE_EXISTING=today)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("release create", self.log.read_text())
        self.assertIn("already exists", out.stdout)

    # S ------------------------------------------------------------------------------------
    def test_site_moves_to_released_bundle_with_digest_on_a_branch(self):
        canon = self.canon("readme")
        site, origin = self.site("canon-v2026.11.13")
        out = self.run_step("S", CANON=str(canon), SITE=str(site), FAKE_LATEST="canon-v2026.11.14",
                            FAKE_ASSETS="os-bundle-canon-v2026.11.14.tar.gz os-bundle-canon-v2026.11.14.DIGEST")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("pr-created", self.log.read_text())
        branches = sh("git", "branch", "--list", "--format=%(refname:short)", cwd=origin, env=self.env).split()
        self.assertIn("auto-intake/site-canon-v2026.11.14", branches)
        main_pin = sh("git", "show", "main:canon-bundle.pin", cwd=origin, env=self.env).strip()
        self.assertEqual(main_pin, "canon-v2026.11.13", "site main must not move without a PR")
        branch_pin = sh("git", "show", "auto-intake/site-canon-v2026.11.14:canon-bundle.pin", cwd=origin, env=self.env).strip()
        self.assertEqual(branch_pin, "canon-v2026.11.14")

    def test_site_waits_while_release_has_no_digest(self):
        canon = self.canon("readme")
        site, _ = self.site("canon-v2026.11.13")
        out = self.run_step("S", CANON=str(canon), SITE=str(site), FAKE_LATEST="canon-v2026.11.14",
                            FAKE_ASSETS="os-bundle-canon-v2026.11.14.tar.gz")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("site stays pinned", out.stdout)

    def test_up_to_date_site_is_left_alone(self):
        canon = self.canon("readme")
        site, _ = self.site("canon-v2026.11.14")
        out = self.run_step("S", CANON=str(canon), SITE=str(site), FAKE_LATEST="canon-v2026.11.14",
                            FAKE_ASSETS="os-bundle-canon-v2026.11.14.DIGEST")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("pr-created", self.log.read_text())

    def test_site_without_sync_script_is_left_alone(self):
        canon = self.canon("readme")
        site, _ = self.site("canon-v2026.11.13", with_script=False)
        out = self.run_step("S", CANON=str(canon), SITE=str(site), FAKE_LATEST="canon-v2026.11.14",
                            FAKE_ASSETS="os-bundle-canon-v2026.11.14.DIGEST")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("pr-created", self.log.read_text())
        self.assertIn("no scripts/sync-canon-bundle.sh", out.stdout)

    def test_script_parses(self):
        subprocess.run(["bash", "-n", str(STEP)], check=True)


if __name__ == "__main__":
    unittest.main()
