#!/usr/bin/env python3
"""Apply the ME-ACI V11 reversible cumulative-evidence patch.

This patch is intentionally minimal and truth-blind. It changes only the
sequential bookkeeping around the already-frozen V10 conditional inverse-
transport likelihood:

1. after an identifiable update, retain the complete evidence history instead
   of clearing it;
2. because the complete history is rescored on every later update, always
   recompute the posterior from the fixed geometry-only design prior instead
   of multiplying the same historical evidence into the previous posterior.

No likelihood family, nuisance member, spatial/temporal identifiability rule,
planner parameter, temperature, or House-specific threshold is changed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"

OLD_PRIOR = """                    const auto& causalPrior = pcAciLastAcceptedUpdateId > 0
                        ? pcAciCausalPosteriorGrid : pcAciDesignPriorGrid;
                    candidatePrior[s] += std::max(causalPrior[cell], 0.0L);"""

NEW_PRIOR = """                    // V11 reversible cumulative contract: pcAciActiveEvents contains the
                    // complete evidence history retained since acquisition began.  The
                    // conditional inverse-transport likelihood below is therefore a
                    // cumulative likelihood, not a new-window likelihood.  Reusing the
                    // previous causal posterior here would count every previously retained
                    // event twice and make an early wrong basin effectively irreversible.
                    // Recompute q_t(s) from the same geometry-only design prior and the
                    // complete conditional likelihood at every identifiable update.
                    candidatePrior[s] += std::max(pcAciDesignPriorGrid[cell], 0.0L);"""

OLD_CLEAR = """        pcAciAcceptedThisUpdate = inject;
        meAciEvidenceReservoir.clear();"""

NEW_CLEAR = """        pcAciAcceptedThisUpdate = inject;
        // V11 reversible cumulative contract: keep the accepted evidence history.
        // beginTADMUpdate() prepends this reservoir to the next completed block,
        // so later observations -- including an all-miss block -- are rescored
        // jointly with the identifying anchor.  This allows future evidence to
        // falsify an earlier basin without introducing a new gate or amplitude
        // parameter.  The next posterior is recomputed from the fixed design
        // prior above, so retained observations are not double counted.
        meAciEvidenceReservoir = pcAciActiveEvents;"""

MARKER = "V11 reversible cumulative contract"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    text = CPP.read_text(encoding="utf-8")
    before = sha256(CPP)
    if text.count(MARKER) >= 2:
        print(f"ALREADY_PATCHED {CPP}")
        print(f"sha256={before}")
        return

    if text.count(OLD_PRIOR) != 1:
        raise SystemExit(f"prior anchor count != 1: {text.count(OLD_PRIOR)}")
    if text.count(OLD_CLEAR) != 1:
        raise SystemExit(f"reservoir anchor count != 1: {text.count(OLD_CLEAR)}")

    text = text.replace(OLD_PRIOR, NEW_PRIOR, 1)
    text = text.replace(OLD_CLEAR, NEW_CLEAR, 1)
    CPP.write_text(text, encoding="utf-8")
    after = sha256(CPP)

    verify = CPP.read_text(encoding="utf-8")
    assert "meAciEvidenceReservoir.clear();" not in verify
    assert "candidatePrior[s] += std::max(pcAciDesignPriorGrid[cell], 0.0L);" in verify
    assert verify.count(MARKER) >= 2

    print("MEACI_V11_PATCH=PASS")
    print(f"source={CPP}")
    print(f"before_sha256={before}")
    print(f"after_sha256={after}")


if __name__ == "__main__":
    main()
