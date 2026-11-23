#!/usr/bin/env bash
# Auto-intake step for the viridis-engine nightly job (docs/auto_intake/README.md).
#
# Runs inside the existing nightly job after the run is certified; adds no schedule (AI-8).
# It runs as three phases, each its own workflow step, so that no code a drafter wrote, and no
# code taken from a merged kernel, ever runs where the write token can be reached (AI-9):
#
#   PHASE=fetch    token, runner user. Runs only gh and git on pristine checkouts.
#     A sweep: merge open auto-intake PRs whose checks are all green; alert on red, missing or
#        stalled checks (AI-4, AI-10)
#     R release: when canon main's live-kernel files differ from the newest canon-v release, publish
#        canon-vYYYY.MM.DD; the canon's os-bundle workflow attaches the bundle + DIGEST (AI-5)
#     then records, in $AI_IN, the open auto-intake branches and the newest released bundle
#   PHASE=build    no credentials at all, run as a separate unprivileged user on copies of the
#     checkouts. Refuses to start if any token is in its environment or stored in a checkout.
#     B ViridisOS refresh from canon main, with its tests
#     S site: move the pinned bundle with the app's scripts/sync-canon-bundle.sh, offline from $AI_IN
#     C plan; draft at most one candidate ($DRAFT); verify, apply, go-live, gates (AI-1..AI-3, AI-6)
#     D print the owner's note for the kernel-flag email (AI-7)
#     Each change is written to $AI_OUT/<canon|viridisos|site>/ as a branch name, a patch and a body.
#   PHASE=publish  token, runner user. Runs only gh and git. For each change in $AI_OUT it clones
#     the target repo fresh, refuses any patch outside that change's allowed paths (AI-9), applies
#     it with hooks off, commits, pushes the branch and opens the PR. It never runs repo code.
#
# Without PHASE the step runs only A and R and raises an alert, so an engine that predates the
# phases never drafts with the token in reach.
#
# Every problem is an ALERT line in the log and, with $AI_ALERTS set, a line in that file (build
# writes $AI_OUT/alerts); the engine turns those lines into a GitHub issue (AI-10).
# STEPS (default "A R B S C D") limits which steps run; the tests use it.
set -euo pipefail
PHASE="${PHASE:-legacy}"
STEPS="${STEPS:-A R B S C D}"
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
log() { echo "auto-intake: $*"; }
alert() {
  echo "auto-intake: ALERT: $*"
  if [ -n "${AI_ALERTS:-}" ]; then printf '%s\n' "$*" | tr -d '\r' | head -c 2000 >> "$AI_ALERTS"; printf '\n' >> "$AI_ALERTS"; fi
}
: "${CANON:?}"
CANON_REPO="${CANON_REPO:-jdhart81/viridis-canon}"
OS_REPO="${OS_REPO:-jdhart81/viridisos}"
SITE_REPO="${SITE_REPO:-jdhart81/viridis-conservation-app}"
GIT_REMOTE_BASE="${GIT_REMOTE_BASE:-https://github.com}"
RESEARCH="${RESEARCH:-}"
INDEX="$RESEARCH/index/certified.json"
SINCE="${SINCE:-$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%SZ)}"
STALL_HOURS="${STALL_HOURS:-12}"
NOW_EPOCH="${NOW_EPOCH:-$(date -u +%s)}"
hours_since() { echo $(( (NOW_EPOCH - $(date -u -d "$1" +%s)) / 3600 )); }

case "$PHASE" in
  fetch|build|publish) ;;
  legacy)
    alert "the engine runs the auto-intake step without PHASE; only the sweep and the release ran (see docs/auto_intake/README.md)"
    STEPS=$(for s in $STEPS; do case "$s" in A|R) printf '%s ' "$s";; esac; done) ;;
  *) echo "auto-intake: unknown PHASE $PHASE" >&2; exit 2 ;;
esac

latest_canon_release() {  # "<tag> <publishedAt>" of the newest canon-v release, or nothing
  gh release list -R "$CANON_REPO" --exclude-drafts --exclude-pre-releases --limit 30 \
    --json tagName,publishedAt \
    -q '[.[] | select(.tagName | startswith("canon-v"))] | sort_by(.publishedAt) | last | select(. != null) | "\(.tagName) \(.publishedAt)"'
}
has_digest() { gh release view "$1" -R "$CANON_REPO" --json assets -q '.assets[].name' | grep -q '\.DIGEST$'; }
is_open() { [ -f "$AI_IN/open-heads" ] && grep -qxF "$1 $2" "$AI_IN/open-heads"; }

