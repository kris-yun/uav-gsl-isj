# Step 1 — Decompose the novelty

Timestamp: 2026-08-30

- **Problem framing:** Sequential single-UAV gas-source localization under
  uncertain obstacle-driven transport, persistent sensor memory and sparse
  completed-stop observations; comparison is authoritative PMFS in a complete
  300 s closed loop.
- **Core mechanism:** A joint posterior over source carrier and one native
  whole-run nuisance atom; the same stochastic transport realization remains
  associated with every completed stop and source update, and source evidence
  replaces the PMFS source channel once.
- **Key insight:** Per-stop transport marginalization can combine mutually
  incompatible plume explanations. Marginalizing only after accumulating
  evidence under a persistent physical realization preserves cross-stop
  dependence.
- **Application domain:** Mobile robotic gas-source localization with native
  GADEN response fields, persistent gas sensor and PMFS planning.

Scientific modules: M1 native interventional response support, M2 persistent
coherent source–transport filter as the main claim, and M3 sensor-aware
reachability/detection support. Neural response approximation is excluded from
the scientific novelty.
