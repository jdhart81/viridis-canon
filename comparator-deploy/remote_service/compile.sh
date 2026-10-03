#!/usr/bin/env bash

set -euo pipefail # realpath or dirname failure should abort

PROJECT_DIR="$(realpath "$1")" # Read-only project source
shift
WORK_DIR="$(realpath "$1")"    # Task-specific temporary directory
shift
MODULE_NAME="$1"               # The argument to `lake exe module-constants`
shift

GIT_PATH=$(dirname $(realpath $(which git)))
DIRNAME_PATH=$(dirname $(realpath $(which dirname)))



cd $PROJECT_DIR
LEAN_ROOT="$(lean --print-prefix)"

# Record the exact paths selected for this job before entering its sandbox.
# The observer only reads/hashes files; a missing observation stops the job.
ATTESTATION_HELPER="$(dirname "$(realpath "$0")")/../src/job-attestation.mjs"
node "$ATTESTATION_HELPER" "compile-$MODULE_NAME" "$PROJECT_DIR" "$WORK_DIR" "$LEAN_ROOT" "$(realpath "$0")"


SH=$(realpath $(which sh))
SCRIPT=$(cat <<EOF
ulimit -t 300      # bounded allowance for full Mathlib-backed Viridis modules
# systemd already enforces LimitNPROC=65536. Under NoNewPrivileges the shell
# may be forbidden from reasserting that value, which must not abort a build.
ulimit -u 65536 2>/dev/null || true
ulimit -f 524288   # File output size limits
exec /lean/bin/lake build "$MODULE_NAME"
EOF
)

# Abort if the .lake/build directory is not in place
if [[ ! -d "$PROJECT_DIR/.lake/build" ]]; then
     echo "error: $PROJECT_DIR/.lake/build does not exist" >&2
     echo "(server deployment needs to ensure this directory is in place)" >&2
     exit 1
fi




mkdir -p "$WORK_DIR/$MODULE_NAME/.lake/build"
mkdir -p "$WORK_DIR/$MODULE_NAME-staging"
while IFS= read -r -d '' BUILD_DIR; do
     mkdir -p "$WORK_DIR/$MODULE_NAME/.lake/build/$BUILD_DIR"
done < <(cd "$PROJECT_DIR/.lake/build" && find . -type d -print0)
chmod -R 0777 "$WORK_DIR/$MODULE_NAME/.lake/build" "$WORK_DIR/$MODULE_NAME-staging"

exec bwrap \
     --ro-bind /nix /nix \
     --ro-bind "$LEAN_ROOT" /lean \
     \
     --dev /dev \
     --tmpfs /tmp \
     --proc /proc \
     \
     --clearenv \
     --setenv HOME "/tmp" \
     --setenv LEAN_NUM_THREADS "4" \
     --setenv PATH "$GIT_PATH:$DIRNAME_PATH" \
     \
     \
     --ro-bind "$PROJECT_DIR" /project \
     --ro-bind "$WORK_DIR/$MODULE_NAME/$MODULE_NAME.lean" "/project/$MODULE_NAME.lean" \
     \
     \
     --overlay-src "$PROJECT_DIR/.lake/build" \
     \
     \
     --overlay "$WORK_DIR/$MODULE_NAME/.lake/build" "$WORK_DIR/$MODULE_NAME-staging" /project/.lake/build \
     \
     --unshare-all \
     --new-session \
     --die-with-parent \
     --hostname sandbox \
     --uid 65534 \
     --gid 65534 \
     --cap-drop ALL \
     --chdir /project \
     \
     "$SH" -c "$SCRIPT"