# ============================================================================== fetch (token)
phase_fetch() {
  local prs repo pr created states age last="" last_at="" latest=""
  prs=$(mktemp)
  # A. sweep: merge only green PRs; say loudly what is red, missing or stalled
  want A && for repo in "$CANON_REPO" "$OS_REPO" ${SITE:+"$SITE_REPO"}; do
    gh pr list -R "$repo" --state open --search "head:auto-intake/" --json number,createdAt \
        -q '.[] | "\(.number) \(.createdAt)"' > "$prs" \
      || { alert "could not list auto-intake PRs on $repo"; continue; }
    while read -r pr created; do
      [ -n "$pr" ] || continue
      states=$(gh pr checks "$pr" -R "$repo" --json state \
               -q '[.[].state | select(. != "SKIPPED" and . != "NEUTRAL")] | unique | join(",")' 2>/dev/null || echo "NONE")
      age=$(hours_since "$created")
      if [ "$states" = "SUCCESS" ]; then
        if gh pr merge "$pr" -R "$repo" --squash --delete-branch; then log "merged $repo#$pr"
        else alert "$repo#$pr is green but would not merge"; fi
      elif echo "$states" | grep -qE 'FAILURE|ERROR|CANCELLED|TIMED_OUT|ACTION_REQUIRED|STARTUP_FAILURE'; then
        alert "$repo#$pr has failing checks ($states); left open"
      elif [ -z "$states" ] || [ "$states" = "NONE" ]; then
        if [ "$age" -ge "$STALL_HOURS" ]; then alert "no checks have run (or none could be read) on $repo#$pr in ${age}h; it cannot merge until they do"
        else log "waiting on $repo#$pr: no checks yet (${age}h)"; fi
      elif [ "$age" -ge "$STALL_HOURS" ]; then
        alert "$repo#$pr has waited ${age}h on checks ($states)"
      else
        log "waiting on $repo#$pr: checks $states"
      fi
    done < "$prs"
  done
  rm -f "$prs"

  # R. release the canon bundle when the live kernel set changed since the last release
  if want R; then
    git -C "$CANON" fetch -q --tags origin main || alert "git fetch of the canon failed"
    read -r last last_at <<<"$(latest_canon_release || true)" || true
    if [ -z "$last" ]; then
      alert "no canon-v release found; the site cannot move"
    elif ! git -C "$CANON" diff --quiet "$last" origin/main -- \
         os/core.json os/admissions.json os/research_statements.json research/; then
      tag="canon-v$(date -u +%Y.%m.%d)"
      if gh release view "$tag" -R "$CANON_REPO" >/dev/null 2>&1; then
        log "release $tag already exists; the next run releases any later change"
      elif gh release create "$tag" -R "$CANON_REPO" --target main --title "$tag" \
             --notes "Canon release after a live-kernel change (auto-intake). The os-bundle workflow attaches the bundle and its DIGEST."; then
        log "published $tag"
      else
        alert "publishing canon release $tag failed"
      fi
    fi
    if [ -n "$last" ] && [ -n "$last_at" ] && ! has_digest "$last" && [ "$(hours_since "$last_at")" -ge 3 ]; then
      alert "canon release $last has no bundle DIGEST $(hours_since "$last_at")h after it was published; check the os-bundle workflow"
    fi
  fi

  # state for build: open branches, fresh refs, the newest released bundle (read-only to build)
  [ -n "${AI_IN:-}" ] || return 0
  mkdir -p "$AI_IN"
  : > "$AI_IN/open-heads"
  for repo in "$CANON_REPO" "$OS_REPO" ${SITE:+"$SITE_REPO"}; do
    gh pr list -R "$repo" --state open --search "head:auto-intake/" --json headRefName -q '.[].headRefName' \
      | sed "s|^|$repo |" >> "$AI_IN/open-heads" || alert "could not list open branches on $repo"
  done
  for d in "${VIRIDISOS:-}" "${SITE:-}"; do
    if [ -n "$d" ]; then git -C "$d" fetch -q origin main || alert "git fetch failed in $d"; fi
  done
  read -r latest _ <<<"$(latest_canon_release || true)" || true
  if [ -n "$latest" ] && has_digest "$latest"; then
    rm -rf "${AI_IN:?}/assets/$latest" && mkdir -p "$AI_IN/assets/$latest"
    if gh release download "$latest" -R "$CANON_REPO" -p "os-bundle-$latest.*" -D "$AI_IN/assets/$latest"; then
      echo "$latest" > "$AI_IN/latest-release"
    else
      alert "downloading the bundle of $latest failed"
    fi
  fi
}

