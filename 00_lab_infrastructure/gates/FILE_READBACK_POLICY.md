# Filename-keyed publication readback

Authority: GAME_PLAN.md, “File-order mismatch resolution — 2026-10-04”.

`require_file_preservation` compares the complete returned public file list by its exact `key` filename when both lists contain unique filenames. Filename sets and every complete per-file JSON object must match. It ignores only the outer array order. JSON scalar types, nested arrays, unknown fields, checksum, size, ID, mimetype and URLs remain exact. Missing or malformed input fails closed. If either list contains duplicate filenames, the complete ordered lists must match instead.

Sandbox fixture https://sandbox.zenodo.org/records/613098 contains six distinct files. An authenticated legacy edit → PUT → publish round trip used the unchanged transport SHA-256 `c331229849f5533476df7f8a7b290a55fa7d3b9fc32dfa43b68d976dd8eaa9cc`. Public metadata preservation and all six downloaded sizes/MD5s passed. The server naturally reordered the returned file array; all complete entries remained equal. The regression fixture also injects a forced reversal of that real public response, which passes, and one checksum corruption, which must HOLD.

The documented legacy sort operation returned definitive HTTP405; native metadata PUT ignored `files.order`. Neither is represented as a successful forced server sort. Forced reorder injection is applied only to copied comparator input. Production native file-object preservation remains exact; no additional native-order exception exists.

Evidence lives under `reports/verification-coverage/2026-10-04/game-plan-completion/sandbox-multi-file-v001`, `v002` and `v003` in the canonical Cowork tree. The repository fixture contains complete public file entries, never credentials or private diagnostics. Tests include strict duplicate-filename fallback and all-field/type-change failures.
