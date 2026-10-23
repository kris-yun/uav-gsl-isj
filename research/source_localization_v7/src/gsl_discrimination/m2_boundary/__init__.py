"""M2: causal relative return directions and source-discriminative pairs."""

from .formation import (
    FormationDiagnostics,
    FormationGeometry,
    PairedAction,
    rank_by_maxmin,
    score_paired_formations,
)
from .memory import (
    BoundaryEvent,
    BoundaryMemoryConfig,
    CausalBoundaryMemory,
    LocalWind,
    MemorySnapshot,
    MemoryUpdate,
    ReturnTube,
)

__all__ = [
    "BoundaryEvent", "BoundaryMemoryConfig", "CausalBoundaryMemory",
    "LocalWind", "MemorySnapshot", "MemoryUpdate", "ReturnTube",
    "FormationDiagnostics", "FormationGeometry", "PairedAction",
    "rank_by_maxmin", "score_paired_formations",
]
