"""Graph integrity services — neurologically-inspired self-correcting processes.

Five processes for internal graph consistency:
  1. Homeostasis — multiplicative weight renormalization
  2. Pattern Separation — near-duplicate neuron detection
  3. Pattern Completion — missing semantic connections
  4. Conflict Monitor — contradiction detection (LLM-assisted)
  5. Aging Review — stale content surfacing
"""

from dataclasses import dataclass, field


@dataclass
class IntegrityFindingData:
    """Data for a single integrity finding before DB persistence."""

    finding_type: str
    severity: str  # info | warning | critical
    priority_score: float
    description: str
    detail_json: str  # JSON string
    neuron_ids: list[int] = field(default_factory=list)
    edge_ids: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class IntegrityScanResult:
    """Result of an integrity scan before DB persistence."""

    scan_type: str
    scope: str
    findings: list[IntegrityFindingData] = field(default_factory=list)
    extra: dict = field(default_factory=dict)  # scan-type-specific summary data
