#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    text = CPP.read_text(encoding="utf-8")
    required = [
        "V11 reversible cumulative contract",
        "candidatePrior[s] += std::max(pcAciDesignPriorGrid[cell], 0.0L);",
        "meAciEvidenceReservoir = pcAciActiveEvents;",
    ]
    forbidden = [
        "meAciEvidenceReservoir.clear();",
        "const auto& causalPrior = pcAciLastAcceptedUpdateId > 0",
    ]
    for item in required:
        assert item in text, f"missing required V11 source marker: {item}"
    for item in forbidden:
        assert item not in text, f"forbidden V10 lock-in pattern remains: {item}"
    print("MEACI_V11_SOURCE_CONTRACT=PASS")
    print(f"Simulations.cpp_sha256={digest(CPP)}")


if __name__ == "__main__":
    main()