# ============================================================================== build (no token)
show_failures() {  # show_failures <what> <log>: the failing part of a test log, into the step's own output
  echo "auto-intake: $1 failed; the failing part of their output:"
  { grep -vE '^test_[A-Za-z0-9_]+\.py +[0-9]+ passed, 0 failed$' "$2" || true; } | tail -n 80 | sed 's/^/  | /'
}
failing_suites() {  # names of the suites whose summary line reports failures, or "see the step log"
  local names
  names=$(grep -oE '^test_[A-Za-z0-9_]+\.py +[0-9]+ passed, [1-9][0-9]* failed$' "$1" | awk '{print $1}' | head -n 5 | paste -sd, - || true)
  echo "${names:-see the step log}"
}
emit() {  # emit <kind> <branch> <checkout> [body]: staged changes in <checkout> become $AI_OUT/<kind>/; 2 = no change
  local out="$AI_OUT/$1"
  rm -rf "$out" && mkdir -p "$out"
  printf '%s\n' "$2" > "$out/branch"
  git -C "$3" diff --cached --binary HEAD > "$out/patch"
  if [ ! -s "$out/patch" ]; then rm -rf "$out"; return 2; fi  # 2: nothing to change
  printf '%s\n' "${4:-}" > "$out/body"
}

phase_build() {
  : "${AI_IN:?}" "${AI_OUT:?}"
  mkdir -p "$AI_OUT"
  AI_ALERTS="${AI_ALERTS:-$AI_OUT/alerts}"
  local leaked d f branch latest pkg
  leaked=$(env | sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' \
           | grep -E 'TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|CREDENTIAL' | grep -vx 'CLAUDE_CODE_OAUTH_TOKEN' || true)
  if [ -n "$leaked" ]; then
    alert "build refused: credentials in its environment ($(echo $leaked))"; exit 3
  fi
  for v in GIT_ASKPASS SSH_ASKPASS SSH_AUTH_SOCK GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS; do
    if [ -n "${!v:-}" ]; then alert "build refused: $v is set"; exit 3; fi
  done
  for d in "$CANON" "${VIRIDISOS:-}" "${SITE:-}" "${RESEARCH:-}"; do
    [ -n "$d" ] && [ -e "$d" ] || continue
    # any checkout git recognises (plain clone, linked worktree, submodule), by its effective config
    git -C "$d" rev-parse --git-dir >/dev/null 2>&1 || continue
    if git -C "$d" config --get-regexp '^(http\..*extraheader|credential(\..*)?\.helper|url\..*insteadof)$' >/dev/null 2>&1 \
       || git -C "$d" config --get-regexp '^remote\..*url$' 2>/dev/null | grep -qE '://[^/]*@'; then
      alert "build refused: $d stores git credentials"; exit 3
    fi
  done
  for f in "${HOME:-/nonexistent}/.git-credentials" "${HOME:-/nonexistent}/.config/gh/hosts.yml"; do
    if [ -e "$f" ]; then alert "build refused: $f exists"; exit 3; fi
  done
  if want B || want C; then : "${VIRIDISOS:?}" "${RESEARCH:?}"; fi
  # Only the drafter gets the Claude credential; tests, sync scripts and gates never see it.
  local claude_token="${CLAUDE_CODE_OAUTH_TOKEN:-}"
  unset CLAUDE_CODE_OAUTH_TOKEN

  # B. ViridisOS follows canon main. Every decision is made on origin/main as fetch left it: the
  # sweep may have merged the previous refresh after the engine checked out, so the working tree
  # can be older than origin/main (the 2026-11-23 false alarm).
  if want B; then
    git -C "$CANON" checkout -q --detach origin/main
    if ! git -C "$VIRIDISOS" checkout -q --detach origin/main; then
      alert "ViridisOS: could not check out origin/main; nothing kept"
    elif (cd "$VIRIDISOS" && python3 tools/refresh_from_canon.py --canon "$CANON" --check >/dev/null); then
      log "ViridisOS already follows canon $(git -C "$CANON" rev-parse --short HEAD)"
    else
      branch="auto-intake/os-refresh-$(git -C "$CANON" rev-parse --short HEAD)"
      tests_log=$(mktemp)
      if is_open "$OS_REPO" "$branch"; then log "ViridisOS refresh $branch already has a PR"
      elif ! (cd "$VIRIDISOS" && git checkout -q -B "$branch" origin/main \
              && python3 tools/refresh_from_canon.py --canon "$CANON"); then
        alert "ViridisOS refresh from canon failed in tools/refresh_from_canon.py; nothing kept"
      elif ! (cd "$VIRIDISOS" && bash run_all_tests.sh > "$tests_log" 2>&1); then
        show_failures "ViridisOS tests" "$tests_log"
        alert "ViridisOS refresh from canon failed its tests ($(failing_suites "$tests_log")); nothing kept"
      else
        rc=0
        (cd "$VIRIDISOS" && git add runtime/canon_auto_kernels.json) \
          && emit viridisos "$branch" "$VIRIDISOS" "Refreshes runtime/canon_auto_kernels.json from canon $(git -C "$CANON" rev-parse HEAD); ViridisOS tests passed in the build." \
          || rc=$?
        case $rc in
          0) log "prepared ViridisOS refresh $branch" ;;
          2) log "ViridisOS refresh $branch changes nothing; ViridisOS already follows the canon" ;;
          *) alert "ViridisOS refresh $branch could not be staged; nothing kept" ;;
        esac
      fi
      rm -f "$tests_log"
    fi
  fi

  # S. the site takes the newest released bundle (decided on origin/main, as in B)
  if ! want S || [ -z "${SITE:-}" ]; then :
  elif ! git -C "$SITE" checkout -q --detach origin/main; then
    alert "site: could not check out origin/main; site stays pinned"
  elif [ ! -x "$SITE/scripts/sync-canon-bundle.sh" ]; then
    alert "the site has no scripts/sync-canon-bundle.sh; site stays pinned"
  elif ! grep -q CANON_ASSETS_DIR "$SITE/scripts/sync-canon-bundle.sh"; then
    alert "the site's sync script cannot read a downloaded release (CANON_ASSETS_DIR); site stays pinned"
  elif [ ! -s "$AI_IN/latest-release" ]; then
    log "no released canon bundle with a DIGEST yet; site stays pinned"
  else
    latest=$(head -n1 "$AI_IN/latest-release")
    export CANON_ASSETS_DIR="$AI_IN/assets/$latest"
    if (cd "$SITE" && scripts/sync-canon-bundle.sh --check "$latest" >/dev/null); then
      log "site already pins $latest"
    elif is_open "$SITE_REPO" "auto-intake/site-$latest"; then log "site update to $latest already has a PR"
    elif ! ( cd "$SITE" && git checkout -q -B "auto-intake/site-$latest" origin/main \
             && scripts/sync-canon-bundle.sh "$latest" && git add -A -- os-bundle ); then
      alert "site update to $latest failed (sync script or the app's tests; the lines above say which); site stays pinned"
    else
      rc=0
      emit site "auto-intake/site-$latest" "$SITE" "Moves the pinned canon os-bundle to $latest after its DIGEST verified; the app's tests passed in the build." || rc=$?
      case $rc in
        0) log "prepared site update to $latest" ;;
        2) log "site update to $latest changes nothing; the site already pins it" ;;
        *) alert "site update to $latest could not be staged; site stays pinned" ;;
      esac
    fi
    unset CANON_ASSETS_DIR
  fi

  # C. one candidate per night
  if want C; then
    STATEMENT=$(cd "$CANON" && python3 -m canon_core auto-intake plan --index "$INDEX" --research-root "$RESEARCH" \
      | python3 -c 'import json,sys; c=json.load(sys.stdin)["candidates"]; print(c[0] if c else "")') \
      || { alert "auto-intake plan failed"; STATEMENT=""; }
    if [ -z "$STATEMENT" ]; then log "no candidate tonight"
    elif ! [[ "$STATEMENT" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then alert "plan returned an unusable statement id"
    elif is_open "$CANON_REPO" "auto-intake/$STATEMENT"; then log "$STATEMENT already has a PR"
    else
      branch="auto-intake/$STATEMENT"
      pushd "$CANON" >/dev/null
      git checkout -q -B "$branch" origin/main
      export STATEMENT INDEX RESEARCH
      if ! CLAUDE_CODE_OAUTH_TOKEN="$claude_token" ${DRAFT:?}; then alert "draft for $STATEMENT failed; nothing kept"; git reset -q --hard && git clean -qfd; fi
      pkg=$(git status --porcelain --untracked-files=all | awk '{print $2}' | grep -oE '^research/[a-z0-9-]+/' | sort -u | head -1 || true)
      if [ -n "$pkg" ]; then
        if python3 -m canon_core auto-intake verify --index "$INDEX" --research-root "$RESEARCH" --package "$pkg" \
           && python3 -m canon_core auto-intake apply --index "$INDEX" --research-root "$RESEARCH" --package "$pkg" >/dev/null \
           && { [ "$(python3 -c 'import json;print(json.load(open("os/auto_intake.json"))["go_live"])')" != "True" ] \
                || python3 -m canon_core auto-intake go-live --function "$(basename "$pkg")" >/dev/null; } \
           && python3 -m canon_core validate-functions \
           && python3 -m canon_core build-os --out "$(mktemp -d)/os-bundle" \
           && python3 tools/build_formalization_yaml.py --check && python3 tools/build_certificates_index.py --check \
           && python3 -m unittest discover -s tests -q \
           && git add -A \
           && emit canon "$branch" "$CANON" "$(python3 -m canon_core auto-intake note --since "$SINCE")"; then
          log "prepared $STATEMENT as $(basename "$pkg")"
        else
          alert "$STATEMENT did not pass the gates; nothing kept"
        fi
      elif ! git diff --quiet -- os/research_statements.json; then
        git add os/research_statements.json \
          && emit canon "$branch" "$CANON" "$(python3 -m canon_core auto-intake note --since "$SINCE")" \
          && log "prepared the decline of $STATEMENT"
      fi
      git reset -q --hard && git clean -qfd && git checkout -q --detach origin/main
      popd >/dev/null
    fi
  fi

  # D. owner note
  if want D; then (cd "$CANON" && git checkout -q --detach origin/main && python3 -m canon_core auto-intake note --since "$SINCE"); fi
}

# ============================================================================== publish (token)
# Paths each change may touch. Anything else, a symlink, a submodule, a rename or (outside the
# site bundle) a deletion refuses the whole change. File contents are left to each repo's CI.
CANON_FIXED='os/research_statements.json os/families.json os/research_intake.json os/core.json os/admissions.json formalization.yaml README.md docs/overview/index.html'

check_patch() {  # check_patch <kind> <clone> <patch>; prints "ok <fid>" or the reason
  local kind="$1" repo_dir="$2" patch="$3" summary paths p fid="" ids
  summary=$(git -C "$repo_dir" apply --summary < "$patch") || { echo "not a patch"; return; }
  if grep -qE '^ (rename|copy|mode change) ' <<<"$summary"; then echo "renames or mode changes"; return; fi
  if grep -qE 'mode 1[26]0000 ' <<<"$summary"; then echo "a symlink or submodule"; return; fi
  paths=$(git -C "$repo_dir" apply --numstat < "$patch" | cut -f3-) || { echo "unreadable patch"; return; }
  [ -n "$paths" ] || { echo "empty patch"; return; }
  while IFS= read -r p; do
    case "$p" in
      \"*|/*|*..*|*/.git/*|.git/*|*' '*) echo "unsafe path $p"; return ;;
    esac
  done <<<"$paths"
  if [ "$kind" != site ] && grep -qE '^ delete mode ' <<<"$summary"; then echo "deletions"; return; fi
  case "$kind" in
    viridisos)
      [ "$paths" = "runtime/canon_auto_kernels.json" ] || { echo "touches more than runtime/canon_auto_kernels.json"; return; } ;;
    site)
      while IFS= read -r p; do
        case "$p" in os-bundle/*) ;; *) echo "touches $p outside os-bundle/"; return ;; esac
      done <<<"$paths" ;;
    canon)
      ids=$(sed -n 's|^research/\([^/]*\)/.*|\1|p' <<<"$paths" | sort -u)
      [ "$(grep -c . <<<"$ids")" -le 1 ] || { echo "more than one package"; return; }
      fid="$ids"
      if [ -n "$fid" ] && ! [[ "$fid" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then echo "bad package id"; return; fi
      while IFS= read -r p; do
        case " $CANON_FIXED " in *" $p "*) continue ;; esac
        if [ -n "$fid" ] && { [[ "$p" == research/"$fid"/* ]] || [ "$p" = "tests/test_os_auto_${fid//-/_}.py" ]; }; then continue; fi
        echo "touches $p"; return
      done <<<"$paths"
      if [ -z "$fid" ] && [ "$paths" != "os/research_statements.json" ]; then echo "a decline may change only the ledger"; return; fi ;;
    *) echo "unknown kind"; return ;;
  esac
  echo "ok $fid"
}

publish_one() {
  local kind="$1" dir="$AI_OUT/$1" repo="" branch tag="" title msg verdict fid work
  if [ ! -f "$dir/branch" ] || [ ! -f "$dir/patch" ]; then alert "$kind change is incomplete; skipped"; return; fi
  branch=$(head -n1 "$dir/branch" | head -c 200)
  case "$kind" in
    canon)     repo="$CANON_REPO"; [[ "$branch" =~ ^auto-intake/[A-Za-z0-9][A-Za-z0-9._-]*$ ]] ;;
    viridisos) repo="$OS_REPO";    [[ "$branch" =~ ^auto-intake/os-refresh-[0-9a-f]{7,40}$ ]] ;;
    site)      repo="$SITE_REPO";  [[ "$branch" =~ ^auto-intake/site-(canon-v[0-9]{4}\.[0-9]{2}\.[0-9]{2})$ ]] && tag="${BASH_REMATCH[1]}" ;;
  esac || { alert "$kind change has an unusable branch name; skipped"; return; }
  if [ "$(wc -c < "$dir/patch")" -gt 52428800 ]; then alert "$kind patch is over 50 MB; skipped"; return; fi
  if gh pr list -R "$repo" --state open --search "head:$branch" --json number -q '.[0].number' | grep -q .; then
    log "$repo already has a PR for $branch"; return
  fi
  if [ -n "$tag" ] && ! has_digest "$tag"; then alert "site change names $tag, which has no released DIGEST; skipped"; return; fi
  work=$(mktemp -d)
  if ! git -c core.hooksPath=/dev/null -c credential.helper= -c 'credential.helper=!gh auth git-credential' \
         clone -q --no-tags --single-branch --branch main "$GIT_REMOTE_BASE/$repo.git" "$work/repo"; then
    alert "could not clone $repo to publish $branch"; rm -rf "$work"; return
  fi
  verdict=$(check_patch "$kind" "$work/repo" "$dir/patch")
  if [ "${verdict%% *}" != ok ]; then alert "refused the $kind change $branch: $verdict"; rm -rf "$work"; return; fi
  fid="${verdict#ok}"; fid="${fid# }"
  case "$kind" in
    canon) if [ -n "$fid" ]; then title="Auto-intake: ${branch#auto-intake/} → $fid"; msg="auto-intake: ${branch#auto-intake/} enters as $fid"
           else title="Auto-intake: ${branch#auto-intake/} not entered"; msg="auto-intake: record ${branch#auto-intake/} as not entered"; fi ;;
    viridisos) title="Auto-intake: refresh kernels from canon"; msg="runtime: refresh auto-intake kernels from canon" ;;
    site) title="Auto-intake: take canon bundle $tag"; msg="canon: take bundle $tag" ;;
  esac
  { head -c 20000 "$dir/body" 2>/dev/null | tr -d '\000' || true
    printf '\n\nGenerated by viridis-canon tools/auto_intake/engine_step.sh (publish phase, from a build that ran without credentials). Merges automatically when its checks pass (owner decision 2026-11-17).\n'
    if [ "$kind" = site ]; then printf 'Roll back: scripts/sync-canon-bundle.sh <previous canon-v tag>.\n'; fi
  } > "$work/body"
  if ( cd "$work/repo" \
       && git -c core.hooksPath=/dev/null checkout -q -b "$branch" \
       && git -c core.hooksPath=/dev/null apply --index --whitespace=nowarn "$dir/patch" \
       && git -c core.hooksPath=/dev/null -c commit.gpgsign=false commit -s -q -m "$msg" \
       && git -c core.hooksPath=/dev/null -c credential.helper= -c 'credential.helper=!gh auth git-credential' \
            push -q -u origin "$branch" ) \
     && gh pr create -R "$repo" --head "$branch" --base main --title "$title" --body-file "$work/body" >/dev/null; then
    log "opened $repo PR for $branch"
  else
    alert "publishing $branch to $repo failed"
  fi
  rm -rf "$work"
}

phase_publish() {
  : "${AI_OUT:?}"
  [ -d "$AI_OUT" ] || { log "nothing to publish"; return 0; }
  if [ -n "$(find "$AI_OUT" -type l -print -quit)" ]; then alert "the build output holds a symlink; nothing published"; return 0; fi
  for kind in canon viridisos site; do
    if [ -d "$AI_OUT/$kind" ]; then publish_one "$kind"; fi
  done
  return 0
}

case "$PHASE" in
  fetch|legacy) phase_fetch ;;
  build) phase_build ;;
  publish) phase_publish ;;
esac
