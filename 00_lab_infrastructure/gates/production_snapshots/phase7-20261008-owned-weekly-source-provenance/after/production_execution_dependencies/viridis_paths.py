"""Canonical filesystem paths for the Viridis research control plane."""

from pathlib import Path


CONTROL_ROOT = Path("/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0").resolve()
FORGE_STATE = CONTROL_ROOT / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json"

if not FORGE_STATE.is_file():
    raise RuntimeError(
        "canonical Viridis control root is invalid: "
        f"missing required forge state at {FORGE_STATE}"
    )
