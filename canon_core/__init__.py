"""Open research-canon primitives for Viridis.

The package is intentionally standard-library only.  It turns a repository of
research artifacts into a deterministic, machine-readable catalog without
claiming that formal verification is empirical validation.
"""

from .canonical import canonical_bytes, canonical_digest
from .catalog import build_catalog, validate_catalog, write_catalog
from .model import ResearchRecord

__all__ = [
    "ResearchRecord",
    "build_catalog",
    "canonical_bytes",
    "canonical_digest",
    "validate_catalog",
    "write_catalog",
]

__version__ = "0.1.0"
