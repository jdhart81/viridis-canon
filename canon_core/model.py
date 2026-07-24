"""Data model for one research artifact in the Viridis canon catalog."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .canonical import canonical_digest


VALID_STATUSES = frozenset({"verified", "working", "quarantined"})
VALID_TIERS = frozenset({"spine", "flagship", "working-corpus"})
VALID_VISIBILITIES = frozenset({"public", "private"})


@dataclass(frozen=True)
class ResearchRecord:
    """A deterministic catalog record.

    ``status`` describes pipeline state.  It deliberately does not collapse
    formal verification into empirical validation; that distinction is carried
    separately by ``external_validation`` and ``caveat``.
    """

    record_id: str
    title: str
    summary: str
    path: str
    status: str
    tier: str
    visibility: str
    source_sha256: str
    abstract: str = ""
    source_url: str = ""
    paper_url: str = ""
    theorem_count: int = 0
    lemma_count: int = 0
    definition_count: int = 0
    line_count: int = 0
    imports: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    doi: str = ""
    lean_module: str = ""
    integrity: str = "not-canon-admitted"
    external_validation: str = "not-recorded"
    caveat: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError("record_id is required")
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.path.strip():
            raise ValueError("path is required")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"unsupported status: {self.status}")
        if self.tier not in VALID_TIERS:
            raise ValueError(f"unsupported tier: {self.tier}")
        if self.visibility not in VALID_VISIBILITIES:
            raise ValueError(f"unsupported visibility: {self.visibility}")
        for value in (
            self.theorem_count,
            self.lemma_count,
            self.definition_count,
            self.line_count,
        ):
            if value < 0:
                raise ValueError("artifact counts cannot be negative")

    def payload(self) -> dict[str, Any]:
        """Return the signed/digested portion of the record."""

        return {
            "record_id": self.record_id,
            "title": self.title,
            "summary": self.summary,
            "path": self.path,
            "status": self.status,
            "tier": self.tier,
            "visibility": self.visibility,
            "source_sha256": self.source_sha256,
            "abstract": self.abstract,
            "source_url": self.source_url,
            "paper_url": self.paper_url,
            "theorem_count": self.theorem_count,
            "lemma_count": self.lemma_count,
            "definition_count": self.definition_count,
            "line_count": self.line_count,
            "imports": list(self.imports),
            "tags": list(self.tags),
            "doi": self.doi,
            "lean_module": self.lean_module,
            "integrity": self.integrity,
            "external_validation": self.external_validation,
            "caveat": self.caveat,
            "metadata": self.metadata,
        }

    @property
    def digest(self) -> str:
        return canonical_digest(self.payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "digest": self.digest}
